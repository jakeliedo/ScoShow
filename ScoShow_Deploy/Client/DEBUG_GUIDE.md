# 🔧 ScoShow Client - Debug Guide

## 📋 **Available Client Versions**

### 🖥️ **ScoShow_Client.exe** (Production)
- **Use**: Normal tournament use
- **Features**: Clean GUI, system tray, no console
- **Auto-detect**: Background folder automatically detected

### 🔧 **ScoShow_Client_Console.exe** (Debug)
- **Use**: Troubleshooting and debugging
- **Features**: Console output, detailed logging, debug messages
- **Auto-detect**: Same auto-detection with verbose logging

## 🚀 **Quick Start (Production)**

1. **Extract** `ScoShow_Client.exe` to any folder
2. **Place** `background` folder (with 00.jpg, 01.png, 02.png) in same directory
3. **Run** `ScoShow_Client.exe`
4. **Check** system tray for client icon
5. **Ready** to receive commands from Remote

## 🔍 **Debug Mode (Troubleshooting)**

### When to Use Console Version:
- ❌ Background folder not detected
- ❌ MQTT connection issues  
- ❌ Commands not received
- ❌ Display not opening
- ❌ General troubleshooting

### Debug Steps:
1. **Close** any running ScoShow Client
2. **Run** `ScoShow_Client_Console.exe`
3. **Watch** console output for errors
4. **Look** for these key messages:

#### ✅ **Success Messages:**
```
✅ Background folder auto-detected: D:\path\to\background
✅ Successfully connected to MQTT broker!
✅ System tray icon created and shown
📤 Status sent: online - Client connected and ready
```

#### ❌ **Error Messages:**
```
❌ Background folder not found at: D:\path\to\background
❌ Failed to connect to MQTT broker: [error]
💡 Check internet connection and firewall settings
```

## 📂 **Background Folder Setup**

### ✅ **Correct Structure:**
```
Your_Folder\
├── ScoShow_Client.exe
└── background\
    ├── 00.jpg    (or .png/.jpeg)
    ├── 01.png    (or .jpg/.jpeg)  
    └── 02.png    (or .jpg/.jpeg)
```

### 🔍 **Debug Output:**
```
📂 Auto-detecting background folder...
🔧 Running as executable from: D:\Your_Folder
📁 Looking for background folder at: D:\Your_Folder\background
📋 Found background files: ['00.jpg', '01.png', '02.png']
✅ Background folder auto-detected: D:\Your_Folder\background
```

## 🌐 **MQTT Connection Debug**

### ✅ **Success Pattern:**
```
🔄 Attempting to connect to MQTT broker...
📡 Broker: test.mosquitto.org:1883
🆔 Session ID: clubvtournamentranking2025
✅ Successfully connected to MQTT broker!
📥 Subscribing to MQTT topics...
   ✓ Subscribed to scoshow_clubvtournamentranking2025/commands
   ✓ Subscribed to scoshow_clubvtournamentranking2025/ranking
   [... more subscriptions ...]
```

### ❌ **Common Issues:**
- **No Internet**: Can't reach test.mosquitto.org
- **Firewall**: Blocking port 1883
- **Network**: Proxy or corporate firewall

## 🎯 **Command Reception Debug**

### 🔍 **Watch for Messages:**
```
📨 Received message on scoshow_clubvtournamentranking2025/commands: {...}
📨 Received message on scoshow_clubvtournamentranking2025/display: {...}
📨 Received message on scoshow_clubvtournamentranking2025/ranking: {...}
```

### 📡 **Topic Patterns:**
- `commands/all` - Broadcast to all clients
- `commands/DESKTOP-NAME` - Targeted to specific computer
- `display/all` - Display control broadcast
- `ranking/all` - Ranking data broadcast

## 💡 **Common Solutions**

### Background Not Detected:
1. Check folder structure (background folder in same directory as exe)
2. Verify image files (00.jpg, 01.png, 02.png)
3. Use console version to see exact paths

### MQTT Connection Failed:
1. Check internet connection
2. Try different network
3. Check firewall settings
4. Restart application

### Commands Not Received:
1. Verify Remote is set to "All Clients (Broadcast)"
2. Check session ID matches between Remote and Client
3. Look for message reception in console

---
**Debug Version**: Console Debug  
**Build Date**: August 14, 2025  
**Console Features**: Full debug logging, background detection details, MQTT verbose output
