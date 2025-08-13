# 🎪 ScoShow - Deployment Package

## 📦 Package Contents

### 📁 Client\
- **ScoShow_Client.exe** - Display client application
- **background\** - Background images (00.jpg, 01.png, 02.png)
- **QUICKSTART.txt** - Quick setup guide for client

### 📁 Remote\
- **ScoShow_Remote.exe** - Remote control application
- **QUICKSTART.txt** - Quick setup guide for remote

### 📄 Documentation
- **DEPLOYMENT.md** - Detailed deployment instructions
- **README_MQTT.md** - MQTT configuration guide

## 🚀 Quick Setup

### For Display Computer (Client):
1. Copy entire `Client\` folder to display computer
2. Run `ScoShow_Client.exe`
3. Keep it running - it will auto-connect to MQTT

### For Control Computer (Remote):
1. Copy entire `Remote\` folder to control computer
2. Run `ScoShow_Remote.exe`
3. Wait for MQTT connection (green status)
4. Start controlling displays!

## ✨ New Features in This Version

### 🧠 **Smart State Management**
- Each monitor remembers its own settings
- Switching between monitors preserves:
  - Background image
  - Fullscreen mode
  - Display status

### 📊 **Enhanced Data Parsing** 
- Supports multiple data formats:
  - Tab-separated columns
  - Space-separated columns  
  - Line-by-line format
  - Auto-detects format type

### 🎯 **Round Number Display**
- Shows just the number (e.g., "1") instead of "Round 1"
- Cleaner, more minimal display

### 🔧 **Improved MQTT Communication**
- Targeted commands prevent multiple displays
- Better error handling and status feedback
- Real-time client status monitoring

## 🛠️ Technical Requirements

- Windows 10/11
- No Python installation required (standalone executables)
- Network connection for MQTT communication
- Multiple monitors supported

## 📞 Support

If you encounter any issues:
1. Check QUICKSTART.txt files first
2. Review DEPLOYMENT.md for detailed setup
3. Ensure network connectivity for MQTT
4. Make sure background folder is present

---
**Built with PyInstaller | Enhanced with State Management | Powered by MQTT**
