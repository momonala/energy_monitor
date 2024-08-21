// Include necessary libraries
#include <PZEM004Tv30.h>
#include <SoftwareSerial.h>
#include <PubSubClient.h>
#include <Wire.h>
//#include <LiquidCrystal_I2C.h>
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

//LiquidCrystal_I2C lcd(0x27, 16, 2);
#define OLED_RESET     -1 // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);


// Initialize software serial and PZEM
SoftwareSerial pzemSWSerial(SOFTWARE_SERIAL_RX, SOFTWARE_SERIAL_TX);
PZEM004Tv30 pzem(pzemSWSerial);

// Initialize WiFi and MQTT clients
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

float ENERGY_COST = 0.30; // euro per kWh
String lcdString;;

void setup() {
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.setRotation(2);
  display.clearDisplay();

  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);

  display.println("Hello, world!");
  display.display(); 
  
//  lcd.init();
//  lcd.backlight();
  
  pinMode(LED_BUILTIN_OVERRIDE, OUTPUT);
  digitalWrite(LED_BUILTIN_OVERRIDE, HIGH);
  Serial.begin(115200);
  
  // Initialize PZEM
  pzem.resetEnergy();
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi");
//  lcd.clear();
//  lcd.setCursor(0, 0);
//  lcd.print("Connect WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
//    lcd.print(".");
  }
  Serial.println("Connected to WiFi!");
//  lcd.setCursor(0, 1);
//  lcd.print("Connected to WiFi!");

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
//    lcd.setCursor(0, 1);
//    lcd.print("Error reading sensor data.");
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

//    lcd.setCursor(0, 0);
    lcdString = String(power, 2) + "W ";
    lcdString += String(energy, 2) + "kWh   ";
//    lcd.print(lcdString);

//    lcd.setCursor(0, 1);
    lcdString = String(current, 2) + "A ";
    lcdString +=  "$" + String(cost, 2);
    lcdString +=  " " + String(pf, 2);
//    lcd.print(lcdString);
  }
  delay(50);
  digitalWrite(LED_BUILTIN_OVERRIDE, HIGH);
  delay(200);
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
//    lcd.clear();
//    lcd.setCursor(0, 0);
    Serial.print("Attempting MQTT connection...");
//    lcd.print("Attempting MQTT connection...");
//    lcd.setCursor(0, 1);
    if (mqttClient.connect("ArduinoClient")) {
      Serial.println("Connected to MQTT!");
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(1000);
    }
  }
}
