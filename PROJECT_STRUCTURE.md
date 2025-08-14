# 📁 ScoShow Project Structure

## 🎯 **Main Files** (Production Ready)

### 🖥️ **Core Applications**
- `main.py` - Tournament display window engine
- `scoshow.py` - Main ScoShow application
- `scoshow_client.py` - Display client (production)
- `scoshow_client_debug.py` - Display client (with debug console)
- `scoshow_remote_super.py` - Remote control application

### ⚙️ **Configuration**
- `mqtt_config.py` - MQTT broker and topic configuration
- `mqtt_session.json` - Session ID storage
- `requirements.txt` - Python dependencies

### 📦 **Build & Deploy**
- `build_executables.bat` - Build .exe files (both windowed and console versions)
- `create_package.bat` - Create deployment package
- `DEPLOYMENT.md` - Deployment instructions

## 📂 **Directories**

### 🎨 **Assets**
- `background/` - Default background images (00.jpg, 01.png, 02.png)

### 📦 **Distribution**
- `ScoShow_Deploy/` - Ready-to-deploy tournament package
  - `Client/` - Display client files with auto background detection
  - `Remote/` - Remote control files with broadcast default
- `dist/` - Built executable files

### 🔧 **Development**
- `.vscode/` - VS Code configuration
- `.git/` - Git repository
- `venv/` - Python virtual environment (if present)

### 📁 **Archive**
- `archive/` - Old/deprecated files moved here during cleanup
  - Old remote versions
  - Test files
  - Debug utilities
  - Old documentation
  - Legacy configuration files

### 🎮 **Hardware Projects**
- `ESP32_TouchRemote/` - Hardware touch remote control project
- `touchscreen_remote/` - Touchscreen interface project

## 🚀 **Quick Start**

### For Development:
1. Install requirements: `pip install -r requirements.txt`
2. Run client: `python scoshow_client_debug.py`
3. Run remote: `python scoshow_remote_super.py`

### For Production:
1. Build executables: `build_executables.bat`
2. Create package: `create_package.bat`
3. Deploy from: `ScoShow_Deploy/`

## 📋 **File Purpose**

### Active Development Files:
```
ScoShow/
├── main.py                     # Core display engine
├── scoshow_client_debug.py     # Client with console debug
├── scoshow_remote_super.py     # Remote control (v2.2)
├── mqtt_config.py              # MQTT configuration
├── build_executables.bat       # Build both exe versions
└── create_package.bat          # Deploy package creation
```

### Production Ready:
```
ScoShow_Deploy/
├── Client/
│   ├── ScoShow_Client.exe          # Production client
│   ├── ScoShow_Client_Console.exe  # Debug client
│   ├── background/                 # Auto-detected images
│   └── DEBUG_GUIDE.md             # Troubleshooting
└── Remote/
    ├── ScoShow_Remote.exe          # Remote control
    └── QUICKSTART.txt              # Setup guide
```

## 🗂️ **Archive Contents**
The `archive/` folder contains historical files that were part of the development process but are no longer needed for production:
- Previous remote control versions
- Test and debugging utilities  
- Old build scripts
- Legacy documentation
- Experimental features

---
**Current Version**: v2.2  
**Last Cleanup**: August 14, 2025  
**Status**: Production Ready  
**Key Features**: Auto Background Detection, Default Broadcast, Console Debug Support
