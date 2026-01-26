# Preguntas Clave para Soporte Técnico (4P-Touch / Alan Tong)

## 👋 Mensaje de Presentación para Chat (Copy & Paste)
Aquí tienes un mensaje listo para mandar, profesional y directo al grano:

> "Hi Alan, nice to meet you! I'm Lukas, the lead developer for the Abuelink project.
> 
> We have successfully set up the server and the device is already connecting to our IP/Port (5001). However, we have hit 3 specific technical blockers that stop us from going to production.
> 
> Could you please help us clarify these points so we can finish the integration today?"

---

## 🔧 Las 3 Preguntas Técnicas (Mándalas después de la intro)

### 1. Protocol Format Issue (Binary vs Text)
**Contexto:** El manual dice que todo es texto `[3G*...]`, pero el reloj nos manda binario `FF41515348`.
**Pregunta:**
> "Hi Alan. We are receiving data from the device, but it is sending Binary Packets starting with header `FF41515348` instead of the Text Protocol `[3G*...]` described in the documentation.
> 
> Q1: Is there a specific TCP command to switch the device to Text Protocol mode? We prefer working with the standard `[3G*...]` format."

### 2. Incorrect GPS Coordinates (Decoding)
**Contexto:** Al decodificar el binario, las coordenadas nos dan en Argentina/Océano (-39, -66) cuando estamos en Chile (-33, -70).
**Pregunta:**
> "Q2: Regarding the Binary Packet `FF41515348`: We are trying to decode the GPS coordinates (Latitude/Longitude).
> 
> We see 4-byte integers in the payload. 
> - What is the exact formula to convert these bytes to Lat/Lng? 
> - Is it Integer / 10,000,000? 
> - Is it Big Endian or Little Endian?
> 
> Currently, our decoded values are significantly offset from the real location (e.g. we are in Chile, but coordinates show Argentina)."

### 3. Health Data & Encryption
**Contexto:** La respuesta del ritmo cardiaco (`hrtstart`) llega como basura ininteligible (`[QN...`). El chat mencionaba AES128.
**Pregunta:**
> "Q3: When we send the command `[...hrtstart,1]`, we receive a response that looks like garbled text/binary (starts with `[` but contains binary bytes).
> 
> - Is the Health Data response Encrypted (AES128)? 
> - If so, what is the default decryption key? (The chat mentioned 'without MQTT' but cited AES128).
> - Can we disable encryption via a command?"

### 4. 4G GPS Enabling
**Contexto:** Confirmar si el comando que encontramos es el correcto.
**Pregunta:**
> "Q4: To enable GPS reporting on this 4G model, we are using `APPLOCK,DW-1`. Is this the correct and only command needed to wake up the GPS? Or is there another command like `WORKMODE`?"

---
### Resumen para el Chat (Copy & Paste Friendly)

Hi Alan, Lukas here. We have the server running but are facing 3 blockers:

1. Protocol: Device sends binary `FF41515348` instead of text `[3G*...]`. Can we switch it to Text Mode via command?
2. GPS: Decoding the binary payload gives wrong coordinates (wrong country). What is the exact formula for Lat/Lng in the `FF41...` binary packet?
3. Encryption: Heart rate response seems encrypted/garbled. Is AES128 active? What is the key?

Thanks!
