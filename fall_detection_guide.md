# Guía de Detección de Caídas

Esta guía describe cómo configurar y utilizar la función de detección de caídas en el sistema, basándose en la documentación del protocolo (`instr.md`).

## 1. Activar Alerta de Caída

Para activar la detección de caídas y configurar las notificaciones, se debe enviar el comando `FALLDOWN`.

**Comando del Servidor:**
```
[3G*ID_DISPOSITIVO*LEN*FALLDOWN,X,Y]
```

**Parámetros:**
*   **X (Interruptor de Alerta):**
    *   `1`: ACTIVADO (ON)
    *   `0`: DESACTIVADO (OFF)
*   **Y (Llamada al Centro):**
    *   Define si el dispositivo debe llamar al número central tras detectar una caída.
    *   `1`: ACTIVADO (ON) - Llama al centro.
    *   `0`: DESACTIVADO (OFF) - No llama.

**Ejemplo:**
Para activar la detección de caídas y que llame al centro:
`[3G*1234567890*000D*FALLDOWN,1,1]`

**Respuesta del Dispositivo:**
```
[3G*ID_DISPOSITIVO*LEN*FALLDOWN]
```

---

## 2. Configurar Sensibilidad de Detección

Es posible ajustar la sensibilidad del sensor de caídas mediante el comando `LSSET`.

**Comando del Servidor:**
```
[3G*ID_DISPOSITIVO*LEN*LSSET,Sensibilidad+Rango]
```

**Parámetros:**
*   **Sensibilidad:** Nivel actual de sensibilidad (X).
*   **Rango:** Rango total de sensibilidad soportado por el firmware (generalmente 6 u 8).
*   **Nota:** `1` es el nivel MÁS sensible.

**Ejemplos:**
*   Configurar nivel 5 en un rango de 8: `[3G*1234567890*0009*LSSET,5+8]`

**Respuesta del Dispositivo:**
```
[3G*ID_DISPOSITIVO*LEN*LSSET,Sensibilidad]
```

---

## 3. Recepción de Alertas

Cuando el dispositivo detecta una caída (y la función está activa), enviará un paquete de estado o alerta al servidor.

**Indicador de Caída:**
En los paquetes de datos de ubicación o estado (ver Apéndice I en `instr.md`), el estado del dispositivo se reporta en hexadecimal.
*   **Bit 21:** Alarma de caída (Fall down alarm).
*   Si este bit es `1`, indica que se ha detectado una caída.

Además, el campo "Body Tumbling times" en el apéndice puede indicar el conteo de caídas/movimientos bruscos.
