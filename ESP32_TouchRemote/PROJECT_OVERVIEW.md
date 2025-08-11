# ESP32-C3 Touch Remote Control System

## Project Structure
```
ESP32_TouchRemote/
├── main.cpp                 # Main ESP32-C3 firmware
├── README.md               # Project documentation
├── DWIN_UI_Design.md       # Complete UI design specification
├── platformio.ini          # PlatformIO configuration
└── src/                    # Source files (if needed)
```

## Key Features Implemented

### 1. WiFi Configuration
- **Network**: "Roll"
- **Password**: "0908800130"
- **Auto-reconnection**: Yes
- **Status monitoring**: Real-time

### 2. MQTT Integration
- **Broker**: test.mosquitto.org:1883
- **Session ID**: clubvtournamentranking2025
- **Topics**:
  - `scoshow_clubvtournamentranking2025/commands` (Publish)
  - `scoshow_clubvtournamentranking2025/ranking` (Publish)
  - `scoshow_clubvtournamentranking2025/final` (Publish)
  - `scoshow_clubvtournamentranking2025/heartbeat` (Publish)
  - `scoshow_clubvtournamentranking2025/status` (Subscribe)

### 3. DWIN Touch Screen Communication
- **UART Interface**: Hardware Serial 1
- **Pins**: RX=16, TX=17
- **Baud Rate**: 115200
- **Protocol**: DGUS standard

### 4. Remote Control Functions
- **Display Control**: Show/Hide background, Toggle fullscreen, Switch monitor
- **Ranking Input**: Numeric keypad for rank and player name entry
- **Final Results**: Winner selection and custom input
- **Connection Status**: Real-time WiFi and MQTT status display
- **Debug Interface**: System information and testing tools

## UI Pages Designed

### Page 0: Main Menu
- Six main control buttons with icons
- Real-time connection status display
- Navigation to all sub-functions

### Page 1: Display Control
- Background show/hide controls
- Fullscreen toggle
- Monitor switching
- Client status monitoring

### Page 2: Ranking Input
- Numeric keypad (0-9)
- Rank position input
- Player name input
- Send/Clear/Backspace functions

### Page 3: Final Results
- Winner name input
- Quick selection buttons for common names
- Custom winner entry
- Send final results

### Page 4: Settings & Debug
- Connection diagnostics
- Device information display
- System controls (restart, reset)
- Debug log viewer

## Required Icons and Assets

### Status Icons (32x32):
- wifi_connected.ico, wifi_disconnected.ico
- mqtt_connected.ico, mqtt_disconnected.ico
- online_status.ico, offline_status.ico

### Control Icons (64x64):
- display_icon.ico, ranking_icon.ico
- final_icon.ico, settings_icon.ico

### Action Icons (48x48):
- show_bg.ico, hide_bg.ico
- fullscreen.ico, switch_monitor.ico

### Navigation Icons (32x32):
- back_arrow.ico, home_icon.ico
- send_icon.ico, clear_icon.ico

## Touch Button Mapping
- **Main Menu**: 0x1010-0x1015
- **Display Control**: 0x1020-0x1025
- **Ranking Input**: 0x1030-0x1052
- **Final Input**: 0x1060-0x1082
- **Settings**: 0x1090-0x1092

## Installation and Setup
1. Install PlatformIO or Arduino IDE with ESP32 support
2. Install required libraries (PubSubClient, ArduinoJson)
3. Connect DWIN screen to ESP32-C3 (RX=16, TX=17)
4. Upload firmware to ESP32-C3
5. Create DGUS project using the UI design specification
6. Upload DGUS project to DWIN screen
7. Power on and test functionality

## Integration with ScoShow Client
The ESP32 Touch Remote acts as a replacement for the PyQt5 remote control, sending the same MQTT commands and data formats. The existing ScoShow client will receive and process commands without modification.

## Next Steps
1. Create DGUS project file with all pages and icons
2. Test UART communication between ESP32 and DWIN
3. Verify MQTT message compatibility with existing client
4. Add any additional features or customizations as needed
