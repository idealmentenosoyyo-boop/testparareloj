import socket
import time

HOST = '127.0.0.1'
PORT = 5001

# Trama capturada que causó problemas (coords negativas pero con S/W)
# ASCII: [3G*3707806493*00E7*UD_LTE,230126,170950,V,-33.438529,S,-70.6465013,W,...
PACKET = b"[3G*3707806493*00E7*UD_LTE,230126,170950,V,-33.438529,S,-70.6465013,W,0.00,0.0,0.0,0,77,59,0,0,00000000,0,0,460,00,0000,0000]"

def send_test_packet():
    print(f"Connecting to {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Connected!")
            print(f"Sending packet: {PACKET}")
            s.sendall(PACKET)
            print("Sent! Waiting for potential response...")
            s.settimeout(2.0)
            try:
                data = s.recv(1024)
                print(f"Received: {data}")
            except socket.timeout:
                print("No response received (expected for UD packets)")
            
    except ConnectionRefusedError:
        print("❌ Connection refused. Is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_test_packet()
