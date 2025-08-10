# ScoShow Touchscreen Remote Setup Guide

## Tổng quan hệ thống

Hệ thống bao gồm 3 thành phần chính:
1. **ScoShow Main** - Chương trình chính trên PC với MQTT client
2. **ESP32-C3** - Board điều khiển kết nối MQTT và màn hình DGUS
3. **DMG80480C050_03WTC** - Màn hình cảm ứng DGUS 5 inch

## Luồng hoạt động

```
[DGUS Display] ←→ [ESP32-C3] ←→ [WiFi/MQTT] ←→ [ScoShow PC]
```

## 1. Cài đặt ScoShow với MQTT

### Yêu cầu Python packages:
```bash
pip install paho-mqtt PyQt5 Pillow screeninfo
```

### Chạy ScoShow với MQTT:
```bash
python touchscreen_remote/scoshow_mqtt_client.py
```

## 2. Cấu hình ESP32-C3

### Hardware Requirements:
- ESP32-C3 Dev Board
- DMG80480C050_03WTC Display
- Jumper wires
- 5V Power supply for display

### Wiring Connections:
```
ESP32-C3    ←→    DGUS Display
GPIO 4      ←→    RX (Serial)
GPIO 5      ←→    TX (Serial)  
GND         ←→    GND
GPIO 2      ←→    Status LED (optional)

DGUS Display Power:
5V          ←→    External 5V supply
GND         ←→    Common GND
```

### Software Setup:
1. Install Arduino IDE
2. Add ESP32 board support
3. Install libraries:
   - PubSubClient
   - ArduinoJson
   - WiFi (built-in)

4. Configure WiFi and MQTT in code:
```cpp
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "YOUR_PC_IP_ADDRESS";
```

5. Upload firmware to ESP32-C3

## 3. Cấu hình DGUS Display

### Requirements:
- DGUS II Tool (DWIN software)
- MicroSD card
- DGUS project files

### Steps:
1. Create new DGUS project with 800x480 resolution
2. Import screen layout từ `screen_layout.md`
3. Configure variables theo `display_config.cfg`
4. Build và generate .bin files
5. Copy files vào MicroSD card
6. Insert SD card vào display và restart

### Variable Configuration trong DGUS Tool:

#### Text Variables:
- 0x1000: Round (String, 20 chars)
- 0x1001-0x100A: Rank 1-10 (String, 20 chars each)
- 0x1010-0x1014: Final 1-5 (String, 20 chars each)

#### Button Variables:
- 0x1020-0x1027: Control buttons (Word type)

#### Status Variables:
- 0x2000-0x2003: Status indicators (Word type)

## 4. MQTT Broker Setup

### Option 1: Local Mosquitto
```bash
# Install Mosquitto
sudo apt install mosquitto mosquitto-clients

# Start service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Test
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test
```

### Option 2: Cloud MQTT
Có thể sử dụng các service như:
- HiveMQ Cloud
- AWS IoT Core  
- Google Cloud IoT

## 5. Testing và Troubleshooting

### Test MQTT Communication:
```bash
# Subscribe to all ScoShow topics
mosquitto_sub -h localhost -t "scoshow/#" -v

# Test commands
mosquitto_pub -h localhost -t "scoshow/commands" -m '{"command":"open_display"}'
mosquitto_pub -h localhost -t "scoshow/display" -m '{"background":"01"}'
```

### Common Issues:

1. **ESP32 không kết nối WiFi:**
   - Kiểm tra SSID/password
   - Kiểm tra signal strength
   - Reset ESP32

2. **MQTT connection failed:**
   - Kiểm tra broker IP/port
   - Firewall settings
   - Network connectivity

3. **DGUS display không phản hồi:**
   - Kiểm tra UART connections
   - Baud rate (115200)
   - Power supply (5V stable)

4. **ScoShow không nhận lệnh:**
   - Kiểm tra MQTT topics
   - JSON format
   - Client connection status

## 6. Protocol Reference

### MQTT Topics:

- `scoshow/commands` - General commands
- `scoshow/display` - Display control
- `scoshow/ranking` - Ranking data
- `scoshow/final` - Final results
- `scoshow/status` - System status
- `scoshow/touch/status` - Touch device status

### Command Examples:

```json
// Open display
{"command": "open_display", "monitor": 0}

// Show background
{"background": "01"}

// Update ranking
{
  "round": "Round 1",
  "1st": "Player A",
  "2nd": "Player B", 
  "apply": true
}

// Update final results
{
  "winner": "Champion",
  "second": "Runner-up",
  "apply": true
}
```

## 7. Customization

### Adding New Functions:
1. Add variables trong DGUS config
2. Update ESP32 firmware handlers
3. Add MQTT message processing trong ScoShow
4. Update screen layout

### Screen Design:
- Use DGUS II Tool để tùy chỉnh giao diện
- Import custom fonts, images
- Configure touch areas và animations

## 8. Deployment

### Production Setup:
1. Configure static IP cho ESP32
2. Setup MQTT broker với authentication
3. Create desktop shortcuts cho ScoShow
4. Document user procedures

### Backup và Recovery:
- Backup DGUS project files
- Backup ESP32 firmware .bin
- Backup ScoShow configuration
- Document all settings và connections
