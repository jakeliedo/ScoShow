# DWIN Touch Screen UI Design for DMG80480C050_03WTC
# Screen Resolution: 800x480 pixels

## Variable Icons (var_icon) Required:

### Status Icons:
- wifi_connected.ico (32x32) - Green WiFi signal icon
- wifi_disconnected.ico (32x32) - Red WiFi signal icon with X
- mqtt_connected.ico (32x32) - Green cloud icon
- mqtt_disconnected.ico (32x32) - Red cloud icon with X
- online_status.ico (24x24) - Green circle
- offline_status.ico (24x24) - Red circle

### Control Icons:
- display_icon.ico (64x64) - Monitor/screen icon
- ranking_icon.ico (64x64) - Trophy/ranking icon
- final_icon.ico (64x64) - Gold medal icon
- settings_icon.ico (64x64) - Gear/settings icon
- back_arrow.ico (32x32) - Left arrow for navigation
- home_icon.ico (32x32) - House icon for home button

### Action Icons:
- show_bg.ico (48x48) - Eye open icon
- hide_bg.ico (48x48) - Eye closed icon
- fullscreen.ico (48x48) - Expand arrows icon
- switch_monitor.ico (48x48) - Two monitors icon
- send_icon.ico (32x32) - Send/arrow right icon
- clear_icon.ico (32x32) - X or trash icon

## Touch Buttons Required:

### Page 0 - Main Menu (800x480):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ScoShow Touch Remote v1.0                          [WiFi] [MQTT] [Status]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   [Display]     │  │   [Ranking]     │  │    [Final]      │            │
│   │  Control Icon   │  │   Input Icon    │  │  Results Icon   │            │
│   │   Touch: 0x1010 │  │  Touch: 0x1011  │  │  Touch: 0x1012  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   [Settings]    │  │    [Debug]      │  │    [Home]       │            │
│   │  Settings Icon  │  │   Debug Icon    │  │   Home Icon     │            │
│   │  Touch: 0x1013  │  │  Touch: 0x1014  │  │  Touch: 0x1015  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ WiFi: Connected     │ MQTT: Connected     │ Last: --:--:--                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Page 1 - Display Control (800x480):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [←Back] Display Control                              [WiFi] [MQTT] [Status] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │ [Show Background│  │ [Hide Background│  │ [Toggle Full]   │            │
│   │   Show BG Icon  │  │   Hide BG Icon  │  │ Fullscreen Icon │            │
│   │  Touch: 0x1020  │  │  Touch: 0x1021  │  │  Touch: 0x1022  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │ [Switch Monitor]│  │   [Refresh]     │  │    [Status]     │            │
│   │Switch Mon Icon  │  │  Refresh Icon   │  │  Status Icon    │            │
│   │  Touch: 0x1023  │  │  Touch: 0x1024  │  │  Touch: 0x1025  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Client Status: [Online/Offline]    │ Last Command: [Command Name]           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Page 2 - Ranking Input (Grid Layout, 800x480):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [←Back] Ranking Input                                [WiFi] [MQTT] [Status] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────┬───────────────┬───────────────┬───────────────┐         │
│   │ Rank 1: [__]  │ Rank 2: [__]  │ Rank 3: [__]  │ Rank 4: [__]  │         │
│   │ Touch: 0x2000 │ Touch: 0x2001 │ Touch: 0x2002 │ Touch: 0x2003 │         │
│   ├───────────────┼───────────────┼───────────────┼───────────────┤         │
│   │ Rank 5: [__]  │ Rank 6: [__]  │ Rank 7: [__]  │ Rank 8: [__]  │         │
│   │ Touch: 0x2004 │ Touch: 0x2005 │ Touch: 0x2006 │ Touch: 0x2007 │         │
│   ├───────────────┼───────────────┼───────────────┼───────────────┤         │
│   │ Rank 9: [__]  │ Rank 10: [__] │               │               │         │
│   │ Touch: 0x2008 │ Touch: 0x2009 │               │               │         │
│   └───────────────┴───────────────┴───────────────┴───────────────┘         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Touch any rank field to open the numeric keypad for input.               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────┐         │
│   │                      [Confirm Updates]                       │         │
│   │                          Touch: 0x2010                       │         │
│   └───────────────────────────────────────────────────────────────┘         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Numeric Keypad (Pop-up):                                                 │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                                      │
│   │    1    │ │    2    │ │    3    │                                      │
│   └─────────┘ └─────────┘ └─────────┘                                      │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                                      │
│   │    4    │ │    5    │ │    6    │                                      │
│   └─────────┘ └─────────┘ └─────────┘                                      │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                                      │
│   │    7    │ │    8    │ │    9    │                                      │
│   └─────────┘ └─────────┘ └─────────┘                                      │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                                      │
│   │  Clear  │ │    0    │ │    OK   │                                      │
│   └─────────┘ └─────────┘ └─────────┘                                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   After entering the Membership ID, press OK to confirm.                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Page 3 - Final Input (800x480):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [←Back] Final Results                                [WiFi] [MQTT] [Status] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Winner Membership ID: [___________]  (Touch: 0x1060)                     │
│                                                                             │
│   Quick Winners:                                                            │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   Member A      │  │   Member B      │  │   Member C      │            │
│   │   Touch: 0x1070 │  │  Touch: 0x1071  │  │  Touch: 0x1072  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │   Member D      │  │   Member E      │  │   Custom...     │            │
│   │   Touch: 0x1073 │  │  Touch: 0x1074  │  │  Touch: 0x1075  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │     [Clear]     │  │  [Send Final]   │  │   [Preview]     │            │
│   │   Clear Icon    │  │   Send Icon     │  │  Preview Icon   │            │
│   │   Touch: 0x1080 │  │  Touch: 0x1081  │  │  Touch: 0x1082  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Final Winner Membership ID: [___________]     │ Status: Ready to Send       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Page 4 - Settings/Debug (800x480):
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [←Back] Settings & Debug                             [WiFi] [MQTT] [Status] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Connection Status:                                                        │
│   WiFi: [Connected/Disconnected] Signal: [-XX dBm]                         │
│   MQTT: [Connected/Disconnected] Broker: test.mosquitto.org                │
│                                                                             │
│   Device Information:                                                       │
│   ESP32-C3 Touch Remote v1.0                                               │
│   Session ID: clubvtournamentranking2025                                    │
│   Uptime: [XX:XX:XX]                                                        │
│   Free Memory: [XXXX KB]                                                    │
│                                                                             │
│   Actions:                                                                  │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │ [Test MQTT]     │  │ [Reset WiFi]    │  │ [Restart ESP32] │            │
│   │  Test Icon      │  │  Reset Icon     │  │  Restart Icon   │            │
│   │  Touch: 0x1090  │  │  Touch: 0x1091  │  │  Touch: 0x1092  │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│   Debug Log (Last 5 messages):                                             │
│   [10:30:25] MQTT message sent: show_background                             │
│   [10:30:20] Touch event: Display Control                                  │
│   [10:30:15] WiFi reconnected successfully                                  │
│   [10:30:10] Heartbeat sent to broker                                      │
│   [10:30:05] DWIN display initialized                                      │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Last Update: [10:30:25]                 │ Next Heartbeat: [10:31:00]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## DGUS Configuration Requirements:

### Text Variables:
- 0x1000: Main title text
- 0x1001: WiFi status text  
- 0x1002: MQTT status text
- 0x3000-0x3009: Ranking membership IDs (Rank 1-10)
- 0x3010: Final winner membership ID

### Touch Button Addresses:
- Main Menu: 0x1010-0x1015
- Display Control: 0x1020-0x1025  
- Ranking Input Grid: 0x2000-0x2009 (Rank 1-10)
- Ranking Confirm: 0x2010
- Final Input: 0x1060-0x1082
- Settings: 0x1090-0x1092

### Numeric Keypad (Pop-up):
- Numbers 0-9: 0x1040-0x1049
- Clear: 0x1050
- OK: 0x1051
- Backspace: 0x1052

### Icon Variables:
- 0x2000-0x2010: Status icons
- 0x2020-0x2030: Control icons
- 0x2040-0x2050: Action icons

### Colors:
- Background: #1e1e1e (Dark gray)
- Text: #ffffff (White)
- Buttons: #3366cc (Blue)
- Active: #00cc66 (Green)
- Error: #cc3333 (Red)
- Warning: #ff9900 (Orange)
