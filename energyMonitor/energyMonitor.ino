// Include necessary libraries
#include <PZEM004Tv30.h>
#include <SoftwareSerial.h>
#include <PubSubClient.h>
#include <Wire.h>
#include "ESP8266WiFi.h"
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// Define pin connections
#define LED_BUILTIN_OVERRIDE 2
#define SOFTWARE_SERIAL_RX   14     // pin D5
#define SOFTWARE_SERIAL_TX   12     // pin D6

// OLED display
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32

// Define MQTT settings
const char* ssid = "leidergeil";
const char* password = "aquaticflute90";
const char* mqtt_server = "192.168.0.183";
const int mqtt_port = 1883;
const char* mqtt_topic = "home/energy_monitor";

#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);


// Initialize software serial and PZEM
SoftwareSerial pzemSWSerial(SOFTWARE_SERIAL_RX, SOFTWARE_SERIAL_TX);
PZEM004Tv30 pzem(pzemSWSerial);

// Initialize WiFi and MQTT clients
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

float ENERGY_COST = 0.30; // euro per kWh
String displayString;

void setup() {
   // Initialize OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.setRotation(2);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.print("Booting up...");
  display.display(); 
  delay(200);
  
  pinMode(LED_BUILTIN_OVERRIDE, OUTPUT);
  digitalWrite(LED_BUILTIN_OVERRIDE, HIGH);
  Serial.begin(115200);
  
  // Initialize PZEM
  pzem.resetEnergy();
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi");
  display.clearDisplay();
  display.setCursor(0, 0);
  display.print("Connect WiFi");
  display.display(); 
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    display.print(".");
    display.display(); 
  }
  Serial.println("Connected to WiFi!");
  display.setCursor(0, 10);
  display.print("Connected to WiFi!");
  display.display(); 

  // Setup MQTT client
  mqttClient.setServer(mqtt_server, mqtt_port);
  reconnectMQTT();
}

void loop() {  
  // Ensure MQTT connection
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  display.clearDisplay();

  // Read the data from the sensor
  float voltage = pzem.voltage();
  float current = pzem.current();
  float power = pzem.power();
  float energy = pzem.energy();
  float frequency = pzem.frequency();
  float pf = pzem.pf();
  float cost = energy * ENERGY_COST;
  
  // Check if the data is valid
  if (
    isnan(voltage) ||
    isnan(current) ||
    isnan(power) ||
    isnan(energy) ||
    isnan(frequency) ||
    isnan(pf)
  ) {
    Serial.println("Error reading sensor data");
    display.setCursor(0, 0);
    display.print("Error reading sensor data.");
  } else {
    // Format data as a JSON string
    String payload = String("{\"voltage\":") + voltage +
                     ",\"current\":" + current +
                     ",\"power\":" + power +
                     ",\"energy\":" + String(energy, 3) +
                     ",\"frequency\":" + frequency +
                     ",\"pf\":" + pf +
                     ",\"cost\":" + String(energy * ENERGY_COST, 2) +
                     "}";

    // Publish data to MQTT topic
    digitalWrite(LED_BUILTIN_OVERRIDE, LOW);
    mqttClient.publish(mqtt_topic, payload.c_str());
    
    // Print values to the Serial console
    Serial.print("Voltage: ");  Serial.print(voltage);    Serial.print("V\t");
    Serial.print("Current: ");  Serial.print(current);    Serial.print("A\t");
    Serial.print("Power: ");    Serial.print(power);      Serial.print("W\t");
    Serial.print("Energy: ");   Serial.print(energy, 3);  Serial.print("kWh\t");
    Serial.print("PF: ");       Serial.print(pf);         Serial.print("\t");
    Serial.print("Cost: € ");   Serial.println(cost, 2);  Serial.print("\t");

    display.setCursor(0, 0);
    displayString = String(power, 2) + "W";
    displayString += (power > 10) ? "   " : "    ";  // pad spaces depending on length
    displayString += String(energy, 2) + "kWh";
    display.print(displayString);

    display.setCursor(0, 10);
    displayString = String(current, 2) + "A    ";
    displayString +=  "$" + String(cost, 2);
    display.print(displayString);

    display.setCursor(0, 20); 
    display.print(String(pf, 2));
  }
  display.display();
  delay(50);
  digitalWrite(LED_BUILTIN_OVERRIDE, HIGH);
  delay(400);
}

void reconnectMQTT() {
  display.clearDisplay();
  display.display();
  while (!mqttClient.connected()) {
    Serial.print("Connect MQTT");
    display.setCursor(0, 0);
    display.print("Connect MQTT");
    display.display(); 
    if (mqttClient.connect("ArduinoClient")) {
      Serial.println("Connected to MQTT!");
      display.setCursor(0, 10);
      display.print("Connected to MQTT!");
      display.display();
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      display.print(".");
      delay(500);
    }
  }
}
