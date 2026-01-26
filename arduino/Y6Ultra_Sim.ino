#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// --- CONFIGURACIÓN DE RED ---
const char* ssid = "TU_WIFI_NOMBRE"; // <--- CAMBIA ESTO por el nombre de tu WiFi
const char* password = "TU_WIFI_PASSWORD"; // <--- CAMBIA ESTO por tu clave
// Conexión al backend local (IP detectada: 10.50.8.227)
const char* serverUrl = "http://10.50.8.227:3000/api/data"; 

// Variables de estado simulado
float lat = -33.4489; // Santiago, CL
float lng = -70.6693;
int battery = 100;    // Representa % de los 800mAh

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  Serial.print("Conectando a WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConectado al WiFi!");
}

void loop() {
  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // --- LÓGICA DE SIMULACIÓN Y6Ultra ---
    
    // 1. Simular GPS (pequeña variación de movimiento)
    lat += (random(-10, 10) / 100000.0);
    lng += (random(-10, 10) / 100000.0);
    
    // 2. Simular Batería (descarga progresiva)
    if (battery > 0) battery -= 1; 
    else battery = 100; // Recarga simulada

    // 3. Generar JSON
    StaticJsonDocument<512> doc;
    doc["device_id"] = "Y6Ultra-SIM-01";
    
    JsonObject gps = doc.createNestedObject("gps");
    gps["lat"] = lat;
    gps["lng"] = lng;
    gps["accuracy"] = random(5, 20); // Precisión en metros

    JsonObject health = doc.createNestedObject("health");
    health["bpm"] = random(60, 110);    // Heart Rate
    health["spo2"] = random(94, 99);    // Oxígeno
    health["temp"] = random(360, 375) / 10.0; // Temp corporal
    health["bp_sys"] = random(110, 130); // Presión sistólica
    health["bp_dia"] = random(70, 85);   // Presión diastólica

    JsonObject status = doc.createNestedObject("status");
    status["battery_level"] = battery;
    status["charging"] = false;
    // Simular eventos raros (SOS o Caída)
    status["sos_alert"] = (random(0, 1000) > 995); 
    status["fall_detected"] = (random(0, 1000) > 998); 

    String requestBody;
    serializeJson(doc, requestBody);

    // 4. Enviar Datos
    Serial.println("Enviando datos: " + requestBody);
    int httpResponseCode = http.POST(requestBody);
    
    if(httpResponseCode > 0){
      String response = http.getString();
      Serial.println("Respuesta Servidor: " + response);
    } else {
      Serial.print("Error HTTP: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("WiFi desconectado");
  }
  
  // Intervalo de envío (5 segundos)
  delay(5000);
}
