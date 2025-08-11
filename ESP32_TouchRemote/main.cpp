#include <WiFi.h>
#include <PubSubClient.h>
#include <HardwareSerial.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "Roll";
const char* password = "0908800130";

// MQTT Configuration
const char* mqtt_server = "test.mosquitto.org";
const int mqtt_port = 1883;
const char* session_id = "clubvtournamentranking2025";

// MQTT Topics
String topic_commands;
String topic_ranking;
String topic_final;
String topic_display;
String topic_background;
String topic_heartbeat;
String topic_status;

// DWIN Communication
HardwareSerial dwinSerial(1); // Use UART1 for DWIN communication
const int RX_PIN = 16;
const int TX_PIN = 17;

// MQTT Client
WiFiClient espClient;
PubSubClient client(espClient);

// Device Status
struct DeviceStatus {
  bool wifi_connected = false;
  bool mqtt_connected = false;
  unsigned long last_heartbeat = 0;
  String current_page = "main";
  String last_command = "";
} status;

// DWIN Packet Structure
struct DWINPacket {
  uint8_t header[2] = {0x5A, 0xA5};
  uint8_t length;
  uint8_t command;
  uint16_t address;
  uint8_t data[64];
  uint8_t data_length;
};

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 ESP32-C3 Touch Remote Starting...");
  
  // Initialize DWIN Serial Communication
  dwinSerial.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  Serial.println("🔧 DWIN Serial initialized");
  
  // Initialize MQTT Topics
  initializeMQTTTopics();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Connect to MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  connectToMQTT();
  
  // Initialize DWIN Display
  initializeDWINDisplay();
  
  Serial.println("✅ ESP32-C3 Touch Remote Ready!");
}

void loop() {
  // Maintain WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }
  
  // Maintain MQTT connection
  if (!client.connected()) {
    connectToMQTT();
  }
  client.loop();
  
  // Read DWIN touch events
  readDWINData();
  
  // Send periodic heartbeat
  sendHeartbeat();
  
  // Update connection status on display
  updateConnectionStatus();
  
  delay(100);
}

void initializeMQTTTopics() {
  String base_topic = "scoshow_" + String(session_id);
  topic_commands = base_topic + "/commands";
  topic_ranking = base_topic + "/ranking";
  topic_final = base_topic + "/final";
  topic_display = base_topic + "/display";
  topic_background = base_topic + "/background";
  topic_heartbeat = base_topic + "/heartbeat";
  topic_status = base_topic + "/status";
  
  Serial.println("📋 MQTT Topics initialized:");
  Serial.println("   Commands: " + topic_commands);
  Serial.println("   Ranking: " + topic_ranking);
  Serial.println("   Final: " + topic_final);
  Serial.println("   Display: " + topic_display);
  Serial.println("   Background: " + topic_background);
  Serial.println("   Heartbeat: " + topic_heartbeat);
  Serial.println("   Status: " + topic_status);
}

void connectToWiFi() {
  Serial.print("🔄 Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    status.wifi_connected = true;
    Serial.println("\n✅ WiFi connected!");
    Serial.print("📡 IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    status.wifi_connected = false;
    Serial.println("\n❌ WiFi connection failed!");
  }
}

void connectToMQTT() {
  while (!client.connected()) {
    Serial.print("🔄 Attempting MQTT connection...");
    
    String clientId = "ESP32TouchRemote_" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      status.mqtt_connected = true;
      Serial.println("\n✅ MQTT connected!");
      
      // Subscribe to status topic to receive client responses
      client.subscribe(topic_status.c_str());
      Serial.println("📥 Subscribed to: " + topic_status);
      
    } else {
      status.mqtt_connected = false;
      Serial.print("❌ MQTT connection failed, rc=");
      Serial.print(client.state());
      Serial.println(" retrying in 5 seconds");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.println("📨 MQTT message received:");
  Serial.println("   Topic: " + String(topic));
  Serial.println("   Message: " + message);
  
  // Parse and handle client responses
  handleClientResponse(message);
}

void handleClientResponse(String message) {
  // Parse JSON message from client
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, message);
  
  String messageType = doc["status"];
  
  // Update DWIN display based on client response
  if (messageType == "online") {
    updateDWINText(0x1000, "Client: ONLINE");
  } else if (messageType == "offline") {
    updateDWINText(0x1000, "Client: OFFLINE");
  }
}

void initializeDWINDisplay() {
  Serial.println("🎨 Initializing DWIN Display...");
  
  // Set initial page to main menu
  setDWINPage(0);
  
  // Initialize text fields
  updateDWINText(0x1000, "Touch Remote v1.0");
  updateDWINText(0x1001, "WiFi: Connecting...");
  updateDWINText(0x1002, "MQTT: Connecting...");
  
  Serial.println("✅ DWIN Display initialized");
}

void readDWINData() {
  if (dwinSerial.available()) {
    uint8_t buffer[16];
    int bytesRead = dwinSerial.readBytes(buffer, sizeof(buffer));
    
    if (bytesRead >= 6 && buffer[0] == 0x5A && buffer[1] == 0xA5) {
      // Parse DWIN touch event
      parseDWINTouchEvent(buffer, bytesRead);
    }
  }
}

void parseDWINTouchEvent(uint8_t* buffer, int length) {
  uint8_t cmd = buffer[3];
  uint16_t address = (buffer[4] << 8) | buffer[5];
  
  Serial.printf("🖱️ Touch Event - CMD: 0x%02X, Address: 0x%04X\n", cmd, address);
  
  // Handle different touch events based on address
  switch (address) {
    case 0x1010: // Main Menu - Display Control Button
      handleDisplayControl();
      break;
      
    case 0x1011: // Main Menu - Ranking Input Button
      handleRankingInput();
      break;
      
    case 0x1012: // Main Menu - Final Input Button
      handleFinalInput();
      break;
      
    case 0x1013: // Main Menu - Settings Button
      handleSettings();
      break;
      
    case 0x1020: // Display Control - Show Background
      sendDisplayCommand("show_background");
      break;
      
    case 0x1021: // Display Control - Hide Background
      sendDisplayCommand("hide_background");
      break;
      
    case 0x1022: // Display Control - Toggle Fullscreen
      sendDisplayCommand("toggle_fullscreen");
      break;
      
    case 0x1023: // Display Control - Switch Monitor
      sendDisplayCommand("switch_monitor");
      break;
      
    // Ranking Input - Grid Layout (0x2000-0x2009)
    case 0x2000: case 0x2001: case 0x2002: case 0x2003: case 0x2004:
    case 0x2005: case 0x2006: case 0x2007: case 0x2008: case 0x2009:
      handleRankSelection(address - 0x2000 + 1); // Convert to rank 1-10
      break;
      
    case 0x2010: // Ranking Input - Confirm Updates Button
      handleRankingConfirm();
      break;
      
    // Final Input - Winner Input
    case 0x1060: // Final Input - Winner Membership ID
      handleWinnerSelection();
      break;
      
    case 0x1070: case 0x1071: case 0x1072: case 0x1073: case 0x1074: case 0x1075:
      handleQuickWinnerSelection(address - 0x1070); // Quick winners
      break;
      
    case 0x1081: // Final Input - Send Final
      handleFinalConfirm();
      break;
      
    default:
      Serial.printf("⚠️ Unknown touch address: 0x%04X\n", address);
      break;
  }
}

void handleDisplayControl() {
  Serial.println("🖥️ Opening Display Control page");
  setDWINPage(1);
  status.current_page = "display";
}

void handleRankingInput() {
  Serial.println("🏆 Opening Ranking Input page");
  setDWINPage(2);
  status.current_page = "ranking";
}

void handleFinalInput() {
  Serial.println("🥇 Opening Final Input page");
  setDWINPage(3);
  status.current_page = "final";
}

void handleSettings() {
  Serial.println("⚙️ Opening Settings page");
  setDWINPage(4);
  status.current_page = "settings";
}

void sendDisplayCommand(String command) {
  DynamicJsonDocument doc(1024);
  doc["action"] = command;
  doc["timestamp"] = millis();
  doc["source"] = "touch_remote";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(topic_commands.c_str(), jsonString.c_str());
  
  Serial.println("📤 Display command sent: " + command);
  status.last_command = command;
}

void sendRankingData(int rank, String membershipId) {
  DynamicJsonDocument doc(1024);
  doc["rank"] = rank;
  doc["membership_id"] = membershipId;
  doc["timestamp"] = millis();
  doc["source"] = "touch_remote";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(topic_ranking.c_str(), jsonString.c_str());
  
  Serial.printf("📤 Ranking data sent - Rank: %d, Membership ID: %s\n", rank, membershipId.c_str());
}

void sendAllRankingData() {
  DynamicJsonDocument doc(2048);
  JsonArray rankings = doc.createNestedArray("rankings");
  
  // Read all ranking data from DWIN variables (0x3000-0x3009)
  for (int i = 0; i < 10; i++) {
    uint16_t membershipId = readDWINVariable(0x3000 + i);
    if (membershipId > 0) { // Only send non-empty rankings
      JsonObject ranking = rankings.createNestedObject();
      ranking["rank"] = i + 1;
      ranking["membership_id"] = membershipId;
    }
  }
  
  doc["timestamp"] = millis();
  doc["source"] = "touch_remote";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(topic_ranking.c_str(), jsonString.c_str());
  
  Serial.println("📤 All ranking data sent via MQTT");
}

void sendFinalData(String winnerMembershipId) {
  DynamicJsonDocument doc(1024);
  doc["winner_membership_id"] = winnerMembershipId;
  doc["timestamp"] = millis();
  doc["source"] = "touch_remote";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  client.publish(topic_final.c_str(), jsonString.c_str());
  
  Serial.println("📤 Final data sent - Winner Membership ID: " + winnerMembershipId);
}

void sendHeartbeat() {
  unsigned long currentTime = millis();
  if (currentTime - status.last_heartbeat > 30000) { // Send every 30 seconds
    DynamicJsonDocument doc(1024);
    doc["timestamp"] = currentTime;
    doc["device_id"] = "esp32_touch_remote";
    doc["wifi_connected"] = status.wifi_connected;
    doc["mqtt_connected"] = status.mqtt_connected;
    doc["current_page"] = status.current_page;
    doc["last_command"] = status.last_command;
    doc["uptime"] = currentTime;
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    client.publish(topic_heartbeat.c_str(), jsonString.c_str());
    
    status.last_heartbeat = currentTime;
  }
}

// New handler functions for updated UI
void handleRankSelection(int rank) {
  Serial.printf("🏆 Rank %d selected for input\n", rank);
  // Store current selected rank for keypad input
  // This will be used when numeric keypad pop-up is implemented
  // For now, just log the selection
}

void handleRankingConfirm() {
  Serial.println("✅ Confirming all ranking updates");
  sendAllRankingData();
  
  // Update status display
  updateDWINText(0x1002, "Rankings sent!");
  
  // Optional: Show confirmation message or return to main menu
  delay(1000);
  setDWINPage(0); // Return to main menu
}

void handleWinnerSelection() {
  Serial.println("🥇 Winner selection activated");
  // This will open numeric keypad for winner membership ID input
}

void handleQuickWinnerSelection(int quickIndex) {
  Serial.printf("⚡ Quick winner %d selected\n", quickIndex);
  // Handle predefined quick winner selection
  // You can store predefined membership IDs for quick access
}

void handleFinalConfirm() {
  Serial.println("🏁 Confirming final winner");
  
  // Read winner membership ID from DWIN variable (e.g., 0x3010)
  uint16_t winnerMembershipId = readDWINVariable(0x3010);
  
  if (winnerMembershipId > 0) {
    sendFinalData(String(winnerMembershipId));
    updateDWINText(0x1002, "Final winner sent!");
    
    delay(1000);
    setDWINPage(0); // Return to main menu
  } else {
    updateDWINText(0x1002, "No winner selected!");
  }
}

// Helper function to read DWIN variable
uint16_t readDWINVariable(uint16_t address) {
  // Send read command to DWIN
  uint8_t cmd[] = {0x5A, 0xA5, 0x04, 0x83, 
                   (uint8_t)(address >> 8), (uint8_t)(address & 0xFF), 0x01};
  dwinSerial.write(cmd, sizeof(cmd));
  
  // Wait for response and parse
  delay(10);
  uint16_t value = 0;
  
  if (dwinSerial.available() >= 7) {
    uint8_t response[16];
    int bytesRead = dwinSerial.readBytes(response, sizeof(response));
    
    if (bytesRead >= 7 && response[0] == 0x5A && response[1] == 0xA5) {
      value = (response[5] << 8) | response[6];
    }
  }
  
  return value;
}
    serializeJson(doc, jsonString);
    
    client.publish(topic_heartbeat.c_str(), jsonString.c_str());
    
    status.last_heartbeat = currentTime;
    Serial.println("💓 Heartbeat sent");
  }
}

void updateConnectionStatus() {
  static unsigned long lastUpdate = 0;
  if (millis() - lastUpdate > 5000) { // Update every 5 seconds
    String wifiStatus = status.wifi_connected ? "WiFi: Connected" : "WiFi: Disconnected";
    String mqttStatus = status.mqtt_connected ? "MQTT: Connected" : "MQTT: Disconnected";
    
    updateDWINText(0x1001, wifiStatus);
    updateDWINText(0x1002, mqttStatus);
    
    lastUpdate = millis();
  }
}

// DWIN Communication Functions
void setDWINPage(uint8_t pageNumber) {
  uint8_t command[] = {0x5A, 0xA5, 0x04, 0x80, 0x03, 0x00, pageNumber};
  dwinSerial.write(command, sizeof(command));
  Serial.printf("📄 DWIN page set to: %d\n", pageNumber);
}

void updateDWINText(uint16_t address, String text) {
  uint8_t textBytes[text.length() + 8];
  textBytes[0] = 0x5A;
  textBytes[1] = 0xA5;
  textBytes[2] = text.length() + 5;
  textBytes[3] = 0x82;
  textBytes[4] = (address >> 8) & 0xFF;
  textBytes[5] = address & 0xFF;
  
  for (int i = 0; i < text.length(); i++) {
    textBytes[6 + i] = text[i];
  }
  textBytes[6 + text.length()] = 0xFF;
  textBytes[7 + text.length()] = 0xFF;
  
  dwinSerial.write(textBytes, text.length() + 8);
  Serial.printf("📝 DWIN text updated at 0x%04X: %s\n", address, text.c_str());
}

void updateDWINIcon(uint16_t address, uint16_t iconId) {
  uint8_t command[] = {
    0x5A, 0xA5, 0x05, 0x82,
    (uint8_t)((address >> 8) & 0xFF),
    (uint8_t)(address & 0xFF),
    (uint8_t)((iconId >> 8) & 0xFF),
    (uint8_t)(iconId & 0xFF)
  };
  
  dwinSerial.write(command, sizeof(command));
  Serial.printf("🖼️ DWIN icon updated at 0x%04X: Icon %d\n", address, iconId);
}
