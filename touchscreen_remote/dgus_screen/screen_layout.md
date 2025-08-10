# DGUS Screen Layout for ScoShow Remote Control
# Screen Size: 800x480 pixels

## Main Screen Layout (ID: 0)

### Header Section (0, 0, 800, 60)
- Background: Dark Blue (#001F)
- Title: "ScoShow Remote Control" (Center, Font 24, White)
- WiFi Status Indicator: (750, 10, 40x40)
- MQTT Status Indicator: (700, 10, 40x40)

### Round Input Section (0, 60, 800, 80)
- Background: Light Gray
- Label: "Round:" (50, 80, Font 16)
- Input Field: Variable 0x1000 (150, 80, 200x40, Font 18)

### Ranking Section (0, 140, 400, 250)
- Title: "Rankings" (50, 140, Font 18, Bold)
- Input Fields (10 players):
  * Position X: 50
  * Width: 300
  * Height: 30
  * Spacing: 35 pixels vertical
  * Labels: "1st:", "2nd:", ... "10th:"
  * Variables: 0x1001 to 0x100A

### Final Results Section (400, 140, 400, 250)
- Title: "Final Results" (450, 140, Font 18, Bold)
- Input Fields (5 positions):
  * Position X: 450
  * Width: 300
  * Height: 40
  * Spacing: 50 pixels vertical
  * Labels: "🥇 Winner:", "🥈 2nd:", "🥉 3rd:", "4th:", "5th:"
  * Variables: 0x1010 to 0x1014

### Control Buttons Section (0, 400, 800, 80)
- Button Layout: 6 buttons in a row
- Button Size: 120x40 pixels
- Spacing: 130 pixels horizontal
- Start Position: (50, 400)

Button Details:
1. "Open Display" - Variable: 0x1020, Color: Green
2. "Close Display" - Variable: 0x1021, Color: Red
3. "Show Wait" - Variable: 0x1022, Color: Blue
4. "Show Ranking" - Variable: 0x1023, Color: Orange
5. "Show Final" - Variable: 0x1024, Color: Purple
6. "Switch Monitor" - Variable: 0x1027, Color: Gray

### Action Buttons Section (400, 350, 400, 40)
- "Apply Ranking" - Variable: 0x1025 (450, 350, 150x40, Green)
- "Apply Final" - Variable: 0x1026 (620, 350, 150x40, Orange)

### Status Display Section (600, 400, 200, 80)
- Background: Dark Gray
- Display Status: "Display: ON/OFF" (Variable: 0x2000)
- Current Mode: "Mode: WAIT/RANK/FINAL" (Variable: 0x2003)
- Font: 12, White text

## Color Codes
- Primary Blue: #001F
- Success Green: #07E0
- Warning Orange: #FD20
- Error Red: #F800
- Background Gray: #7BEF
- Text White: #FFFF
- Text Black: #0000

## Touch Event Configuration
All input fields and buttons should be configured with:
- Touch Press: Send variable value = 1
- Touch Release: Send variable value = 0
- For text inputs: Enable keyboard popup

## Communication Protocol
- Baud Rate: 115200
- Data Bits: 8
- Stop Bits: 1
- Parity: None
- Flow Control: None

## Variable Types
- Text Variables (0x1000-0x1014): String, 20 characters max
- Button Variables (0x1020-0x1027): Word (16-bit)
- Status Variables (0x2000-0x2003): Word (16-bit)

## Screen Transitions
Only one main screen required for this application.
All interactions happen on the main screen.
