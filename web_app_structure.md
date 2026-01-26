# Estructura App Web de Visualización (Abuelink Dashboard)

Este documento define la arquitectura para la aplicación web que consumirá la nueva estructura de datos de Firebase (`devices/{id}/days/...`).

## 🛠 Tech Stack Recomendado
- **Framework**: React (Vite) - Rápido y ligero.
- **Estilos**: Tailwind CSS - Para diseño "premium" y rápido.
- **Mapas**: React-Leaflet o Google Maps API (Leaflet es gratis).
- **Base de Datos**: Firebase Client SDK.
- **Gráficos**: Recharts (para historial de batería/salud).

## 📂 Estructura de Carpetas

```text
/frontend
  ├── /public              # Assets estáticos (iconos, logos)
  ├── /src
  │    ├── /components     # Componentes Reutilizables
  │    │     ├── /ui       # Botones, Cards, Inputs, Loaders
  │    │     ├── MapView.jsx      # Mapa con Leaflet/Google
  │    │     ├── DeviceCard.jsx   # Tarjeta resumen del reloj
  │    │     ├── HealthChart.jsx  # Gráfico de SV/Pasos
  │    │     └── DatePicker.jsx   # Selector de día de historial
  │    │
  │    ├── /contexts       # Estado Global
  │    │     └── AuthContext.jsx  # Manejo de sesión (si aplica)
  │    │
  │    ├── /hooks          # Hooks personalizados
  │    │     ├── useDevices.js    # Suscripción a 'devices' (tiempo real)
  │    │     └── useDailyLogs.js  # Fetch de 'devices/{id}/days/{date}'
  │    │
  │    ├── /pages
  │    │     ├── Dashboard.jsx    # Vista principal (Lista de relojes)
  │    │     ├── DeviceDetail.jsx # Vista detalle (Mapa + Histórico)
  │    │     └── Login.jsx
  │    │
  │    ├── /services
  │    │     └── firebase.js      # Configuración e inicialización
  │    │
  │    ├── App.jsx         # Router principal
  │    └── main.jsx        # Punto de entrada
```

## 🧠 Lógica de Datos (Firebase)

### 1. Vista General (Dashboard)
Aquí mostramos el estado "en vivo". Usamos los campos de resumen que creamos en el documento raíz del dispositivo.
*   **Query**: `db.collection('devices')` (Escuchar cambios en tiempo real `onSnapshot`).
*   **Datos a mostrar**:
    *   `last_battery` (Icono batería verde/roja).
    *   `online` (Indicador de estado).
    *   `last_seen` (Hace cuánto se reportó).
    *   `last_lat`, `last_lng` (Ubicación actual rápida).

### 2. Vista Detallada (Historial Diario)
Cuando el usuario pincha un reloj y selecciona una fecha.
*   **Query**: `db.collection('devices').doc(deviceID).collection('days').doc('YYYY-MM-DD').collection('events')`.
*   **Orden**: `.orderBy('timestamp', 'asc')`.
*   **Procesamiento**:
    *   `type == 'POSITION'` -> Pintar línea en el mapa.
    *   `type == 'HEARTBEAT'` -> Agregar puntito en el gráfico de batería.
### 3. Pipeline de Comandos (Control Remoto)
El frontend NO habla directo con el dispositivo. Escribe solicitudes en Firestore que el servidor TCP procesa.

*   **Acción**: El usuario clickea botón "Pedir Ubicación" o "Tomar Presión".
*   **Write**: `db.collection('devices/{id}/pending_commands').add(...)`
    ```javascript
    {
      command_raw: "CR", // Comandos: "CR" (Ubicación), "UPLOAD,300" (Intervalo 5min), "hrtstart,1" (Ritmo)
      status: "PENDING",    // Estado inicial
      timestamp: serverTimestamp(),
      user_id: "admin_dashboard" 
    }
    ```
*   **Feedback Visual UI**:
    *   Escuchar cambios en ese documento (`onSnapshot`).
    *   Si `status` cambia a "SENT" -> Mostrar "Comando Enviado 🚀".
    *   Si `status` cambia a "FAILED" -> Mostrar error.
    *   Si llega el dato a `events/` -> Mostrar "Dato Recibido ✅".

## 🎨 Diseño "Premium" (UI/UX)
*   **Tema**: Modo Oscuro por defecto (Dark Mode) con acentos neón suave.
*   **Cards**: "Glassmorphism" (fondo semitransparente borroso) para las tarjetas de dispositivos.
*   **Mapa**: Estilo limpio (sin saturación de iconos).
*   **Animaciones**: Framer Motion para transiciones suaves al cambiar de fecha o de reloj.

## 🚀 Pasos de Implementación
1.  Inicializar proyecto Vite + Tailwind.
2.  Configurar Firebase Client (`firebase.js`).
3.  Crear `useDevices` hook para leer la lista.
4.  Maquetar `Dashboard` con tarjetas.
5.  Implementar Routing dinámico `/device/:id`.
6.  Crear `DeviceDetail` con selector de calendario.
7.  Integrar Mapa y Gráficos.
