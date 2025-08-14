# 🎯 ScoShow v2.2 - Summary of Changes

## 📋 **Quick Overview**
This update focuses on **Smart Default Settings** and **Enhanced Debug Capabilities** to make ScoShow even easier to set up and troubleshoot.

## ✨ **Key Improvements**

### 📂 **Client: Auto Background Detection** ✅ WORKING
- **Before**: Manual "Select Background Folder" required every time
- **After**: Automatically detects `background` folder in same directory  
- **Impact**: Zero-configuration setup for display computers
- **Debug**: Full console logging shows detection process

### 📡 **Remote: Default Broadcast Mode** ✅ WORKING
- **Before**: Defaulted to "This Computer Only" (confusing for tournaments)
- **After**: Defaults to "All Clients (Broadcast)" mode
- **Impact**: Perfect for multi-display tournament setups

### 🔧 **Debug Console Version** ✅ NEW FEATURE
- **Added**: `ScoShow_Client_Console.exe` for troubleshooting
- **Features**: Full debug output, MQTT logging, background detection details
- **Use Case**: When auto-detection fails or MQTT issues occur

## 🔧 **Technical Changes**

### Client Files Modified:
- `scoshow_client_debug.py` - Added auto background folder detection with debug
- `scoshow_client.py` - Added auto background folder detection
- `build_executables.bat` - Added console version build

### Remote Files Modified:
- `scoshow_remote_super.py` - Changed default target from index 1 to index 0

### Code Changes:
```python
# Client: Auto-detect background folder with executable path detection
if hasattr(sys, '_MEIPASS'):
    exe_dir = os.path.dirname(sys.executable)  # For PyInstaller executable
else:
    exe_dir = os.path.dirname(os.path.abspath(__file__))  # For script
    
default_bg_folder = os.path.join(exe_dir, "background")
self.background_folder = default_bg_folder if os.path.exists(default_bg_folder) else ""

# Remote: Default to broadcast
self.target_client_combo.setCurrentIndex(0)  # "All Clients (Broadcast)"
```

## 🎯 **User Experience Improvements**

### For Tournament Organizers:
1. **Faster Setup**: Drop exe + background folder = ready to go
2. **Less Confusion**: Remote broadcasts by default (expected behavior)  
3. **Fewer Support Questions**: Auto-detection eliminates common setup issues
4. **Debug Tools**: Console version for troubleshooting

### For Technical Staff:
1. **Portable Deployment**: Everything relative to exe location
2. **Consistent Behavior**: Same setup process across all computers
3. **Backward Compatible**: Existing configs still work
4. **Debug Capabilities**: Full console logging for issue resolution

## 📦 **Deployment Ready**

### New File Sizes:
- **Client (Production)**: 50.4 MB (August 14, 2025 12:00 PM)
- **Client (Console Debug)**: 50.5 MB (August 14, 2025 12:01 PM)
- **Remote**: 41.5 MB (August 14, 2025 12:01 PM)

### Enhanced File Structure:
```
ScoShow_Deploy\
├── Client\
│   ├── ScoShow_Client.exe          (Production - Auto background detection)
│   ├── ScoShow_Client_Console.exe  (Debug - Console logging)
│   ├── background\                 (Auto-detected by both versions)
│   ├── DEBUG_GUIDE.md             (Troubleshooting instructions)
│   └── QUICKSTART.txt             (Basic setup guide)
└── Remote\
    ├── ScoShow_Remote.exe          (Defaults to broadcast mode)
    └── QUICKSTART.txt              (Remote setup guide)
```

### Setup Instructions:
1. **For Display Computers**: Extract Client exe + background folder to same directory
2. **For Control Computer**: Extract Remote exe, it's ready to broadcast
3. **For Troubleshooting**: Use ScoShow_Client_Console.exe to see debug output
4. **Start tournament**: No additional configuration needed!

## 🔍 **Debug Output Example**

```
📂 Auto-detecting background folder...
🔧 Running as executable from: D:\Tournament\Client
📁 Looking for background folder at: D:\Tournament\Client\background
📋 Found background files: ['00.jpg', '01.png', '02.png']
✅ Background folder auto-detected: D:\Tournament\Client\background
✅ Successfully connected to MQTT broker!
📤 Status sent: online - Client connected and ready
```

## 🚀 **Next Steps**
The ScoShow system is now optimized for tournament use with minimal setup requirements and comprehensive debug capabilities. Both Client and Remote applications are tournament-ready out of the box with full troubleshooting support.

---
**Version**: 2.2  
**Release Date**: August 14, 2025  
**Compatibility**: Windows 10/11  
**Status**: Ready for Production Use + Debug Support  
**Key Features**: Auto Background Detection ✅, Default Broadcast Mode ✅, Console Debug ✅
