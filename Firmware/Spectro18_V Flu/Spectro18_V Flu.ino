#include "SparkFun_AS7265X.h"
AS7265X sensor;
const int ledPin = 32;

void setup() {
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, HIGH); // Apagado (lógica invertida)
  Serial.begin(115200);

  if (sensor.begin() == false) {
    Serial.println("Sensor no detectado.");
    while (1);
  }

  Serial.println("LISTO");
}

void loop() {
    if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando == "LIGHT_ON") {
      digitalWrite(ledPin, LOW);
      delay(100);
      Serial.println("LUZ_ENCENDIDA");
      return; // ← Salir inmediatamente, sin medir
    }
    if (comando == "LIGHT_OFF") {
      digitalWrite(ledPin, HIGH);
      delay(100);
      Serial.println("LUZ_APAGADA");
      return;
    }
  }


  sensor.takeMeasurements();
 
 

for (int i=0;i<10;i++){
    sensor.takeMeasurements();
 Serial.print("435:");
  Serial.println(sensor.getCalibratedB());
   Serial.print("645:");
  Serial.println(sensor.getCalibratedI());

    Serial.println(",");


  delay(100);
}
      Serial.println(",");
        Serial.println(",");
          Serial.println(",");
              Serial.println(",");
      Serial.println(",");
        Serial.println(",");
          Serial.println(",");
delay(5000);
}
