# 🚀 ScoShow Professional Edition - Deployment Guide

## 📦 Executables

### 🖥️ ScoShow Professional Client
**File:** `ScoShow_Professional_Client.exe`
- **Purpose:** Advanced MQTT display client with debug capabilities
- **Features:**
  - Multi-monitor support
  - Background image display
  - Real-time MQTT communication
  - Debug logging and status reporting
  - Fullscreen toggle support

### 🎮 ScoShow Super Remote Control  
**File:** `ScoShow_Super_Remote.exe`
- **Purpose:** Advanced tournament management remote control
- **Features:**
  - Smart data parsing (line-by-line, tab-separated formats)
  - Monitor state management (remembers fullscreen/background per monitor)
  - MQTT communication with targeted client selection
  - Round number display customization
  - Real-time status monitoring

## 🎯 Quick Start

### Client Setup:
1. Run `ScoShow_Professional_Client.exe`
2. Ensure `background` folder is in the same directory
3. Configure MQTT settings if needed (via `mqtt_session.json`)

### Remote Control Setup:
1. Run `ScoShow_Super_Remote.exe`
2. Configure remote settings if needed (via `remote_config.json`)
3. Connect to client via MQTT
4. Use data parsing features for tournament ranking

## 🔧 Configuration Files

- **mqtt_session.json:** MQTT broker connection settings
- **remote_config.json:** Remote control preferences and positions
- **background/:** Image files for display backgrounds

## ✨ New Features in v2.0

### State Management:
- Each monitor remembers its own background and fullscreen state
- Switching between monitors automatically restores previous settings
- No need to manually reconfigure when returning to a monitor

### Enhanced Data Parsing:
- Support for multiple data formats (line-by-line, columnar, tab-separated)
- Smart format detection
- Round number extraction and display customization

### Improved MQTT Communication:
- Targeted client commands (no more broadcast issues)
- Real-time status monitoring
- Enhanced error handling and logging

## 🛠️ Build Information

Built with:
- PyInstaller 6.3.0
- PyQt5 5.15.10
- paho-mqtt 1.6.1
- Python 3.13

Created on: August 13, 2025
Version: 2.0.0.0
Company: ScoShow Professional Systems
