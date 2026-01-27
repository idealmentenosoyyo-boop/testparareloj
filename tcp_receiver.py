import socket
import datetime
import threading
import json
import os
import time
from typing import Optional, Dict

import firebase_admin
from firebase_admin import credentials, firestore

# Configuration
HOST = '0.0.0.0'
PORT = 5001

# Global Firestore client
db = None

# Global tracking
active_connections = {}
active_connections_lock = threading.Lock()

connected_devices = {}
connected_devices_lock = threading.Lock()

# Global mapping: DeviceID -> Manufacturer/Metadata
device_metadata = {}
device_metadata_lock = threading.Lock()

def log_info(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [INFO] {msg}")

def log_error(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [ERROR] {msg}")

def initialize_firebase():
    """Inicializa Firebase con variable de entorno"""
    global db
    if db: return

    try:
        firebase_sa_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        
        if firebase_sa_json:
            log_info("Initialize Firebase from env...")
            try:
                sa_dict = json.loads(firebase_sa_json)
                cred = credentials.Certificate(sa_dict)
            except json.JSONDecodeError:
                cred = credentials.Certificate(firebase_sa_json) # Path string
            
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            log_info("Firestore connection successful")
        else:
            log_error("CRITICAL: FIREBASE_SERVICE_ACCOUNT not found. DB disabled.")

    except Exception as e:
        log_error(f"Error initializing Firebase: {e}")

def _update_device_metadata(device_id: str, manufacturer: str):
    with device_metadata_lock:
        device_metadata[device_id] = {'manufacturer': manufacturer}

def register_device_connection(device_id: str, conn):
    """Registra la conexión activa, envía flush de comandos y actualiza last_seen/online"""
    log_info(f"🔌 Registering device {device_id}...")
    with connected_devices_lock:
        connected_devices[device_id] = conn
    
    # Check for pending commands immediately (Flush on Connect)
    if db:
        try:
            pending_ref = db.collection('devices').document(device_id).collection('pending_commands')
            # Requires the user to have created the index as requested previously
            docs = pending_ref.where('status', '==', 'PENDING').stream()
            
            count = 0
            for doc in docs:
                data = doc.to_dict()
                raw_cmd = data.get('command_raw') or data.get('payload')
                
                log_info(f"📬 Flush: Sending pending command to {device_id}: {raw_cmd}")
                
                try:
                    # ENMARCAR COMANDO (Wrapping) para flush
                    payload = _build_command_frame(device_id, raw_cmd)
                    
                    if hasattr(payload, 'encode'):
                         conn.sendall(payload.encode('ascii'))
                    else:
                         conn.sendall(payload)
                         
                    # Mark as SENT
                    doc.reference.update({
                        'status': 'SENT',
                        'sent_at': firestore.SERVER_TIMESTAMP,
                        'flushed_on_connect': True,
                        'payload_sent': payload
                    })
                    count += 1
                except Exception as e:
                    log_error(f"Failed to flush command: {e}")
            
            if count > 0:
                log_info(f"✅ Flushed {count} pending commands to {device_id}")


            # --- AUTO-CONFIGURATION CHECK ---
            # Check if Fall Detection is configured
            device_doc = db.collection('devices').document(device_id).get()
            device_data = device_doc.to_dict() if device_doc.exists else {}
            
            if not device_data.get('fall_detection_configured', False):
                log_info(f"⚙️ Auto-Configuring Fall Detection for {device_id}...")
                
                # Command 1: Enable Fall (FALLDOWN,1,1 -> On, Call Center)
                cmd_fall = _build_command_frame(device_id, "FALLDOWN,1,1")
                # Command 2: Sensitivity (LSSET,5+8 -> Level 5 of 8? Or just default logic)
                # Note: instr.md says X+6 or X+8. Let's send a safe default or just enable first.
                # Let's stick to just enabling for now to minimize risk suitable for all FW.
                # If user wants sensitivity, we can add later.
                
                try:
                    conn.sendall(cmd_fall.encode('ascii') if hasattr(cmd_fall, 'encode') else cmd_fall)
                    log_info(f"   👉 Sent FALLDOWN config to {device_id}")
                    
                    # Update flag to prevent loop (will be re-checked next connection)
                    # We assume it takes effect. 
                    db.collection('devices').document(device_id).update({
                        'fall_detection_configured': True,
                        'fall_detection_configured_at': firestore.SERVER_TIMESTAMP
                    })
                except Exception as e:
                    log_error(f"   ❌ Failed to send auto-config: {e}")
            # -------------------------------

        except Exception as e:
            log_error(f"Error flushing/configuring for {device_id}: {e}")

def _get_or_create_device(device_id: str, updates: Dict = None):
    """Obtiene ref al dispositivo y actualiza 'last_seen'"""
    if not db or not device_id: return None
    
    device_ref = db.collection('devices').document(device_id)
    base_updates = {
        'last_seen': firestore.SERVER_TIMESTAMP,
        'updated_at': datetime.datetime.now().isoformat()
    }
    if updates:
        base_updates.update(updates)
        # Debug log for HOT location updates
        if 'last_lat' in updates:
            log_info(f"📍 HOT Location Update | Dev: {device_id} | Lat: {updates.get('last_lat')} | Lng: {updates.get('last_lng')}")
        
    try:
        device_ref.set(base_updates, merge=True)
        return device_ref
    except Exception as e:
        log_error(f"Error updating device {device_id}: {e}")
        return None

def _save_to_daily_log(device_id: str, data: Dict, event_type: str):
    """Helper para guardar eventos en bucket diario"""
    global db
    if not db: return

    try:
        now = datetime.datetime.now()
        day_str = now.strftime('%Y-%m-%d')
        # 2. Daily Log (Use add() for Auto-ID to prevent collisions)
        events_ref = db.collection('devices').document(device_id)\
                      .collection('days').document(day_str)\
                      .collection('events')
        
        final_data = data.copy()
        final_data['event_type'] = event_type
        
        # Returns (update_time, document_ref)
        _, new_doc_ref = events_ref.add(final_data)
        log_info(f"Saved {event_type} | Dev: {device_id} | Day: {day_str} | ID: {new_doc_ref.id}")
            
    except Exception as e:
        log_error(f"Error saving to daily log: {e}")

def save_location(data: Dict):
    device_id = data.get('device_id', 'unknown')
    
    # Determine event type (Position vs Alarm vs Fall)
    event_type = data.get('type', 'POSITION')
    if data.get('alarm_type'):
         event_type = data.get('alarm_type')
         
    doc_data = {
        'timestamp': firestore.SERVER_TIMESTAMP,
        'device_timestamp': f"{data.get('date')} {data.get('time')}",
        'lat': data.get('lat'),
        'lng': data.get('lng'),
        'speed': data.get('speed'),
        'course': data.get('direction'),
        'sat': data.get('satellites'),
        'bat': data.get('battery'),
        'valid': data.get('gps_valid', False),
        'type': event_type
    }
    
    # Add alarm details if present
    if data.get('alarm_type'):
        doc_data['alarm_type'] = data.get('alarm_type')
        
    device_updates = {
        'last_lat': data.get('lat'),
        'last_lng': data.get('lng'),
        'last_battery': data.get('battery'),
        'last_gps_timestamp': firestore.SERVER_TIMESTAMP,
        'online': True
    }
    
    # HOT UPDATE: Save alarm status directly to device document
    if data.get('alarm_type'):
        device_updates['last_alarm'] = data.get('alarm_type')
        device_updates['last_alarm_timestamp'] = firestore.SERVER_TIMESTAMP
    _get_or_create_device(device_id, device_updates)
    _save_to_daily_log(device_id, doc_data, event_type)

def save_heartbeat(data: Dict):
    device_id = data.get('device_id', 'unknown')
    doc_data = {
        'timestamp': firestore.SERVER_TIMESTAMP,
        'bat': int(data.get('battery', 0)),
        'steps': int(data.get('steps', 0)),
        'tumbles': int(data.get('tumbles', 0)),
        'type': 'HEARTBEAT'
    }
    device_updates = {
        'last_battery': doc_data['bat'],
        'steps_today': doc_data['steps'],
        'online': True
    }
    _get_or_create_device(device_id, device_updates)
    _save_to_daily_log(device_id, doc_data, 'HEARTBEAT')

def save_health_data(data: Dict):
    device_id = data.get('device_id', 'unknown')
    doc_data = {
        'timestamp': firestore.SERVER_TIMESTAMP,
        'hr': data.get('heart_rate'),
        'bp_sys': data.get('bp_systolic'),
        'bp_dia': data.get('bp_diastolic'),
        'spo2': data.get('spo2'),
        'source': data.get('measurement_type', 'Auto')
    }
    device_updates = {
        'online': True,
        'last_health_timestamp': firestore.SERVER_TIMESTAMP
    }
    if doc_data.get('hr'): device_updates['last_hr'] = doc_data['hr']
    if doc_data.get('spo2'): device_updates['last_spo2'] = doc_data['spo2']
    if doc_data.get('bp_sys'): 
        device_updates['last_bp'] = f"{doc_data['bp_sys']}/{doc_data['bp_dia']}"
        device_updates['last_bp_sys'] = doc_data['bp_sys']
        device_updates['last_bp_dia'] = doc_data['bp_dia']
    
    # APPLY HOT UPDATES
    _get_or_create_device(device_id, device_updates)
    
    _save_to_daily_log(device_id, doc_data, 'HEALTH')

def _build_command_frame(device_id: str, content: str) -> str:
    """Construye el comando en formato [MFG*DEVICEID*LEN*COMMAND] usando el fabricante correcto"""
    content = str(content).strip()
    # Si ya empieza con [, asumimos que está listo
    if content.startswith('[') and content.endswith(']'):
        return content
        
    length = len(content)
    length_hex = f"{length:04X}"
    
    # Recuperar fabricante detectado del dispositivo (Dynamic)
    manufacturer = "3G" # Default
    with device_metadata_lock:
        if device_id in device_metadata:
            manufacturer = device_metadata[device_id].get('manufacturer', '3G')
    
    return f"[{manufacturer}*{device_id}*{length_hex}*{content}]"

def listen_to_firestore_commands():
    """Escucha comandos pendientes en Firestore (Real-time)"""
    global db
    if not db:
        log_error("Firestore not initialized, cannot listen for commands")
        return

    def on_snapshot(col_snapshot, changes, read_time):
        for change in changes:
            if change.type.name == 'ADDED':
                doc = change.document
                data = doc.to_dict()
                
                if data.get('status') == 'PENDING':
                    device_ref = doc.reference.parent.parent
                    if not device_ref: continue
                    
                    device_id = device_ref.id
                    raw_cmd = data.get('command_raw') or data.get('payload')
                    
                    # ENMARCAR COMANDO (Wrapping)
                    payload = _build_command_frame(device_id, raw_cmd)
                    
                    log_info(f"🔔 Command received for {device_id}: {raw_cmd} -> {payload}")
                    
                    conn = None
                    with connected_devices_lock:
                        conn = connected_devices.get(device_id)
                    
                    if conn:
                        try:
                            if hasattr(payload, 'encode'):
                                conn.sendall(payload.encode('ascii'))
                            else:
                                conn.sendall(payload)
                                
                            log_info(f"   🚀 Command SENT to {device_id}")
                            
                            doc.reference.update({
                                'status': 'SENT',
                                'sent_at': firestore.SERVER_TIMESTAMP,
                                'payload_sent': payload
                            })
                        except Exception as e:
                            log_error(f"   ❌ Failed to send command: {e}")
                            doc.reference.update({'status': 'FAILED', 'error': str(e)})
                    else:
                        log_info(f"   ⚠️ Device {device_id} not connected. Waiting...")

    log_info("👀 Starting Firestore Command Listener...")
    # Escuchar en todos los 'pending_commands' de la BD
    query = db.collection_group('pending_commands').where('status', '==', 'PENDING')
    query_watch = query.on_snapshot(on_snapshot)
    
    while True:
        time.sleep(60)

class ProtocolDecoder:
    """Decodificador oficial del protocolo Setracker/Beesure"""
    
    @staticmethod
    def _log(msg: str, level: str = 'INFO'):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {msg}")

    @staticmethod
    def parse_packet(packet_hex: str) -> Optional[Dict]:
        try:
            packet_bytes = bytes.fromhex(packet_hex)
            try:
                packet_ascii = packet_bytes.decode('ascii', errors='strict')
                if '[' in packet_ascii and '*' in packet_ascii:
                    return ProtocolDecoder._parse_text_protocol(packet_ascii)
            except UnicodeDecodeError:
                pass
            return ProtocolDecoder._parse_binary_protocol(packet_hex, packet_bytes)
        except Exception as e:
            ProtocolDecoder._log(f"Error parsing packet: {e}", 'ERROR')
            return None
    
    @staticmethod
    def _parse_text_protocol(packet_ascii: str) -> Optional[Dict]:
        try:
            content = packet_ascii.strip('[]')
            parts = content.split('*')
            
            if len(parts) < 4: return None
            
            manufacturer = parts[0]
            device_id = parts[1]
            length = parts[2]
            command_content = parts[3]
            
            cmd_parts = command_content.split(',')
            command = cmd_parts[0]
            
            result = {
                'protocol': 'TEXT',
                'manufacturer': manufacturer,
                'device_id': device_id,
                'length': length,
                'command': command,
                'raw': packet_ascii,
                'date': datetime.datetime.now().strftime('%d%m%y'),
                'time': datetime.datetime.now().strftime('%H%M%S')
            }
            
            if command in ['UD', 'UD2', 'UD_LTE']:
                return ProtocolDecoder._parse_location_data(parts, result)
            elif command == 'LK':
                return ProtocolDecoder._parse_heartbeat(cmd_parts, result)
            elif command == 'AL' or command == 'AL_LTE':
                res = ProtocolDecoder._parse_location_data(parts, result)
                res['type'] = 'ALARM'
                return res
            elif command == 'bphrt':
                result.update(ProtocolDecoder._parse_health_data(cmd_parts[1:]))
                return result
            elif command == 'oxygen':
                result.update(ProtocolDecoder._parse_spo2_data(cmd_parts[1:]))
                return result
            # TKQ, TKQ2, etc return basic result (enough to trigger connection register)
            if command in ['FALLDOWN', 'FIND', 'LSSET', 'RESET', 'POWEROFF', 'FACTORY']:
                result['type'] = 'CMD_REPLY'
                
            return result
            
        except Exception as e:
            ProtocolDecoder._log(f"Error parsing text protocol: {e}", 'ERROR')
            return None

    @staticmethod
    def _parse_location_data(parts: list, base_data: Dict) -> Dict:
        try:
            content = parts[3]
            data_parts = content.split(',')
            
            if len(data_parts) < 10: return base_data
            
            raw_lat = data_parts[4]
            raw_lng = data_parts[6]
            
            try:
                lat = float(raw_lat)
                if data_parts[5] == 'S': lat = -abs(lat)
                else: lat = abs(lat)
                
                lng = float(raw_lng)
                if data_parts[7] == 'W': lng = -abs(lng)
                else: lng = abs(lng)
            except:
                lat, lng = 0.0, 0.0

            # Parse Device Status (Hex)
            dev_status = data_parts[16] if len(data_parts) > 16 else "0"
            status_int = 0
            try:
                status_int = int(dev_status, 16)
            except:
                pass
            
            # Check bits (Right-to-Left, 0-indexed)
            # Bit 16 (0x10000) = SOS
            # Bit 21 (0x200000) = Fall Down (00200000)
            is_sos = bool(status_int & 0x10000)
            is_fall = bool(status_int & 0x200000)
            is_low_bat = bool(status_int & 0x20000) # 0x00020000 (Bit 17? Need verify, assuming standard) or Low Battery Alarm logic
            
            base_data.update({
                'type': 'POSITION',
                'lat': lat,
                'lng': lng,
                'gps_valid': data_parts[3] == 'A',
                'date': data_parts[1],
                'time': data_parts[2],
                'speed': float(data_parts[8]) if data_parts[8] else 0.0,
                'direction': float(data_parts[9]) if data_parts[9] else 0.0,
                'satellites': int(data_parts[12]) if len(data_parts) > 12 and data_parts[12].isdigit() else 0,
                'gsm_signal': int(data_parts[13]) if len(data_parts) > 13 and data_parts[13].isdigit() else 0,
                'battery': int(data_parts[14]) if len(data_parts) > 14 and data_parts[14].isdigit() else 0,
                'status_hex': dev_status,
                'alarm_sos': is_sos,
                'alarm_fall': is_fall
            })
            
            # If explicit AL type or flags are set, refine it
            if base_data.get('command') in ['AL', 'AL_LTE'] or is_fall or is_sos:
                 if is_fall: base_data['alarm_type'] = 'FALL_DOWN'
                 elif is_sos: base_data['alarm_type'] = 'SOS'
                 elif base_data.get('command') in ['AL', 'AL_LTE']: base_data['alarm_type'] = 'OTHER'
            
            return base_data
        except:
            return base_data

    @staticmethod
    def _parse_heartbeat(cmd_parts: list, base_data: Dict) -> Dict:
        try:
            base_data.update({
                'type': 'HEARTBEAT',
                'steps': int(cmd_parts[1]) if len(cmd_parts) > 1 else 0,
                'tumbles': int(cmd_parts[2]) if len(cmd_parts) > 2 else 0,
                'battery': int(cmd_parts[3]) if len(cmd_parts) > 3 else 0
            })
            return base_data
        except:
            return base_data

    @staticmethod
    def _parse_health_data(data_parts: list) -> Dict:
        try:
            return {
                'type': 'HEALTH_DATA',
                'bp_systolic': int(data_parts[0]) if data_parts[0] != '0' else None,
                'bp_diastolic': int(data_parts[1]) if data_parts[1] != '0' else None,
                'heart_rate': int(data_parts[2]) if data_parts[2] != '0' else None,
            }
        except:
            return {'type': 'HEALTH_DATA'}
    
    @staticmethod
    def _parse_spo2_data(data_parts: list) -> Dict:
        try:
            return {
                'type': 'SPO2_DATA',
                'spo2': int(data_parts[1]) if len(data_parts) > 1 else None,
                'measurement_type': "Manual" if data_parts[0] == '0' else "Auto"
            }
        except:
            return {'type': 'SPO2_DATA'}

    @staticmethod
    def generate_reply(packet_data: Dict) -> Optional[bytes]:
        try:
            if not packet_data: return None
            
            if packet_data.get('protocol') == 'TEXT':
                manufacturer = packet_data.get('manufacturer', '3G')
                device_id = packet_data.get('device_id', '0000000000')
                command = packet_data.get('command', '')
                
                # Command replies defined in instr.md
                # Command replies defined in instr.md
                if command == 'LK':
                    return f"[{manufacturer}*{device_id}*0002*LK]".encode('ascii')
                elif command in ['AL', 'AL_LTE']:
                    return f"[{manufacturer}*{device_id}*0002*AL]".encode('ascii')
                elif command == 'CONFIG':
                     # Reply with 1 (Success)
                     return f"[{manufacturer}*{device_id}*0003*CONFIG,1]".encode('ascii')
                elif command == 'bphrt':
                    return f"[{manufacturer}*{device_id}*0005*bphrt]".encode('ascii')
                elif command == 'oxygen':
                    return f"[{manufacturer}*{device_id}*0007*oxygen,1]".encode('ascii')
                elif command == 'TKQ':
                    return f"[{manufacturer}*{device_id}*0003*TKQ]".encode('ascii')
                elif command == 'TKQ2':
                    return f"[{manufacturer}*{device_id}*0004*TKQ2]".encode('ascii')
                
                # NOTE: We do NOT reply to CR, hrtstart, or other setting commands 
                # because those are responses/ACKs from the device to our requests.
                # Replying to them would cause an infinite loop (Server sends CR -> Device ACKs CR -> Server ACKs CR -> ...)

        except Exception as e:
            ProtocolDecoder._log(f"Error generating reply: {e}", 'ERROR')
        return None

    @staticmethod
    def _parse_binary_protocol(packet_hex: str, packet_bytes: bytes) -> Optional[Dict]:
        return None

def handle_client(conn, addr):
    log_info(f"New connection from {addr[0]}:{addr[1]}")
    buffer = b""
    packet_count = 0
    current_device_id = None
    
    with conn:
        while True:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    log_info(f"Client disconnected: {addr}")
                    break
                
                buffer += chunk
                
                while True:
                    # Search for packet start and end in bytes to preserve binary integrity
                    start = buffer.find(b'[')
                    if start == -1: 
                        # No start found, clear buffer if it gets too large to avoid memory issues
                        # But be careful not to discard partial packets at the end
                        if len(buffer) > 2048:
                            buffer = b"" 
                        break
                    
                    end = buffer.find(b']', start)
                    if end == -1:
                        # Start found but no end, wait for more data
                        break
                        
                    # Extract complete packet
                    packet_bytes = buffer[start:end+1]
                    
                    # Remove processed packet from buffer
                    buffer = buffer[end+1:]
                    
                    packet_count += 1
                    packet_hex = packet_bytes.hex().upper()
                    
                    # Try to decode for logging, but don't crash if binary
                    try:
                        packet_log_str = packet_bytes.decode('ascii')
                    except:
                        packet_log_str = f"<Binary: {packet_hex[:20]}...>"
                        
                    log_info(f"📥 Raw Packet ({addr[0]}): {packet_log_str}")
                    
                    parsed = ProtocolDecoder.parse_packet(packet_hex)
                    if not parsed:
                        log_info("⚠️ Failed to parse packet (returned None)")
                    
                    if parsed:
                        dev_id = parsed.get('device_id')
                        if dev_id and dev_id != 'unknown':
                            current_device_id = dev_id
                            
                            # CAPTURE MANUFACTURER
                            mfg = parsed.get('manufacturer', '3G')
                            _update_device_metadata(dev_id, mfg)
                            
                            register_device_connection(dev_id, conn)

                        reply = ProtocolDecoder.generate_reply(parsed)
                        if reply:
                            conn.sendall(reply)
                        
                        if parsed.get('type') in ['HEALTH_DATA', 'SPO2_DATA']:
                            parsed['device_id'] = parsed.get('device_id', 'unknown')
                            save_health_data(parsed)
                        if parsed.get('type') == 'HEARTBEAT':
                            parsed['device_id'] = parsed.get('device_id', 'unknown')
                            save_heartbeat(parsed)
                        if parsed.get('type') == 'POSITION':
                            parsed['ip'] = addr[0]
                            save_location(parsed)
                        if parsed.get('type') == 'ALARM':
                            parsed['device_id'] = parsed.get('device_id', 'unknown')
                            save_location(parsed) # Saving alarm loc same as position for now
                        
                        # Save Command Replies (FALLDOWN, FIND, etc)
                        if parsed.get('type') == 'CMD_REPLY':
                             # 1. Save to daily log as system event (History)
                             _save_to_daily_log(
                                 parsed.get('device_id', 'unknown'), 
                                 {'raw': parsed.get('raw'), 'cmd': parsed.get('command')}, 
                                 'CMD_REPLY'
                             )
                             
                             # 2. Update HOT device document (Real-time status)
                             _get_or_create_device(
                                 parsed.get('device_id', 'unknown'),
                                 {
                                     'last_command_reply': parsed.get('command'),
                                     'last_command_raw': parsed.get('raw'),
                                     'last_command_timestamp': firestore.SERVER_TIMESTAMP
                                 }
                             )
                
                # Binary skip (Legacy/Alternative protocol check)
                pass

            except ConnectionResetError:
                log_info(f"Connection reset: {addr}")
                break
            except Exception as e:
                log_error(f"Error processing connection: {e}")
                break
        
        # Cleanup
        addr_str = f"{addr[0]}:{addr[1]}"
        with active_connections_lock:
             if addr_str in active_connections:
                 del active_connections[addr_str]
        
        if current_device_id:
            with connected_devices_lock:
                if connected_devices.get(current_device_id) == conn:
                    del connected_devices[current_device_id]
            # Cleanup metadata? Maybe keep it for cache.
            
    log_info(f"Session finished {addr} | Packets: {packet_count}")


def start_server():
    initialize_firebase()
    log_info(f"GPS Server v4.0 Started | Port: {PORT}")
    log_info(f"Host: {HOST} | Protocol: Setracker/Beesure Official")
    
    cmd_thread = threading.Thread(target=listen_to_firestore_commands, daemon=True)
    cmd_thread.start()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
            s.listen(5)
            log_info("Waiting for connections...")
            
            while True:
                conn, addr = s.accept()
                addr_str = f"{addr[0]}:{addr[1]}"
                with active_connections_lock:
                    active_connections[addr_str] = conn
                
                t = threading.Thread(target=handle_client, args=(conn, addr))
                t.daemon = True
                t.start()
                
        except KeyboardInterrupt:
            log_info("Server stopped by user")
        except Exception as e:
            log_error(f"Server crash: {e}")

if __name__ == "__main__":
    start_server()
