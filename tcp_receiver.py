#!/usr/bin/env python3
"""
TCP Receiver LEGACY - Server Migration Edition
Solo envia el comando IP para migrar dispositivos al nuevo servidor.
"""

import socket
import datetime
import threading

# Configuration
HOST = '0.0.0.0'
PORT = 5001

# Comando para cambiar al nuevo servidor
NEW_SERVER_COMMAND = "[3G*3707806493*001F*IP,gondola.proxy.rlwy.net,44330]"

def log_info(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [INFO] {msg}")

def log_error(msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [ERROR] {msg}")

def handle_client(conn, addr):
    log_info(f"🔌 New connection from {addr[0]}:{addr[1]}")
    buffer = b""
    command_sent = False
    
    with conn:
        while True:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    log_info(f"Client disconnected: {addr}")
                    break
                
                buffer += chunk
                
                # Buscar paquete completo [...]
                while True:
                    start = buffer.find(b'[')
                    if start == -1:
                        break
                    
                    end = buffer.find(b']', start)
                    if end == -1:
                        break
                    
                    # Extraer paquete
                    packet_bytes = buffer[start:end+1]
                    buffer = buffer[end+1:]
                    
                    try:
                        packet_str = packet_bytes.decode('ascii')
                        log_info(f"📥 Received: {packet_str}")
                        
                        # Extraer device_id del paquete
                        # Formato: [MFG*DEVICEID*LEN*CMD]
                        parts = packet_str.strip('[]').split('*')
                        if len(parts) >= 2:
                            device_id = parts[1]
                            
                            # Enviar comando de cambio de IP solo una vez
                            if not command_sent:
                                # Construir comando con el device_id correcto
                                ip_cmd = f"[3G*{device_id}*001F*IP,gondola.proxy.rlwy.net,44330]"
                                log_info(f"📤 Sending IP change command: {ip_cmd}")
                                conn.sendall(ip_cmd.encode('ascii'))
                                command_sent = True
                                log_info(f"✅ IP command sent to device {device_id}")
                                
                            # Responder LK si es heartbeat para mantener conexión
                            if len(parts) >= 4 and parts[3].startswith('LK'):
                                reply = f"[{parts[0]}*{device_id}*0002*LK]"
                                conn.sendall(reply.encode('ascii'))
                                log_info(f"💓 Heartbeat reply sent")
                                
                    except Exception as e:
                        log_error(f"Error parsing packet: {e}")
                
            except ConnectionResetError:
                log_info(f"Connection reset: {addr}")
                break
            except Exception as e:
                log_error(f"Error: {e}")
                break
    
    log_info(f"Session finished {addr} | Command sent: {command_sent}")

def start_server():
    log_info(f"🚀 GPS Server LEGACY - Migration Mode")
    log_info(f"📡 Port: {PORT}")
    log_info(f"🎯 Target: gondola.proxy.rlwy.net:44330")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((HOST, PORT))
            s.listen(5)
            log_info("Waiting for connections...")
            
            while True:
                conn, addr = s.accept()
                t = threading.Thread(target=handle_client, args=(conn, addr))
                t.daemon = True
                t.start()
                
        except KeyboardInterrupt:
            log_info("Server stopped by user")
        except Exception as e:
            log_error(f"Server crash: {e}")

if __name__ == "__main__":
    start_server()
