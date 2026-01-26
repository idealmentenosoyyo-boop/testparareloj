# Abuelink Backend

Este servidor recibe datos de telemetría del dispositivo Arduino (Y6Ultra) y los guarda en Firebase Firestore.

## Configuración Local

1. Instalar dependencias:
   ```bash
   npm install
   ```

2. Configurar Credenciales de Firebase:
   - Ve a la Consola de Firebase -> Configuración del Proyecto -> Cuentas de servicio.
   - Genera una nueva clave privada. Se descargará un archivo JSON.
   - Renombra ese archivo a `service-account.json` y colócalo en esta carpeta (`backend/`).
   - **IMPORTANTE:** No subas `service-account.json` a GitHub/Git.

3. Ejecutar servidor:
   ```bash
   npm start
   ```

## Despliegue en Railway

1. Sube este código a un repositorio (asegúrate de que la carpeta `backend` sea la raíz del servicio o configura el "Root Directory" en Railway como `/backend`).
2. En Railway, crea un nuevo servicio desde GitHub.
3. Agrega una Variable de Entorno llamada `FIREBASE_SERVICE_ACCOUNT`.
   - El valor debe ser el contenido **completo** del archivo JSON de tu cuenta de servicio (puedes copiar y pegar todo el texto del JSON).
4. Railway detectará `package.json` e instalará las dependencias automáticamente.
5. Una vez desplegado, Railway te dará una URL (ej: `https://...up.railway.app`).
6. Actualiza el archivo `arduino/Y6Ultra_Sim.ino` con esta nueva URL.
