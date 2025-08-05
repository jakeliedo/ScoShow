# ScoShow MQTT Remote Control System

This system allows you to control ScoShow displays remotely using MQTT communication.

## System Architecture

```
Remote Computer (Control)    MQTT Broker    Client Computer (Display)
┌─────────────────────┐        ┌─────┐        ┌──────────────────────┐
│   scoshow_remote.py │◄──────►│MQTT │◄──────►│  scoshow_client.py   │
│                     │        │     │        │                      │
│  - Control UI       │        │     │        │  - Display Window    │
│  - Send Commands    │        │     │        │  - Receive Commands  │
│  - Monitor Status   │        │     │        │  - System Tray       │
└─────────────────────┘        └─────┘        └──────────────────────┘
```

## Components

### 1. MQTT Broker
- Can be local (on either computer) or cloud-based
- Handles message routing between remote and client
- Popular options: Mosquitto, HiveMQ, AWS IoT Core

### 2. Client Computer (Display)
- Runs `scoshow_client.py`
- Connected to display monitors
- Runs in system tray (background)
- Receives and executes commands via MQTT

### 3. Remote Computer (Control)
- Runs `scoshow_remote.py` 
- Provides UI for controlling the display
- Sends commands via MQTT
- Monitors client status and heartbeat

## Features

### Remote Control Capabilities
- **Display Control**: Open/close display, switch monitors, toggle fullscreen
- **Background Selection**: Choose between Wait (00), Ranking (01), Final (02)
- **Ranking Updates**: Update player rankings with custom positions and fonts
- **Final Results**: Display tournament winners with custom formatting
- **Real-time Status**: Monitor client connection and receive status updates
- **Heartbeat Monitoring**: Automatic client health checking

### Client Features
- **System Tray Operation**: Runs silently in background
- **Auto-reconnect**: Automatically reconnects to MQTT broker
- **Status Reporting**: Sends operation status back to remote
- **Manual Override**: Local controls via system tray menu

## Setup Instructions

### Prerequisites
```bash
pip install paho-mqtt PyQt5 Pillow screeninfo
```

### 1. Setup MQTT Broker

#### Option A: Local Mosquitto Broker
```bash
# Install Mosquitto
# Windows: Download from https://mosquitto.org/download/
# Linux: sudo apt-get install mosquitto mosquitto-clients
# Mac: brew install mosquitto

# Start broker
mosquitto -p 1883
```

#### Option B: Cloud MQTT Broker
- Use HiveMQ Cloud (free tier available)
- Update `mqtt_config.py` with broker details

### 2. Configure MQTT Settings
Edit `mqtt_config.py`:
```python
MQTT_BROKER = "your-broker-ip-or-hostname"
MQTT_PORT = 1883
MQTT_USERNAME = "your-username"  # If required
MQTT_PASSWORD = "your-password"  # If required
```

### 3. Setup Client Computer (Display)
1. Copy all files to client computer
2. Install dependencies
3. Configure `mqtt_config.py` with broker details
4. Run: `python scoshow_client.py`
5. Client will appear in system tray

### 4. Setup Remote Computer (Control)
1. Copy remote files: `scoshow_remote.py`, `mqtt_config.py`
2. Install dependencies: `pip install paho-mqtt PyQt5`
3. Configure `mqtt_config.py` with same broker details
4. Run: `python scoshow_remote.py`

## Usage

### Initial Setup
1. On remote: Set background folder path
2. On remote: Select monitor number
3. Click "Open Display" to initialize client display

### Controlling Rankings
1. Switch to "Ranking" tab
2. Set font settings (font, size, color)
3. Enter round information
4. Fill in player rankings (1st-10th)
5. Adjust positions if needed (x,y coordinates)
6. Click "Apply Ranking"

### Final Results
1. Switch to "Final Results" tab
2. Enter winner and runner-ups
3. Adjust positions if needed
4. Click "Apply Final Results"

### Background Control
1. Use "Display Control" tab
2. Click background buttons:
   - "Wait (00)": Show waiting screen
   - "Ranking (01)": Show current rankings
   - "Final (02)": Show final results

## MQTT Topics

| Topic | Purpose | Direction |
|-------|---------|-----------|
| `scoshow/commands` | General commands | Remote → Client |
| `scoshow/ranking` | Ranking updates | Remote → Client |
| `scoshow/final` | Final results | Remote → Client |
| `scoshow/display` | Display control | Remote → Client |
| `scoshow/background` | Background settings | Remote → Client |
| `scoshow/status` | Status updates | Client → Remote |
| `scoshow/heartbeat` | Health check | Client → Remote |

## Troubleshooting

### Connection Issues
1. Check MQTT broker is running
2. Verify network connectivity
3. Check firewall settings (port 1883)
4. Verify broker IP/hostname in config

### Client Not Responding
1. Check system tray for client icon
2. Right-click tray icon → "Reconnect MQTT"
3. Check status log on remote for error messages
4. Restart client application

### Display Issues
1. Ensure background folder is accessible on client
2. Check monitor configuration
3. Verify file paths in background folder
4. Test with local ScoShow first

### Performance
- Use QoS 1 for reliable delivery
- Monitor network latency
- Consider local MQTT broker for best performance

## Security Considerations

### For Production Use
1. **Authentication**: Enable MQTT username/password
2. **Encryption**: Use MQTT over TLS (port 8883)
3. **Network**: Use VPN for remote access
4. **Firewall**: Restrict MQTT port access

### Example Secure Config
```python
MQTT_BROKER = "your-secure-broker.com"
MQTT_PORT = 8883  # TLS port
MQTT_USERNAME = "scoshow_user"
MQTT_PASSWORD = "strong_password_here"
# Add TLS settings in client configuration
```

## Advanced Features

### Multiple Clients
- Each client can have unique client ID
- Use different topic prefixes per venue
- Centralized control of multiple locations

### Custom Commands
- Extend MQTT message format
- Add new command types
- Implement custom display effects

### Integration
- REST API wrapper around MQTT
- Web-based remote control
- Mobile app integration

## Files Structure
```
ScoShow/
├── main.py                 # Original ScoShow (local)
├── mqtt_config.py          # MQTT configuration
├── scoshow_client.py       # Client application (display)
├── scoshow_remote.py       # Remote control application
├── requirements_mqtt.txt   # MQTT dependencies
└── README_MQTT.md         # This file
```

## Support

For issues or questions:
1. Check MQTT broker logs
2. Review client/remote application logs
3. Test MQTT connectivity with tools like MQTT Explorer
4. Verify network configuration and firewall settings
