import socket
import time
import json
import os
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5001
LOCATIONS_FILE = 'gps_locations.json'

def send_test_packet():
    print(f"Connecting to {HOST}:{PORT}...")
    
    if not os.path.exists(LOCATIONS_FILE):
        print(f"❌ Error: {LOCATIONS_FILE} not found.")
        return

    try:
        with open(LOCATIONS_FILE, 'r') as f:
            locations = json.load(f)
            
        print(f"Loaded {len(locations)} locations from {LOCATIONS_FILE}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Connected! Replaying history...")
            
            for i, loc in enumerate(locations):
                lat = loc.get('lat', 0.0)
                lng = loc.get('lng', 0.0)
                timestamp_str = loc.get('timestamp', '')
                
                # Parse timestamp for protocol fields
                try:
                    dt = datetime.fromisoformat(timestamp_str)
                    date_str = dt.strftime("%d%m%y")
                    time_str = dt.strftime("%H%M%S")
                except:
                    dt = datetime.now()
                    date_str = dt.strftime("%d%m%y")
                    time_str = dt.strftime("%H%M%S")
                
                # S/N and W/E logic
                ns = 'S' if lat < 0 else 'N'
                ew = 'W' if lng < 0 else 'E'
                
                # Construct UD_LTE packet with Valid (A) status
                # Format: [3G*ID*LEN*UD_LTE,DDMMYY,HHMMSS,A,LAT,NS,LNG,EW,...]
                packet_content = f"3G*TEST_DEV_01*00E7*UD_LTE,{date_str},{time_str},A,{abs(lat):.6f},{ns},{abs(lng):.6f},{ew},0.00,0.0,0.0,0,77,59,0,0,00000000,0,0,460,00,0000,0000"
                packet = f"[{packet_content}]"
                
                print(f"Sending packet #{i+1} ({timestamp_str}): {lat}, {lng}")
                s.sendall(packet.encode('ascii'))
                
                time.sleep(1) # Fast forward replay
                
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_test_packet()
