# ESP32-C3 Touch Remote Project

## Overview
This project implements an ESP32-C3 based touch remote control system using a DWIN DMG80480C050_03WTC touch screen. The ESP32 acts as a bridge between the touch screen and the ScoShow client via MQTT.

## Hardware Requirements
- ESP32-C3 Development Board
- DWIN DMG80480C050_03WTC Touch Screen (5", 800x480, Capacitive)
- Connecting wires for UART communication

## Pin Configuration
- **DWIN UART Communication**:
  - RX Pin: GPIO 16
  - TX Pin: GPIO 17
  - Baud Rate: 115200

## Network Configuration
- **WiFi Network**: "Roll"
- **WiFi Password**: "0908800130"
- **MQTT Broker**: test.mosquitto.org:1883
- **Session ID**: clubvtournamentranking2025

## MQTT Topics
The ESP32 publishes to the following topics:
- `scoshow_clubvtournamentranking2025/commands` - Display control commands
- `scoshow_clubvtournamentranking2025/ranking` - Ranking data input
- `scoshow_clubvtournamentranking2025/final` - Final results input
- `scoshow_clubvtournamentranking2025/heartbeat` - Device status heartbeat

Subscribes to:
- `scoshow_clubvtournamentranking2025/status` - Client status updates

## Dependencies
Add these libraries to your Arduino IDE or PlatformIO:
```
WiFi
PubSubClient
ArduinoJson
HardwareSerial
```

## Installation
1. Install the ESP32 board package in Arduino IDE
2. Install required libraries
3. Upload the code to ESP32-C3
4. Connect DWIN screen to specified pins
5. Power on and test functionality

## Features
- WiFi connectivity with automatic reconnection
- MQTT communication with the ScoShow client
- Touch screen interface for remote control
- Real-time connection status display
- Heartbeat monitoring
- Multiple UI pages (Main, Display Control, Ranking Input, Final Input, Settings)

## Troubleshooting
- Check serial monitor for debugging information
- Verify WiFi credentials
- Ensure MQTT broker is accessible
- Check UART wiring between ESP32 and DWIN screen
