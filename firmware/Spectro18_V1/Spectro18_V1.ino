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
  // ... imprime los 18 valores calibrados
  Serial.print(sensor.getCalibratedA());
  Serial.print(",");
  Serial.print(sensor.getCalibratedB());
  Serial.print(",");
  Serial.print(sensor.getCalibratedC());
  Serial.print(",");
  Serial.print(sensor.getCalibratedD());
  Serial.print(",");
  Serial.print(sensor.getCalibratedE());
  Serial.print(",");
  Serial.print(sensor.getCalibratedF());
  Serial.print(",");

  Serial.print(sensor.getCalibratedG());
  Serial.print(",");
  Serial.print(sensor.getCalibratedH());
  Serial.print(",");
  Serial.print(sensor.getCalibratedR());
  Serial.print(",");
  Serial.print(sensor.getCalibratedI());
  Serial.print(",");
  Serial.print(sensor.getCalibratedS());
  Serial.print(",");
  Serial.print(sensor.getCalibratedJ());
  Serial.print(",");

  Serial.print(sensor.getCalibratedT());
  Serial.print(",");
  Serial.print(sensor.getCalibratedU());
  Serial.print(",");
  Serial.print(sensor.getCalibratedV());
  Serial.print(",");
  Serial.print(sensor.getCalibratedW());
  Serial.print(",");
  Serial.print(sensor.getCalibratedK());
  Serial.print(",");
  Serial.print(sensor.getCalibratedL());
  Serial.println();
}