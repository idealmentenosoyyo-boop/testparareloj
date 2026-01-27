#!/usr/bin/env python3
"""
Monitor de datos de salud del GPS tracker
Visualiza HR, BP, SpO2 y genera reportes
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

HEALTH_DATA_FILE = 'health_data.json'
LOCATIONS_FILE = 'gps_locations.json'

class HealthMonitor:
    """Monitor de datos de salud con análisis y alertas"""
    
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """Carga datos de salud desde archivo"""
        if not Path(HEALTH_DATA_FILE).exists():
            return []
        
        with open(HEALTH_DATA_FILE, 'r') as f:
            return json.load(f)
    
    def get_latest(self, limit: int = 10) -> List[Dict]:
        """Obtiene las últimas N mediciones"""
        return self.data[-limit:] if self.data else []
    
    def get_by_timeframe(self, hours: int = 24) -> List[Dict]:
        """Obtiene mediciones de las últimas N horas"""
        if not self.data:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered = []
        for record in self.data:
            record_time = datetime.fromisoformat(record['timestamp'])
            if record_time >= cutoff_time:
                filtered.append(record)
        
        return filtered
    
    def calculate_averages(self, records: List[Dict]) -> Dict:
        """Calcula promedios de los datos"""
        if not records:
            return {}
        
        hr_values = [r['heart_rate'] for r in records if r.get('heart_rate')]
        bp_sys_values = [r['blood_pressure_systolic'] for r in records if r.get('blood_pressure_systolic')]
        bp_dia_values = [r['blood_pressure_diastolic'] for r in records if r.get('blood_pressure_diastolic')]
        spo2_values = [r['spo2'] for r in records if r.get('spo2')]
        
        return {
            'heart_rate_avg': sum(hr_values) / len(hr_values) if hr_values else None,
            'bp_systolic_avg': sum(bp_sys_values) / len(bp_sys_values) if bp_sys_values else None,
            'bp_diastolic_avg': sum(bp_dia_values) / len(bp_dia_values) if bp_dia_values else None,
            'spo2_avg': sum(spo2_values) / len(spo2_values) if spo2_values else None,
            'total_measurements': len(records)
        }
    
    def check_alerts(self, record: Dict) -> List[str]:
        """Verifica si hay alertas médicas"""
        alerts = []
        
        # Frecuencia cardíaca
        hr = record.get('heart_rate')
        if hr:
            if hr > 100:
                alerts.append(f"⚠️ Frecuencia cardíaca ALTA: {hr} BPM (normal: 60-100)")
            elif hr < 60:
                alerts.append(f"⚠️ Frecuencia cardíaca BAJA: {hr} BPM (normal: 60-100)")
        
        # Presión arterial
        bp_sys = record.get('blood_pressure_systolic')
        bp_dia = record.get('blood_pressure_diastolic')
        if bp_sys and bp_dia:
            if bp_sys > 139 or bp_dia > 89:
                alerts.append(f"⚠️ Presión arterial ALTA: {bp_sys}/{bp_dia} mmHg (normal: 90-139/60-89)")
            elif bp_sys < 90 or bp_dia < 60:
                alerts.append(f"⚠️ Presión arterial BAJA: {bp_sys}/{bp_dia} mmHg (normal: 90-139/60-89)")
        
        # SpO2
        spo2 = record.get('spo2')
        if spo2:
            if spo2 < 90:
                alerts.append(f"🚨 Saturación de oxígeno BAJA: {spo2}% (normal: ≥90%)")
            elif spo2 < 95:
                alerts.append(f"⚠️ Saturación de oxígeno PROMEDIO: {spo2}% (óptimo: ≥95%)")
        
        return alerts
    
    def print_summary(self, hours: int = 24):
        """Imprime resumen de las últimas horas"""
        records = self.get_by_timeframe(hours)
        
        if not records:
            print(f"\n❌ No hay datos de salud de las últimas {hours} horas")
            return
        
        averages = self.calculate_averages(records)
        
        print(f"\n{'='*70}")
        print(f"📊 RESUMEN DE SALUD - Últimas {hours} horas")
        print(f"{'='*70}")
        print(f"   Total de mediciones: {averages['total_measurements']}")
        
        if averages.get('heart_rate_avg'):
            print(f"\n   💓 Frecuencia Cardíaca Promedio: {averages['heart_rate_avg']:.1f} BPM")
        
        if averages.get('bp_systolic_avg') and averages.get('bp_diastolic_avg'):
            print(f"   🩸 Presión Arterial Promedio: {averages['bp_systolic_avg']:.1f}/{averages['bp_diastolic_avg']:.1f} mmHg")
        
        if averages.get('spo2_avg'):
            print(f"   🫁 SpO2 Promedio: {averages['spo2_avg']:.1f}%")
        
        print(f"{'='*70}\n")
        
        # Mostrar alertas de las últimas 3 mediciones
        print(f"🚨 ALERTAS RECIENTES:\n")
        recent = records[-3:]
        has_alerts = False
        
        for record in reversed(recent):
            alerts = self.check_alerts(record)
            if alerts:
                has_alerts = True
                timestamp = datetime.fromisoformat(record['timestamp'])
                print(f"   {timestamp.strftime('%Y-%m-%d %H:%M:%S')}:")
                for alert in alerts:
                    print(f"      {alert}")
                print()
        
        if not has_alerts:
            print("   ✅ No hay alertas. Todos los valores en rango normal.\n")
    
    def print_latest(self, limit: int = 5):
        """Imprime las últimas N mediciones"""
        records = self.get_latest(limit)
        
        if not records:
            print("\n❌ No hay datos de salud registrados")
            return
        
        print(f"\n{'='*70}")
        print(f"📋 ÚLTIMAS {len(records)} MEDICIONES")
        print(f"{'='*70}\n")
        
        for i, record in enumerate(reversed(records), 1):
            timestamp = datetime.fromisoformat(record['timestamp'])
            
            print(f"#{i} - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if record.get('heart_rate'):
                print(f"   💓 HR: {record['heart_rate']} BPM")
            
            if record.get('blood_pressure_systolic') and record.get('blood_pressure_diastolic'):
                print(f"   🩸 BP: {record['blood_pressure_systolic']}/{record['blood_pressure_diastolic']} mmHg")
            
            if record.get('spo2'):
                print(f"   🫁 SpO2: {record['spo2']}%")
            
            # Mostrar alertas
            alerts = self.check_alerts(record)
            if alerts:
                for alert in alerts:
                    print(f"   {alert}")
            else:
                print(f"   ✅ Valores normales")
            
            print()
    
    def export_csv(self, filename: str = 'health_export.csv'):
        """Exporta datos a CSV"""
        if not self.data:
            print("❌ No hay datos para exportar")
            return
        
        import csv
        
        with open(filename, 'w', newline='') as f:
            fieldnames = [
                'timestamp', 'device_id', 'heart_rate', 
                'blood_pressure_systolic', 'blood_pressure_diastolic',
                'spo2', 'height_cm', 'weight_kg', 'age', 'gender'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in self.data:
                writer.writerow({
                    'timestamp': record.get('timestamp', ''),
                    'device_id': record.get('device_id', ''),
                    'heart_rate': record.get('heart_rate', ''),
                    'blood_pressure_systolic': record.get('blood_pressure_systolic', ''),
                    'blood_pressure_diastolic': record.get('blood_pressure_diastolic', ''),
                    'spo2': record.get('spo2', ''),
                    'height_cm': record.get('height_cm', ''),
                    'weight_kg': record.get('weight_kg', ''),
                    'age': record.get('age', ''),
                    'gender': record.get('gender', '')
                })
        
        print(f"✅ Datos exportados a {filename}")


def main():
    """Función principal"""
    import sys
    
    monitor = HealthMonitor()
    
    print(f"\n{'#'*70}")
    print(f"  🫀 GPS HEALTH MONITOR")
    print(f"{'#'*70}\n")
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 health_monitor.py latest [N]    - Muestra últimas N mediciones")
        print("  python3 health_monitor.py summary [H]   - Resumen de últimas H horas")
        print("  python3 health_monitor.py export        - Exporta a CSV")
        print("\nEjemplos:")
        print("  python3 health_monitor.py latest 10")
        print("  python3 health_monitor.py summary 24")
        print("  python3 health_monitor.py export")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'latest':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        monitor.print_latest(limit)
    
    elif command == 'summary':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        monitor.print_summary(hours)
    
    elif command == 'export':
        filename = sys.argv[2] if len(sys.argv) > 2 else 'health_export.csv'
        monitor.export_csv(filename)
    
    else:
        print(f"❌ Comando desconocido: {command}")


if __name__ == "__main__":
    main()
