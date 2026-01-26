# Guía de Detección de Caídas (Frontend)

Esta guía explica cómo activar la detección de caídas en el reloj y cómo saber cuando ocurre una caída usando los eventos de Firebase.

## 1. Activar Detección (Comandos)

Para que el reloj detecte caídas, debes enviar dos comandos **una sola vez** (o tener un botón de configuración).

Envia a `devices/{id}/pending_commands` con `addDoc`:

### A. Activar Función y Llamada
Activa el algoritmo de caídas y la llamada automática al número de emergencia (SOS).

*   **Comando**: `FALLDOWN,1,1`
    *   `1`: Detección ON.
    *   `1`: Llamar SOS ON (Poner `0` si solo quieres alerta en App).

### B. Ajustar Sensibilidad (Tests)
Para pruebas (sacudir el reloj), usa la máxima sensibilidad.

*   **Comando**: `LSSET,1+8`
    *   `1`: Nivel Actual (1 = Máximo/Gatillo Fácil).
    *   `+8`: Escala Total (Depende del fw, el reloj reportó `LS:8+8`).

---

## 2. Escuchar Caídas (Eventos)

Cuando el reloj detecta una caída, enviará un paquete de alarma. El Backend ahora procesa esto enriqueciendo el evento.

Escucha `devices/{id}/days/{DATE}/events` con `Where('alarm_fall', '==', true)`.

### Esquema del Evento de Caída

```javascript
{
  "event_type": "POSITION", // O "ALARM" si el firmware lo manda como AL
  "type": "POSITION",
  
  // Campos Clave para Frontend
  "alarm_fall": true,       // 🚨 ¡CAÍDA DETECTADA!
  "alarm_sos": false,       // (Si fuera botón SOS, esto sería true)
  "alarm_type": "FALL_DOWN",// (Si entró como paquete ALARM)
  
  "lat": -33.43...,
  "lng": -70.60...,
  "timestamp": (Date),
  "status_hex": "00200000"  // Bit 21 activado
}
```

### Lógica de UI Sugerida

1.  Si recibes un evento con `alarm_fall: true`:
    *   Mostrar alerta roja en pantalla completa.
    *   Reproducir sonido de sirena.
    *   Mostrar ubicación de la caída en mapa.

---

## Resumen para Pruebas

1.  Envía `FALLDOWN,1,0` (Activar sin llamada).
2.  Envía `LSSET,1+8` (Máxima sensibilidad).
3.  Simula caída (lanza el reloj al sofá con giro).
4.  Espera evento con `"alarm_fall": true` en Firestore.
