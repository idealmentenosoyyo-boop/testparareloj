# 📡 API Reference: Frontend Data Layer
Este documento detalla las rutas de Firestore y los esquemas de datos exactos para conectar el Frontend (React) con el Backend (GPS).

---

## 1. 🟢 Datos en Vivo (Dashboard)
**Ruta:** `devices/{deviceID}`  
**Uso:** Mostrar estado actual del dispositivo en tarjetas o lista. Escuchar con `onSnapshot`.

| Campo | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `online` | `boolean` | Estado de conexión (True si ha enviado datos recientemente). | `true` |
| `last_seen` | `Timestamp` | Última vez que el servidor recibió *cualquier paquete*. | `(Timestamp)` |
| `last_battery`| `number` | Nivel de batería (0-100). | `85` |
| **Ubicación** | | | |
| `last_lat` | `number` | Latitud más reciente. | `-33.4385` |
| `last_lng` | `number` | Longitud más reciente. | `-70.6465` |
| `last_gps_timestamp` | `Timestamp` | Cuándo se actualizó la ubicación. | `(Timestamp)` |
| **Salud** | | | |
| `last_hr` | `number` | Último ritmo cardíaco (BPM). | `72` |
| `last_spo2` | `number` | Última saturación de oxígeno (%). | `98` |
| `last_bp` | `string` | Presión arterial (Sys/Dia). | `"120/80"` |
| `last_bp_sys` | `number` | Presión Sistólica (Alta). | `120` |
| `last_bp_dia` | `number` | Presión Diastólica (Baja). | `80` |

---

## 2. 📜 Historial de Eventos (Detalle Dispositivo)
**Ruta:** `devices/{deviceID}/days/{YYYY-MM-DD}/events/{eventID}`  
**Uso:** Gráficos, dibujar ruta en mapa, tabla de historial.  
**Orden sugerido:** `.orderBy('timestamp', 'asc')`

### Tipos de Evento (`event_type`)

#### 📍 `POSITION` (Ubicación)
Se genera cuando llega comando `UD`, `UD2`, `UD_LTE` o `AL`.
```javascript
{
  type: "POSITION",
  lat: -33.4385,
  lng: -70.6465,
  speed: 0.0,
  bat: 85,
  timestamp: (Timestamp),
  valid: true // 'A' del protocolo GPS (Valid vs Void)
}
```

#### ❤️ `HEALTH` (Salud)
Se genera cuando llega comando `bphrt`.
```javascript
{
  type: "HEALTH",
  hr: 72,          // Ritmo cardiaco
  bp_sys: 120,     // Sistólica
  bp_dia: 80,      // Diastólica
  spo2: null,      // (Opcional)
  source: "Auto",  // "Auto" o "Manual"
  timestamp: (Timestamp)
}
```

#### 💓 `HEARTBEAT` (Latido Técnico)
Se genera cada ~5-10 min con comando `LK`.
```javascript
{
  type: "HEARTBEAT",
  bat: 85,
  steps: 1250,    // Pasos del día
  tumbles: 0,     // Caídas detectadas (si aplica)
  timestamp: (Timestamp)
}
```

---

## 3. 🎮 Comandos (Control Remoto)
**Ruta:** `devices/{deviceID}/pending_commands`  
**Acción:** `addDoc()` para enviar una orden al reloj.

| Campo | Valor | Descripción |
| :--- | :--- | :--- |
| `command_raw` | `"CR"` | Solicitar Ubicación Inmediata. |
| | `"hrtstart,1"` | Medir Ritmo Cardíaco (1 vez). |
| | `"UPLOAD,60"` | Configurar intervalo a 60 segundos. |
| | `"FIND"` | Hacer sonar el reloj (Buscar). |
| `status` | `"PENDING"` | **Siempre** iniciar con este estado. |
| `timestamp` | `serverTimestamp()` | Fecha de creación. |

### Ciclo de Vida del Comando
1. **Frontend crea el doc**: `status: "PENDING"`.
2. **Backend lee y envía**: Cambia `status: "SENT"` (y agrega `sent_at`).
3. **Frontend muestra**: "Enviado con éxito ✅".
4. **Error**: Si falla, backend pone `status: "FAILED"`.

---

## 📝 Ejemplo de Consulta (React)

```javascript
// Obtener historial de hoy
const today = new Date().toISOString().split('T')[0]; // "2026-01-23"
const eventsRef = collection(db, `devices/${deviceId}/days/${today}/events`);
const q = query(eventsRef, orderBy("timestamp", "asc"));

onSnapshot(q, (snapshot) => {
  const route = [];
  const healthData = [];
  
  snapshot.forEach(doc => {
    const data = doc.data();
    if (data.type === 'POSITION' && data.lat !== 0) {
      route.push([data.lat, data.lng]);
    }
    if (data.type === 'HEALTH') {
      healthData.push({ time: data.timestamp, hr: data.hr });
    }
  });
  
  // Actualizar estado...
});
```
