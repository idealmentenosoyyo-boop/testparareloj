#!/usr/bin/env python3
"""
Script para enviar comandos al dispositivo GPS
Basado en protocolo oficial Setracker/Beesure
"""

import socket
import sys
from typing import Optional

# Configuración del servidor
SERVER_HOST = '127.0.0.1'  # Cambiar a IP pública en producción
SERVER_PORT = 5001

# Diccionario de comandos disponibles
COMMANDS = {
    'position': {
        'cmd': 'CR',
        'desc': 'Solicitar posición GPS inmediata (3 min, cada 20s)',
        'example': '[3G*8800000015*0002*CR]'
    },
    'heartrate': {
        'cmd': 'hrtstart,1',
        'desc': 'Medir frecuencia cardíaca y presión arterial una vez',
        'example': '[3G*8800000015*000A*hrtstart,1]'
    },
    'heartrate_stop': {
        'cmd': 'hrtstart,0',
        'desc': 'Detener medición de frecuencia cardíaca',
        'example': '[3G*8800000015*000A*hrtstart,0]'
    },
    'heartrate_auto': {
        'cmd': 'hrtstart,300',
        'desc': 'Medición automática cada 5 minutos',
        'example': '[3G*8800000015*000C*hrtstart,300]'
    },
    'health_auto': {
        'cmd': 'HEALTHAUTOSET,1,1,300',
        'desc': 'Activar medición automática de salud (cada 5 min)',
        'example': '[3G*8800000015*0015*HEALTHAUTOSET,1,1,300]'
    },
    'health_stop': {
        'cmd': 'HEALTHAUTOSET,1,0,300',
        'desc': 'Desactivar medición automática de salud',
        'example': '[3G*8800000015*0015*HEALTHAUTOSET,1,0,300]'
    },
    'upload_interval': {
        'cmd': 'UPLOAD,600',
        'desc': 'Cambiar intervalo de reporte (600s = 10 min)',
        'example': '[3G*8800000015*000A*UPLOAD,600]'
    },
    'reset': {
        'cmd': 'RESET',
        'desc': 'Reiniciar el dispositivo',
        'example': '[3G*8800000015*0005*RESET]'
    },
    'status': {
        'cmd': 'TS',
        'desc': 'Obtener estado del dispositivo',
        'example': '[3G*8800000015*0002*TS]'
    },
    'version': {
        'cmd': 'VERNO',
        'desc': 'Obtener versión del firmware',
        'example': '[3G*8800000015*0005*VERNO]'
    },
    'find': {
        'cmd': 'FIND',
        'desc': 'Hacer sonar el dispositivo (1 minuto)',
        'example': '[3G*8800000015*0004*FIND]'
    },
    'gps_on': {
        'cmd': 'APPLOCK,DW-1',
        'desc': 'ACTIVAR GPS (Requerido para relojes 4G)',
        'example': '[3G*8800000015*000C*APPLOCK,DW-1]'
    },
    'gps_off': {
        'cmd': 'APPLOCK,DW-0',
        'desc': 'Desactivar GPS (Ahorro batería)',
        'example': '[3G*8800000015*000C*APPLOCK,DW-0]'
    },
    'wifi_search': {
        'cmd': 'WIFISEARCH',
        'desc': 'Buscar redes WiFi cercanas (Solo 4G)',
        'example': '[3G*8800000015*000A*WIFISEARCH]'
    },
    'power_off': {
        'cmd': 'POWEROFF',
        'desc': 'Apagar el dispositivo remotamente',
        'example': '[3G*8800000015*0008*POWEROFF]'
    },
    'take_pills': {
        'cmd': 'TAKEPILLS,11:25-1-2,1,Recordatorio',
        'desc': 'Recordatorio de medicamentos (Hora-Switch-Frec)',
        'example': '[3G*8800000015*len*TAKEPILLS...]'
    }
}

class GPSCommander:
    """Cliente para enviar comandos al GPS a través del servidor"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.manufacturer = '3G'  # Puede ser 3G, CS, 4G, etc.
    
    def build_command(self, command: str) -> str:
        """
        Construye el comando en formato [MFG*DEVICEID*LEN*COMMAND]
        """
        # Calcular longitud del comando
        content = command
        length = len(content)
        length_hex = f"{length:04X}"
        
        # Construir comando completo
        full_command = f"[{self.manufacturer}*{self.device_id}*{length_hex}*{content}]"
        return full_command
    
    def send_command(self, command_name: str, custom_params: Optional[str] = None) -> bool:
        """
        Envía un comando al dispositivo a través del servidor
        
        Args:
            command_name: Nombre del comando (ver COMMANDS dict)
            custom_params: Parámetros personalizados (opcional)
        """
        if command_name not in COMMANDS:
            print(f"❌ Comando '{command_name}' no encontrado")
            print(f"\nComandos disponibles:")
            self.list_commands()
            return False
        
        # Obtener comando base
        cmd_data = COMMANDS[command_name]['cmd']
        
        # Usar parámetros personalizados si se proporcionan
        if custom_params:
            cmd_data = f"{cmd_data.split(',')[0]},{custom_params}"
        
        # Construir comando completo
        full_command = self.build_command(cmd_data)
        
        print(f"\n{'='*70}")
        print(f"📤 ENVIANDO COMANDO AL GPS")
        print(f"{'='*70}")
        print(f"   Dispositivo: {self.device_id}")
        print(f"   Comando: {command_name}")
        print(f"   Descripción: {COMMANDS[command_name]['desc']}")
        print(f"   Paquete: {full_command}")
        print(f"{'='*70}\n")
        
        try:
            # Escribir en la cola de comandos del servidor
            try:
                import json
                from pathlib import Path
                
                COMMANDS_FILE = 'pending_commands.json'
                
                commands = []
                if Path(COMMANDS_FILE).exists():
                    try:
                        with open(COMMANDS_FILE, 'r') as f:
                            content = f.read().strip()
                            if content:
                                commands = json.loads(content)
                    except:
                        commands = []
                
                commands.append({
                    'device_id': self.device_id,
                    'command': command_name,
                    'payload': full_command,
                    'timestamp': str(socket.socket) # dummy hash
                })
                
                with open(COMMANDS_FILE, 'w') as f:
                    json.dump(commands, f)
                    
                print("✅ Comando enviado a la cola del servidor")
                print("   El servidor lo despachará en breve.")
                return True
                
            except Exception as e:
                 print(f"❌ Error escribiendo comando: {e}")
                 return False
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def list_commands(self):
        """Muestra todos los comandos disponibles"""
        print(f"\n{'='*70}")
        print(f"📋 COMANDOS DISPONIBLES")
        print(f"{'='*70}\n")
        
        for name, info in COMMANDS.items():
            print(f"• {name}")
            print(f"  {info['desc']}")
            print(f"  Ejemplo: {info['example']}\n")


def main():
    """Función principal del script"""
    
    print(f"\n{'#'*70}")
    print(f"  📡 GPS COMMAND SENDER")
    print(f"{'#'*70}\n")
    
    # Parsear argumentos
    if len(sys.argv) < 3:
        print("Uso: python3 gps_commands.py <DEVICE_ID> <COMANDO> [PARAMETROS]")
        print("\nEjemplos:")
        print("  python3 gps_commands.py 8800000015 position")
        print("  python3 gps_commands.py 8800000015 heartrate")
        print("  python3 gps_commands.py 8800000015 health_auto")
        print("  python3 gps_commands.py 8800000015 upload_interval 300")
        print("\nPara ver todos los comandos:")
        print("  python3 gps_commands.py 8800000015 list")
        sys.exit(1)
    
    device_id = sys.argv[1]
    command = sys.argv[2]
    custom_params = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Crear commander
    commander = GPSCommander(device_id)
    
    # Listar comandos si se solicita
    if command == 'list':
        commander.list_commands()
        return
    
    # Enviar comando
    commander.send_command(command, custom_params)


if __name__ == "__main__":
    main()
