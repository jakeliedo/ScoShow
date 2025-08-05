# ScoShow Remote Control - Deployment Guide

## 📦 Building Executables

### Requirements
- Python 3.7+
- All dependencies installed

### Build Process
1. Run `build_exe.bat` from the project directory
2. Wait for build to complete
3. Executables will be in `dist/` folder:
   - `ScoShow_Client.exe` - For display computers
   - `ScoShow_Remote.exe` - For control computers

## 🚀 Deployment

### For Client Computer (Display)
1. Copy `ScoShow_Client.exe` to target computer
2. Copy `background/` folder to same directory as EXE
3. Run `ScoShow_Client.exe`
4. No additional installation required!

### For Remote Computer (Control)
1. Copy `ScoShow_Remote.exe` to target computer
2. Run `ScoShow_Remote.exe`
3. No additional installation required!

## 🌐 MQTT Configuration Options

### Option 1: Public MQTT Broker (Default)
- Uses `test.mosquitto.org` (free public broker)
- Works instantly without setup
- Both computers need internet connection
- No firewall configuration needed

### Option 2: Local MQTT Broker
If you want to use local network only:

1. **Install Mosquitto MQTT Broker** on one computer:
   - Download from: https://mosquitto.org/download/
   - Install and run as service

2. **Update MQTT configuration**:
   - Edit `mqtt_config.py` before building
   - Change `MQTT_BROKER` to the IP of broker computer
   - Rebuild executables

3. **Network Setup**:
   - Ensure computers are on same network
   - Open port 1883 in firewall

## 📋 Usage Instructions

### Setting Up Display
1. Run `ScoShow_Client.exe` on display computer
2. Keep it running in background

### Using Remote Control
1. Run `ScoShow_Remote.exe` on control computer
2. Wait for "MQTT: Connected" (green status)
3. Wait for "Client: Online" when client connects
4. Use interface to control display:
   - **Display Control**: Open/close display, change backgrounds
   - **Ranking**: Enter and display rankings
   - **Final Results**: Show final tournament results

## 🔧 Troubleshooting

### "MQTT: Disconnected"
- Check internet connection (for public broker)
- Check if broker computer is running (for local broker)

### "Client: Unknown/Timeout"
- Ensure client computer is running ScoShow_Client.exe
- Check both computers use same MQTT broker

### Display not showing
- Click "🚀 Open Display" in remote control
- Select background folder if needed
- Check if client computer has display attached

## 🎯 Features

- **Real-time control** via MQTT messaging
- **Multi-monitor support** with monitor switching
- **Background management** with preview images
- **Live ranking display** with customizable positions
- **Final results screen** for tournament endings
- **Heartbeat monitoring** to check client status
- **No database required** - all data sent via MQTT

## 🔐 Security Notes

- Public MQTT broker is visible to others on internet
- For production use, consider:
  - Private MQTT broker with authentication
  - VPN connection between computers
  - Custom topic names to avoid conflicts
