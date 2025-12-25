#include <Wire.h>
#include <Adafruit_AMG88xx.h>

Adafruit_AMG88xx amg;

void setup() {
  Serial.begin(9600);
  Serial.println("AMG8833 test");

  if (!amg.begin()) {
    Serial.println("Could not find a valid AMG88xx sensor, check wiring!");
    while (1);
  }

  delay(100);
}

void loop() {
  float pixels[AMG88xx_PIXEL_ARRAY_SIZE];
  amg.readPixels(pixels);

  // Imprime la matriz como una cuadrícula 8x8
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    Serial.print(pixels[i]);
    Serial.print("\t");
    if ((i + 1) % 8 == 0) Serial.println();
  }
  Serial.println();

  delay(1000); // Actualiza cada segundo
}