/*
ESP32-C3 Firmware for ScoShow Remote Control
Connects DMG80480C050_03WTC display to ScoShow via MQTT

Hardware connections:
- DMG Display UART: GPIO 4 (TX), GPIO 5 (RX)
- Status LED: GPIO 2
- WiFi: Built-in

DGUS Display Protocol:
- Baud: 115200
- Format: 8N1
- Command format: 5A A5 [LEN] [CMD] [DATA...]
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <HardwareSerial.h>

// Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "YOUR_MQTT_BROKER_IP";
const int mqtt_port = 1883;
const char* mqtt_user = "";
const char* mqtt_pass = "";

// MQTT Topics
const char* topic_commands = "scoshow/commands";
const char* topic_status = "scoshow/status";
const char* topic_display = "scoshow/display";
const char* topic_ranking = "scoshow/ranking";
const char* topic_final = "scoshow/final";
const char* topic_touch_status = "scoshow/touch/status";

// Hardware
#define DGUS_SERIAL Serial1
#define DGUS_TX_PIN 4
#define DGUS_RX_PIN 5
#define STATUS_LED_PIN 2

// DGUS Communication
#define DGUS_HEADER1 0x5A
#define DGUS_HEADER2 0xA5
#define DGUS_READ_VAR 0x83
#define DGUS_WRITE_VAR 0x82

WiFiClient espClient;
PubSubClient mqtt_client(espClient);

// Touch screen variables (DGUS variable addresses)
#define VAR_ROUND 0x1000
#define VAR_RANK1 0x1001
#define VAR_RANK2 0x1002
#define VAR_RANK3 0x1003
#define VAR_RANK4 0x1004
#define VAR_RANK5 0x1005
#define VAR_RANK6 0x1006
#define VAR_RANK7 0x1007
#define VAR_RANK8 0x1008
#define VAR_RANK9 0x1009
#define VAR_RANK10 0x100A

#define VAR_FINAL1 0x1010
#define VAR_FINAL2 0x1011
#define VAR_FINAL3 0x1012
#define VAR_FINAL4 0x1013
#define VAR_FINAL5 0x1014

#define VAR_BTN_OPEN_DISPLAY 0x1020
#define VAR_BTN_CLOSE_DISPLAY 0x1021
#define VAR_BTN_SHOW_WAIT 0x1022
#define VAR_BTN_SHOW_RANK 0x1023
#define VAR_BTN_SHOW_FINAL 0x1024
#define VAR_BTN_APPLY_RANK 0x1025
#define VAR_BTN_APPLY_FINAL 0x1026
#define VAR_BTN_SWITCH_MONITOR 0x1027

// Current state
struct TouchState {
  String round;
  String ranks[10];
  String finals[5];
  bool display_open;
  String current_mode;
} touch_state;

void setup() {
  Serial.begin(115200);
  
  // Initialize DGUS communication
  DGUS_SERIAL.begin(115200, SERIAL_8N1, DGUS_RX_PIN, DGUS_TX_PIN);
  
  // Initialize LED
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);
  
  // Connect to WiFi
  setup_wifi();
  
  // Setup MQTT
  mqtt_client.setServer(mqtt_server, mqtt_port);
  mqtt_client.setCallback(mqtt_callback);
  
  Serial.println("ESP32-C3 ScoShow Remote started");
  
  // Initialize touch screen
  delay(2000);
  init_dgus_display();
}

void loop() {
  if (!mqtt_client.connected()) {
    reconnect_mqtt();
  }
  mqtt_client.loop();
  
  // Read from DGUS display
  read_dgus_data();
  
  // Blink status LED
  static unsigned long last_blink = 0;
  if (millis() - last_blink > 1000) {
    digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
    last_blink = millis();
  }
  
  delay(100);
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect_mqtt() {
  while (!mqtt_client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    String clientId = "ESP32-ScoShow-";
    clientId += String(random(0xffff), HEX);
    
    if (mqtt_client.connect(clientId.c_str(), mqtt_user, mqtt_pass)) {
      Serial.println("connected");
      
      // Subscribe to status topic to get current state
      mqtt_client.subscribe(topic_status);
      
      // Publish touch status
      publish_touch_status("connected");
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqtt_client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void mqtt_callback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.println("Received: " + String(topic) + " -> " + message);
  
  // Parse JSON
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, message);
  
  if (String(topic) == topic_status) {
    // Update local state from ScoShow status
    touch_state.display_open = doc["display_open"];
    touch_state.current_mode = doc["current_mode"].as<String>();
    
    // Update display indicators
    update_display_status();
  }
}

void init_dgus_display() {
  Serial.println("Initializing DGUS display...");
  
  // Set initial values
  write_dgus_text_var(VAR_ROUND, "Round 1");
  
  // Clear ranking fields
  for (int i = 0; i < 10; i++) {
    write_dgus_text_var(VAR_RANK1 + i, "");
  }
  
  // Clear final fields
  for (int i = 0; i < 5; i++) {
    write_dgus_text_var(VAR_FINAL1 + i, "");
  }
  
  Serial.println("DGUS display initialized");
}

void read_dgus_data() {
  if (DGUS_SERIAL.available()) {
    static uint8_t buffer[256];
    static int buffer_pos = 0;
    
    while (DGUS_SERIAL.available() && buffer_pos < sizeof(buffer)) {
      buffer[buffer_pos++] = DGUS_SERIAL.read();
      
      // Check for complete message
      if (buffer_pos >= 3) {
        if (buffer[0] == DGUS_HEADER1 && buffer[1] == DGUS_HEADER2) {
          uint8_t len = buffer[2];
          if (buffer_pos >= len + 3) {
            // Process complete message
            process_dgus_message(buffer, len + 3);
            buffer_pos = 0;
          }
        } else {
          // Invalid header, shift buffer
          memmove(buffer, buffer + 1, buffer_pos - 1);
          buffer_pos--;
        }
      }
    }
  }
}

void process_dgus_message(uint8_t* data, int len) {
  if (len < 6) return;
  
  uint8_t cmd = data[3];
  uint16_t var_addr = (data[4] << 8) | data[5];
  
  if (cmd == DGUS_READ_VAR) {
    // Response to read command
    if (len >= 8) {
      uint16_t value = (data[6] << 8) | data[7];
      handle_var_change(var_addr, value);
    }
  }
}

void handle_var_change(uint16_t var_addr, uint16_t value) {
  Serial.printf("Variable changed: 0x%04X = %d\n", var_addr, value);
  
  // Handle button presses (value > 0 means pressed)
  if (value > 0) {
    switch (var_addr) {
      case VAR_BTN_OPEN_DISPLAY:
        publish_command("open_display");
        break;
        
      case VAR_BTN_CLOSE_DISPLAY:
        publish_command("close_display");
        break;
        
      case VAR_BTN_SHOW_WAIT:
        publish_display_command("00");
        break;
        
      case VAR_BTN_SHOW_RANK:
        publish_display_command("01");
        break;
        
      case VAR_BTN_SHOW_FINAL:
        publish_display_command("02");
        break;
        
      case VAR_BTN_APPLY_RANK:
        read_and_publish_ranking();
        break;
        
      case VAR_BTN_APPLY_FINAL:
        read_and_publish_final();
        break;
        
      case VAR_BTN_SWITCH_MONITOR:
        publish_command("switch_monitor");
        break;
    }
  }
}

void publish_command(const char* command) {
  DynamicJsonDocument doc(256);
  doc["command"] = command;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  mqtt_client.publish(topic_commands, message.c_str());
  Serial.println("Published command: " + message);
}

void publish_display_command(const char* background) {
  DynamicJsonDocument doc(256);
  doc["background"] = background;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  mqtt_client.publish(topic_display, message.c_str());
  Serial.println("Published display: " + message);
}

void read_and_publish_ranking() {
  DynamicJsonDocument doc(1024);
  
  // Read round
  String round = read_dgus_text_var(VAR_ROUND);
  if (round.length() > 0) {
    doc["round"] = round;
  }
  
  // Read rankings
  const char* rank_names[] = {"1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"};
  for (int i = 0; i < 10; i++) {
    String rank_text = read_dgus_text_var(VAR_RANK1 + i);
    if (rank_text.length() > 0) {
      doc[rank_names[i]] = rank_text;
    }
  }
  
  doc["apply"] = true;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  mqtt_client.publish(topic_ranking, message.c_str());
  Serial.println("Published ranking: " + message);
}

void read_and_publish_final() {
  DynamicJsonDocument doc(512);
  
  const char* final_names[] = {"winner", "second", "third", "fourth", "fifth"};
  for (int i = 0; i < 5; i++) {
    String final_text = read_dgus_text_var(VAR_FINAL1 + i);
    if (final_text.length() > 0) {
      doc[final_names[i]] = final_text;
    }
  }
  
  doc["apply"] = true;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  mqtt_client.publish(topic_final, message.c_str());
  Serial.println("Published final: " + message);
}

void write_dgus_text_var(uint16_t var_addr, const String& text) {
  uint8_t cmd[64];
  int pos = 0;
  
  cmd[pos++] = DGUS_HEADER1;
  cmd[pos++] = DGUS_HEADER2;
  cmd[pos++] = 0; // Length placeholder
  cmd[pos++] = DGUS_WRITE_VAR;
  cmd[pos++] = (var_addr >> 8) & 0xFF;
  cmd[pos++] = var_addr & 0xFF;
  
  // Add text data (up to 20 characters)
  for (int i = 0; i < 20 && i < text.length(); i++) {
    cmd[pos++] = text[i];
  }
  
  // Pad with zeros
  while ((pos - 6) < 20) {
    cmd[pos++] = 0;
  }
  
  cmd[2] = pos - 3; // Set length
  
  DGUS_SERIAL.write(cmd, pos);
}

String read_dgus_text_var(uint16_t var_addr) {
  // Send read command
  uint8_t cmd[] = {
    DGUS_HEADER1, DGUS_HEADER2,
    0x04, // Length
    DGUS_READ_VAR,
    (var_addr >> 8) & 0xFF,
    var_addr & 0xFF,
    0x14 // Read 20 bytes
  };
  
  DGUS_SERIAL.write(cmd, sizeof(cmd));
  
  // Wait for response (simplified - in production use proper timeout)
  delay(100);
  
  // This is a simplified version - proper implementation would
  // parse the response message and extract the text
  return ""; // Placeholder
}

void update_display_status() {
  // Update status indicators on touch screen
  // This would involve writing to status variables on the DGUS display
  
  // Example: Set display status LED variable
  uint16_t status_value = touch_state.display_open ? 1 : 0;
  write_dgus_var(0x2000, status_value); // Assuming 0x2000 is status LED variable
}

void write_dgus_var(uint16_t var_addr, uint16_t value) {
  uint8_t cmd[] = {
    DGUS_HEADER1, DGUS_HEADER2,
    0x05, // Length
    DGUS_WRITE_VAR,
    (var_addr >> 8) & 0xFF,
    var_addr & 0xFF,
    (value >> 8) & 0xFF,
    value & 0xFF
  };
  
  DGUS_SERIAL.write(cmd, sizeof(cmd));
}

void publish_touch_status(const char* status) {
  DynamicJsonDocument doc(256);
  doc["status"] = status;
  doc["ip"] = WiFi.localIP().toString();
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  
  mqtt_client.publish(topic_touch_status, message.c_str());
}
