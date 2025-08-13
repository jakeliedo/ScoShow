"""
ScoShow MQTT Remote Control - Super Enhanced Version
This runs on the remote computer for controlling the client display
Enhanced with Data Paste Pop-up and Improved UI
"""

import sys
import json
import time
import os
import re
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QComboBox, QGroupBox, QGridLayout, QFrame,
                             QFileDialog, QMessageBox, QTextEdit, QTabWidget,
                             QSpinBox, QCheckBox, QDialog, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor

try:
    from screeninfo import get_monitors
except ImportError:
    print("Warning: screeninfo not installed. Using default monitor names.")
    def get_monitors():
        return [type('Monitor', (), {'name': f'Monitor {i}', 'width': 1920, 'height': 1080})() for i in range(1, 5)]
        
from mqtt_config import *
import paho.mqtt.client as mqtt

# Setup console logging for debug
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def debug_print(message):
    """Enhanced debug print with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    print(f"[{timestamp}] {message}")
    logger.info(message)
    if sys.stdout:  # Check if stdout exists before flushing
        sys.stdout.flush()

class DataInputPopup(QDialog):
    """Pop-up window for pasting and processing data"""
    
    def __init__(self, parent=None, tab_type="rank"):
        super().__init__(parent)
        self.tab_type = tab_type
        self.parent_window = parent
        self.init_ui()
        
    def init_ui(self):
        """Initialize the pop-up UI"""
        self.setWindowTitle(f"Data Input - {self.tab_type.title()}")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("""
Paste your data here (Tab-separated format):
Round	MB	NAME	Credit	Last Bet
Round 1	60050	HO CUONG DIEU	30900	
Round 1	555	CHWEE WAI ONN	21180	
...
        """)
        instructions.setStyleSheet("font-size: 10px; color: gray; padding: 5px;")
        layout.addWidget(instructions)
        
        # Data input area
        self.data_input = QTextEdit(self)
        self.data_input.setPlaceholderText("Paste your data here...")
        layout.addWidget(self.data_input)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Check button
        self.check_button = QPushButton("✅ Check Data")
        self.check_button.clicked.connect(self.check_data)
        self.check_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.check_button)
        
        # Cancel button
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Preview area
        self.preview_label = QLabel("Data preview will appear here after checking...")
        self.preview_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc; max-height: 100px;")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
    def check_data(self):
        """Process and check the pasted data"""
        raw_data = self.data_input.toPlainText().strip()
        
        if not raw_data:
            QMessageBox.warning(self, "Warning", "No data to process!")
            return
            
        try:
            parsed_data = self.parse_data(raw_data)
            
            if not parsed_data:
                QMessageBox.warning(self, "Warning", "No valid data found!")
                return
                
            # Show preview
            preview_text = f"Found {len(parsed_data)} rows:\n"
            for i, row in enumerate(parsed_data[:5]):  # Show first 5 rows
                preview_text += f"Rank {row.get('position', 'N/A')}: Round {row.get('round', 'N/A')}, MB={row.get('mb', 'N/A')}, Name={row.get('name', 'N/A')}\n"
            if len(parsed_data) > 5:
                preview_text += f"... and {len(parsed_data) - 5} more rows"
                
            # Debug: Print parsed data details
            debug_print(f"🔍 Parsed data details:")
            for i, row in enumerate(parsed_data):
                debug_print(f"   Row {i+1}: Position={row.get('position')}, Round={row.get('round')}, MB={row.get('mb')}, Name={row.get('name')}")
                
            self.preview_label.setText(preview_text)
            
            # Send data to parent
            if self.parent_window:
                self.parent_window.update_fields_from_popup(parsed_data, self.tab_type)
                
            # Ask if user wants to apply
            reply = QMessageBox.question(self, "Apply Data", 
                                       f"Do you want to apply this data to {self.tab_type} fields?",
                                       QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process data: {str(e)}")
            debug_print(f"❌ Error processing data: {e}")
            
    def parse_data(self, raw_data):
        """Parse the raw data into structured format with Round X validation"""
        debug_print(f"🔍 Starting to parse raw data:")
        debug_print(f"Raw data length: {len(raw_data)} characters")
        debug_print(f"Raw data preview: {raw_data[:200]}...")
        
        rows = raw_data.split('\n')
        parsed_data = []
        
        # Filter out empty rows and clean data
        clean_rows = []
        for row in rows:
            row_stripped = row.strip()
            if row_stripped:
                clean_rows.append(row_stripped)
        
        debug_print(f"🔍 Found {len(clean_rows)} non-empty rows")
        for i, row in enumerate(clean_rows[:10]):  # Show first 10
            debug_print(f"   Row {i+1}: '{row}'")
        
        if not clean_rows:
            debug_print("❌ No data rows found after filtering")
            return parsed_data
        
        # Format detection
        columnar_format = False
        line_by_line_format = False
        
        # Check for columnar format - look for rows that have "Round X" and a number on the same line
        for row in clean_rows[:5]:  # Check first 5 rows
            if '\t' in row or ('round' in row.lower() and len(row.split()) >= 2):
                # Check if it looks like "Round 1 60050" or "Round 1\t60050"
                parts = row.split('\t') if '\t' in row else row.split()
                if len(parts) >= 2:
                    # For 3+ parts like "Round 1 60050", check if first two parts form "Round X"
                    if len(parts) >= 3:
                        round_part = f"{parts[0]} {parts[1]}"  # "Round 1"
                        number_part = parts[2]  # The member ID
                    else:
                        round_part = parts[0]  # "Round1" or similar
                        number_part = parts[1]  # The member ID
                    
                    if (re.search(r'round\s*\d+', round_part.lower()) and 
                        number_part.isdigit() and len(number_part) > 2):  # Member IDs are usually longer
                        columnar_format = True
                        break
        
        # Check for line-by-line format - alternating "Round X" and number lines
        if not columnar_format and len(clean_rows) >= 2:
            consecutive_round_lines = 0
            
            for i in range(0, min(len(clean_rows), 10), 2):  # Check pairs
                if i + 1 < len(clean_rows):
                    line1 = clean_rows[i].strip()
                    line2 = clean_rows[i + 1].strip()
                    
                    # Check if line1 is "Round X" and line2 is a number
                    if (re.search(r'^round\s+\d+$', line1.lower()) and 
                        line2.isdigit() and len(line2) > 2):
                        consecutive_round_lines += 1
                    else:
                        break
            
            # If we found at least 2 consecutive pairs, it's likely line-by-line format
            if consecutive_round_lines >= 2:
                line_by_line_format = True
        
        debug_print(f"🔍 Detected format: {'Columnar' if columnar_format else 'Line-by-line' if line_by_line_format else 'Auto-detect'}")
        
        round_number = None
        
        if line_by_line_format:
            debug_print("📋 Using LINE-BY-LINE parsing strategy")
            # Parse line-by-line format: alternating "Round X" and member number lines
            i = 0
            while i < len(clean_rows) - 1:
                row1 = clean_rows[i].strip()
                row2 = clean_rows[i + 1].strip()
                
                debug_print(f"🔍 Processing line-by-line pair {i//2 + 1}: '{row1}' + '{row2}'")
                
                # Check if first row is "Round X" format
                round_match = re.search(r'round\s+(\d+)', row1.lower())
                if round_match and row2.isdigit():
                    current_round = int(round_match.group(1))
                    member_value = row2
                    
                    debug_print(f"   Round info: '{row1}', Member value: '{member_value}'")
                    debug_print(f"   Extracted round number: {current_round}")
                    
                    # Validate consistent round number
                    if round_number is None:
                        round_number = current_round
                        debug_print(f"   Set round number to: {round_number}")
                    elif round_number != current_round:
                        debug_print(f"❌ Inconsistent round number in pair {i//2 + 1}: found 'Round {current_round}', expected 'Round {round_number}'")
                        i += 2
                        continue
                    
                    # Position is based on order in the parsed data
                    position = len(parsed_data) + 1
                    
                    data_row = {
                        'round': round_number,
                        'position': position,
                        'name': member_value,
                        'rank': f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}",
                        'member_id': member_value
                    }
                    parsed_data.append(data_row)
                    debug_print(f"   ✅ Added data row: Position={position}, Round={round_number}, Member={member_value}")
                    
                    i += 2  # Move to next pair
                else:
                    debug_print(f"❌ Invalid pair in lines {i+1}-{i+2}: '{row1}' + '{row2}' (expected 'Round X' + number)")
                    i += 1  # Try next line
                    
        elif columnar_format:
            debug_print("📋 Using COLUMNAR parsing strategy")
            # Parse columnar format: "Round 1\t60050" or "Round 1 60050"
            for row_index, row in enumerate(clean_rows):
                debug_print(f"🔍 Processing columnar row {row_index + 1}: '{row}'")
                
                # Try different separators: tab, multiple spaces, single space, comma
                columns = []
                if '\t' in row:
                    columns = [col.strip() for col in row.split('\t') if col.strip()]
                    debug_print(f"   Using tab separation: {columns}")
                elif '  ' in row:  # Multiple spaces
                    columns = [col.strip() for col in row.split() if col.strip()]
                    debug_print(f"   Using space separation: {columns}")
                elif ',' in row:
                    columns = [col.strip() for col in row.split(',') if col.strip()]
                    debug_print(f"   Using comma separation: {columns}")
                else:
                    columns = [col.strip() for col in row.split() if col.strip()]
                    debug_print(f"   Using default split: {columns}")
                    
                if len(columns) >= 2:
                    # Handle both "Round 1 60050" (3 parts) and "Round1 60050" (2 parts)
                    if len(columns) >= 3 and columns[0].lower() == 'round' and columns[1].isdigit():
                        # Format: "Round 1 60050"
                        round_info = f"{columns[0]} {columns[1]}"
                        member_value = columns[2]
                    elif len(columns) >= 2:
                        # Format: "Round1 60050" or any other 2-column format
                        round_info = columns[0]
                        member_value = columns[1]
                    else:
                        debug_print(f"❌ Unexpected column format in row {row_index + 1}")
                        continue
                    
                    debug_print(f"   Round info: '{round_info}', Member value: '{member_value}'")
                    
                    # Extract and validate round number
                    round_match = re.search(r'round\s*(\d+)', round_info.lower())
                    if not round_match:
                        debug_print(f"❌ Invalid round format in row {row_index + 1}: '{round_info}' (expected 'Round X')")
                        continue
                    
                    current_round = int(round_match.group(1))
                    debug_print(f"   Extracted round number: {current_round}")
                    
                    # Validate consistent round number
                    if round_number is None:
                        round_number = current_round
                        debug_print(f"   Set round number to: {round_number}")
                    elif round_number != current_round:
                        debug_print(f"❌ Inconsistent round number in row {row_index + 1}: found 'Round {current_round}', expected 'Round {round_number}'")
                        continue
                    
                    # Position is based on order in the parsed data
                    position = len(parsed_data) + 1
                    
                    data_row = {
                        'round': round_number,
                        'position': position,
                        'name': member_value,
                        'rank': f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}",
                        'member_id': member_value
                    }
                    parsed_data.append(data_row)
                    debug_print(f"   ✅ Added data row: Position={position}, Round={round_number}, Member={member_value}")
                else:
                    debug_print(f"❌ Insufficient columns in row {row_index + 1}: {len(columns)} columns found, need at least 2")
        else:
            debug_print("📋 Using AUTO-DETECT parsing strategy")
            # Auto-detect and try both formats
            # Try columnar format first
            for row_index, row in enumerate(clean_rows):
                debug_print(f"🔍 Processing auto-detect row {row_index + 1}: '{row}'")
                
                # Try different separators: tab, multiple spaces, single space, comma
                columns = []
                if '\t' in row:
                    columns = [col.strip() for col in row.split('\t') if col.strip()]
                    debug_print(f"   Using tab separation: {columns}")
                elif '  ' in row:  # Multiple spaces
                    columns = [col.strip() for col in row.split() if col.strip()]
                    debug_print(f"   Using space separation: {columns}")
                elif ',' in row:
                    columns = [col.strip() for col in row.split(',') if col.strip()]
                    debug_print(f"   Using comma separation: {columns}")
                else:
                    columns = [col.strip() for col in row.split() if col.strip()]
                    debug_print(f"   Using default split: {columns}")
                    
                if len(columns) >= 2:
                    # Handle both "Round 1 60050" (3 parts) and "Round1 60050" (2 parts)
                    if len(columns) >= 3 and columns[0].lower() == 'round' and columns[1].isdigit():
                        # Format: "Round 1 60050"
                        round_info = f"{columns[0]} {columns[1]}"
                        member_value = columns[2]
                    elif len(columns) >= 2:
                        # Format: "Round1 60050" or any other 2-column format
                        round_info = columns[0]
                        member_value = columns[1]
                    else:
                        debug_print(f"❌ Unexpected column format in row {row_index + 1}")
                        continue
                    
                    debug_print(f"   Round info: '{round_info}', Member value: '{member_value}'")
                    
                    # Extract and validate round number
                    round_match = re.search(r'round\s*(\d+)', round_info.lower())
                    if not round_match:
                        debug_print(f"❌ Invalid round format in row {row_index + 1}: '{round_info}' (expected 'Round X'), skipping")
                        continue
                    
                    current_round = int(round_match.group(1))
                    debug_print(f"   Extracted round number: {current_round}")
                    
                    # Validate consistent round number
                    if round_number is None:
                        round_number = current_round
                        debug_print(f"   Set round number to: {round_number}")
                    elif round_number != current_round:
                        debug_print(f"❌ Inconsistent round number in row {row_index + 1}: found 'Round {current_round}', expected 'Round {round_number}'")
                        continue
                    
                    # Position is based on order in the parsed data
                    position = len(parsed_data) + 1
                    
                    data_row = {
                        'round': round_number,
                        'position': position,
                        'name': member_value,
                        'rank': f"{position}{'st' if position == 1 else 'nd' if position == 2 else 'rd' if position == 3 else 'th'}",
                        'member_id': member_value
                    }
                    parsed_data.append(data_row)
                    debug_print(f"   ✅ Added data row: Position={position}, Round={round_number}, Member={member_value}")
                else:
                    debug_print(f"❌ Insufficient columns in row {row_index + 1}: {len(columns)} columns found, need at least 2")
                    
        debug_print(f"✅ Successfully parsed {len(parsed_data)} rows for Round {round_number}")
        return parsed_data

class MQTTRemoteHandler(QObject):
    """Handle MQTT communication for remote control"""
    
    # Signals
    status_received = pyqtSignal(dict)
    heartbeat_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    debug_message = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        debug_print("🔧 Initializing MQTT Remote Handler...")
        self.client = mqtt.Client()
        self.connected = False
        
        # Setup MQTT client
        self.setup_mqtt()
        debug_print("✅ MQTT Remote Handler initialized")
        
    def setup_mqtt(self):
        """Setup MQTT client"""
        debug_print("🔧 Setting up MQTT callbacks...")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Set authentication if provided
        if MQTT_USERNAME and MQTT_PASSWORD:
            debug_print(f"🔐 Setting MQTT authentication for user: {MQTT_USERNAME}")
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        else:
            debug_print("🔓 No MQTT authentication required")
            
    def connect(self):
        """Connect to MQTT broker"""
        try:
            debug_print(f"🔌 Attempting to connect to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
            debug_print(f"📡 Session ID: {UNIQUE_ID}")
            debug_print(f"📋 Topics to subscribe:")
            debug_print(f"   - Status: {MQTT_TOPICS['status']}")
            debug_print(f"   - Heartbeat: {MQTT_TOPICS['heartbeat']}")
            
            self.client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.client.loop_start()
            return True
        except Exception as e:
            debug_print(f"❌ Failed to connect to MQTT broker: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from MQTT broker"""
        debug_print("🔌 Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            debug_print("✅ Connected to MQTT broker successfully")
            self.connected = True
            self.connection_changed.emit(True)
            
            # Subscribe to status and heartbeat topics
            debug_print("📡 Subscribing to topics...")
            client.subscribe(MQTT_TOPICS['status'], MQTT_QOS)
            client.subscribe(MQTT_TOPICS['heartbeat'], MQTT_QOS)
            debug_print(f"📬 Subscribed to: {MQTT_TOPICS['status']}")
            debug_print(f"📬 Subscribed to: {MQTT_TOPICS['heartbeat']}")
            
        else:
            debug_print(f"❌ Failed to connect to MQTT broker, return code {rc}")
            self.connected = False
            self.connection_changed.emit(False)
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        debug_print("🔌 Disconnected from MQTT broker")
        self.connected = False
        self.connection_changed.emit(False)
        
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            debug_print(f"📨 Message received on {topic}: {payload}")
            
            # Emit debug message to be displayed in the UI
            debug_msg = f"📨 Received on {topic}: {json.dumps(payload, indent=2, ensure_ascii=False)}"
            self.debug_message.emit(debug_msg)
            
            if topic == MQTT_TOPICS['status']:
                self.status_received.emit(payload)
            elif topic == MQTT_TOPICS['heartbeat']:
                self.heartbeat_received.emit(payload)
                
        except Exception as e:
            debug_print(f"❌ Error processing MQTT message: {e}")
            # Emit error message to be displayed in the UI
            self.debug_message.emit(f"❌ Error: {e}")
            
    def send_command(self, command_type, data=None, target_client=None):
        """Send command via MQTT with optional targeting"""
        if not self.connected:
            debug_print("❌ Cannot send command: Not connected to MQTT broker")
            return False
        
        # Determine target and topic
        if target_client and target_client != "all":
            # Use targeted topic for specific client
            base_topic = MQTT_TOPICS.get(command_type, MQTT_TOPICS['commands'])
            topic = f"{base_topic}/{target_client}"
            debug_print(f"🎯 Sending TARGETED command to client: {target_client}")
        else:
            # Use broadcast topic for all clients
            topic = MQTT_TOPICS.get(command_type, MQTT_TOPICS['commands'])
            debug_print(f"📢 Sending BROADCAST command to all clients")
        
        # Ensure data is a dict and add target field
        if data is None:
            data = {}
        if not isinstance(data, dict):
            data = {'message': data}
        
        # Add target field to data payload
        data['target'] = target_client if target_client else "all"
        
        message = json.dumps(data, ensure_ascii=False)
        
        try:
            debug_print(f"📤 SENDING COMMAND TO CLIENT")
            debug_print(f"   Command Type: {command_type}")
            debug_print(f"   Target: {data.get('target', 'all')}")
            debug_print(f"   Topic: {topic}")
            debug_print(f"   Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            result = self.client.publish(topic, message, MQTT_QOS)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                debug_print(f"✅ Command sent successfully!")
                return True
            else:
                debug_print(f"❌ Failed to send command, RC: {result.rc}")
                return False
        except Exception as e:
            debug_print(f"❌ Error sending command: {e}")
            return False

class ScoShowRemoteControlSuper(QMainWindow):
    """Enhanced ScoShow Remote Control with Data Paste functionality"""
    
    def __init__(self):
        super().__init__()
        debug_print("🚀 Initializing ScoShow Remote Control Super...")
        
        # Initialize MQTT handler
        self.mqtt_handler = None
        self.last_heartbeat = None
        self.client_online = False
        
        # Data storage
        self.current_round = ""
        self.rank_data = {}
        self.final_data = {}
        
        # Initialize variables for compatibility with enhanced version
        self.saved_settings = {}
        self.config_file = "remote_config.json"
        self.current_background = "00"
        self.current_display_mode = "windowed"
        self.current_content_type = None
        self.available_monitors = []
        
        # State management for each monitor
        self.monitor_states = {
            0: {"background": "00", "fullscreen": False, "display_open": False},
            1: {"background": "00", "fullscreen": False, "display_open": False},
            2: {"background": "00", "fullscreen": False, "display_open": False},
            3: {"background": "00", "fullscreen": False, "display_open": False}
        }
        self.current_monitor_index = 0
        
        # Setup default positions (from enhanced version)
        self.default_rank_positions = {
            '1st': "2980,125", '2nd': "2980,220", '3rd': "2980,318", 
            '4th': "2980,402", '5th': "2980,495", '6th': "2980,578", 
            '7th': "2980,672", '8th': "2980,762", '9th': "2980,850", 
            '10th': "2980,939"
        }
        self.default_final_positions = {
            'winner': "3000,80", 'second': "3000,280", 'third': "3000,480", 
            'fourth': "3000,680", 'fifth': "3000,880"
        }
        self.default_round_position = "1286,935"
        
        # Detect monitors
        self.detect_monitors()
        
        # Setup UI
        self.init_ui()
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Setup status check timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_client_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        
        debug_print("✅ ScoShow Remote Control Super initialized")
        
    def detect_monitors(self):
        """Detect available monitors"""
        self.available_monitors = ["Monitor 1 (Primary)", "Monitor 2", "Monitor 3", "Monitor 4"]
        debug_print("🖥️ Using default monitor list")
        
    def update_monitors_from_client(self, monitor_info):
        """Update monitor information received from client"""
        try:
            if monitor_info and isinstance(monitor_info, list):
                debug_print(f"🖥️ Updating monitors from client: {monitor_info}")
                
                # Store the monitor info
                self.available_monitors = monitor_info
                
                # Update both combo boxes
                if hasattr(self, 'monitor_combo'):
                    current_index = self.monitor_combo.currentIndex()
                    self.monitor_combo.clear()
                    for monitor_name in monitor_info:
                        self.monitor_combo.addItem(monitor_name)
                    
                    # Restore selection if valid
                    if current_index < len(monitor_info):
                        self.monitor_combo.setCurrentIndex(current_index)
                    
                if hasattr(self, 'monitor_settings_combo'):
                    current_index = self.monitor_settings_combo.currentIndex()
                    self.monitor_settings_combo.clear()
                    for monitor_name in monitor_info:
                        self.monitor_settings_combo.addItem(monitor_name)
                    
                    # Restore selection if valid
                    if current_index < len(monitor_info):
                        self.monitor_settings_combo.setCurrentIndex(current_index)
                
                # Update spin box range
                if hasattr(self, 'monitor_spin'):
                    self.monitor_spin.setRange(0, len(monitor_info) - 1)
                
                debug_print(f"✅ Monitor list updated with {len(monitor_info)} monitors")
                
        except Exception as e:
            debug_print(f"❌ Error updating monitors from client: {e}")
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("🎪 ScoShow Remote Control - Super Enhanced")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Connection status
        self.create_connection_status(main_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_display_tab()
        self.create_ranking_tab()
        self.create_final_tab()
        self.create_settings_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
    def create_connection_status(self, main_layout):
        """Create connection status display"""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        # MQTT Status
        self.mqtt_status = QLabel("🔴 MQTT: Disconnected")
        self.mqtt_status.setStyleSheet("font-weight: bold; color: red;")
        status_layout.addWidget(self.mqtt_status)
        
        # Client Status
        self.client_status = QLabel("⚫ Client: Unknown")
        self.client_status.setStyleSheet("font-weight: bold; color: gray;")
        status_layout.addWidget(self.client_status)
        
        # Last update
        self.last_update = QLabel("📅 Last: Never")
        status_layout.addWidget(self.last_update)
        
        status_layout.addStretch()
        
        # Target Client Selection
        status_layout.addWidget(QLabel("🎯 Target:"))
        self.target_client_combo = QComboBox()
        self.target_client_combo.addItem("📢 All Clients (Broadcast)")
        self.target_client_combo.addItem("🖥️ This Computer Only")
        self.target_client_combo.setCurrentIndex(1)  # Default to "This Computer Only"
        self.target_client_combo.setToolTip("Select which client(s) to send commands to")
        status_layout.addWidget(self.target_client_combo)
        
        # Reconnect button
        reconnect_btn = QPushButton("🔄 Reconnect")
        reconnect_btn.clicked.connect(self.reconnect_mqtt)
        status_layout.addWidget(reconnect_btn)
        
        main_layout.addWidget(status_frame)
        
    def get_target_client(self):
        """Get the currently selected target client"""
        if hasattr(self, 'target_client_combo'):
            selected_index = self.target_client_combo.currentIndex()
            if selected_index == 0:  # "All Clients (Broadcast)"
                return "all"
            elif selected_index == 1:  # "This Computer Only"
                return CLIENT_ID  # Use the client ID from mqtt_config
            else:
                # Custom client selection (if we add more options later)
                return "all"
        return CLIENT_ID  # Default to this computer only
    
    def debug_monitor_states(self):
        """Debug function to show current monitor states"""
        debug_print("🔍 CURRENT MONITOR STATES:")
        for monitor_idx, state in self.monitor_states.items():
            debug_print(f"   Monitor {monitor_idx}: {state}")
        debug_print(f"🎯 Current monitor index: {self.current_monitor_index}")
        debug_print(f"📺 Current display mode: {self.current_display_mode}")
        debug_print(f"🖼️ Current background: {self.current_background}")
        
    def create_display_tab(self):
        """Create display control tab"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "🖥️ Display")
        
        layout = QVBoxLayout(tab)
        
        # Monitor and Background Setup
        setup_group = QGroupBox("🖥️ Setup")
        setup_layout = QGridLayout(setup_group)
        
        # Monitor selection
        setup_layout.addWidget(QLabel("Monitor:"), 0, 0)
        self.monitor_combo = QComboBox()
        for monitor_name in self.available_monitors:
            self.monitor_combo.addItem(monitor_name)
        setup_layout.addWidget(self.monitor_combo, 0, 1)
        
        # Keep spin box for compatibility
        self.monitor_spin = QSpinBox()
        self.monitor_spin.setRange(0, len(self.available_monitors)-1)
        self.monitor_spin.setValue(0)
        self.monitor_spin.hide()
        
        # Sync combo with spin box
        self.monitor_combo.currentIndexChanged.connect(self.monitor_spin.setValue)
        
        # Background folder
        setup_layout.addWidget(QLabel("Background Folder:"), 1, 0)
        self.bg_folder_edit = QLineEdit()
        setup_layout.addWidget(self.bg_folder_edit, 1, 1)
        
        bg_browse_btn = QPushButton("📁 Browse")
        bg_browse_btn.clicked.connect(self.browse_background_folder)
        setup_layout.addWidget(bg_browse_btn, 1, 2)
        
        # Background file selection
        setup_layout.addWidget(QLabel("Background File:"), 2, 0)
        self.bg_file_combo = QComboBox()
        self.bg_file_combo.addItems(["00.jpg (Wait)", "01.png (Ranking)", "02.png (Final)"])
        setup_layout.addWidget(self.bg_file_combo, 2, 1)
        
        load_bg_btn = QPushButton("🔄 Load List")
        load_bg_btn.clicked.connect(self.load_background_list)
        setup_layout.addWidget(load_bg_btn, 2, 2)
        
        layout.addWidget(setup_group)
        
        # Display Controls
        control_group = QGroupBox("🎮 Display Controls")
        control_layout = QGridLayout(control_group)
        
        open_btn = QPushButton("🚀 Open Display")
        open_btn.clicked.connect(self.open_display)
        control_layout.addWidget(open_btn, 0, 0)
        
        close_btn = QPushButton("❌ Close Display")
        close_btn.clicked.connect(self.close_display)
        control_layout.addWidget(close_btn, 0, 1)
        
        fullscreen_btn = QPushButton("🖥️ Toggle Fullscreen")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        control_layout.addWidget(fullscreen_btn, 1, 0)
        
        switch_btn = QPushButton("🔄 Switch Monitor")
        switch_btn.clicked.connect(self.switch_monitor)
        control_layout.addWidget(switch_btn, 1, 1)
        
        layout.addWidget(control_group)
        
        # Background Selection
        bg_group = QGroupBox("🖼️ Background Selection")
        bg_layout = QVBoxLayout(bg_group)
        
        # Quick selection buttons
        quick_layout = QHBoxLayout()
        
        bg00_btn = QPushButton("⏸️ Wait (00)")
        bg00_btn.clicked.connect(lambda: self.show_background("00"))
        quick_layout.addWidget(bg00_btn)
        
        bg01_btn = QPushButton("📊 Ranking (01)")
        bg01_btn.clicked.connect(lambda: self.show_background("01"))
        quick_layout.addWidget(bg01_btn)
        
        bg02_btn = QPushButton("🏆 Final (02)")
        bg02_btn.clicked.connect(lambda: self.show_background("02"))
        quick_layout.addWidget(bg02_btn)
        
        bg_layout.addLayout(quick_layout)
        
        # Custom selection
        custom_layout = QHBoxLayout()
        
        show_selected_btn = QPushButton("🖼️ Show Selected")
        show_selected_btn.clicked.connect(self.show_selected_background)
        custom_layout.addWidget(show_selected_btn)
        
        hide_bg_btn = QPushButton("🙈 Hide Background")
        hide_bg_btn.clicked.connect(self.hide_background)
        custom_layout.addWidget(hide_bg_btn)
        
        bg_layout.addLayout(custom_layout)
        
        layout.addWidget(bg_group)
        
    def create_ranking_tab(self):
        """Create ranking input tab with enhanced data paste functionality"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "🏆 Ranking")
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)
        
        layout = QVBoxLayout(scroll_widget)
        
        # Font Settings
        font_group = QGroupBox("🔤 Font Settings")
        font_layout = QHBoxLayout(font_group)
        
        font_layout.addWidget(QLabel("Font:"))
        self.rank_font_combo = QComboBox()
        self.rank_font_combo.addItems(["arial.ttf", "times.ttf", "calibri.ttf"])
        font_layout.addWidget(self.rank_font_combo)
        
        font_layout.addWidget(QLabel("Size:"))
        self.rank_font_size = QSpinBox()
        self.rank_font_size.setRange(10, 200)
        self.rank_font_size.setValue(80)
        font_layout.addWidget(self.rank_font_size)
        
        font_layout.addWidget(QLabel("Color:"))
        self.rank_font_color = QComboBox()
        self.rank_font_color.addItems(["white", "black", "red", "blue", "yellow"])
        font_layout.addWidget(self.rank_font_color)
        
        layout.addWidget(font_group)
        
        # Round information
        round_group = QGroupBox("Round Information")
        round_layout = QHBoxLayout(round_group)
        
        round_layout.addWidget(QLabel("Round:"))
        self.round_edit = QLineEdit()
        self.round_edit.setPlaceholderText("e.g., Round 1")
        round_layout.addWidget(self.round_edit)
        
        round_layout.addWidget(QLabel("Position:"))
        self.round_pos_edit = QLineEdit(self.default_round_position)
        round_layout.addWidget(self.round_pos_edit)
        
        layout.addWidget(round_group)
        
        # Data input controls
        input_group = QGroupBox("Data Input")
        input_layout = QVBoxLayout(input_group)
        
        # Paste data button
        paste_btn = QPushButton("📋 Paste Ranking Data")
        paste_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        paste_btn.clicked.connect(lambda: self.open_data_popup("rank"))
        input_layout.addWidget(paste_btn)
        
        layout.addWidget(input_group)
        
        # Ranking fields
        ranking_group = QGroupBox("Ranking Data")
        ranking_layout = QGridLayout(ranking_group)
        
        self.rank_edits = {}
        self.rank_pos_edits = {}
        positions = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]
        
        for i, pos in enumerate(positions):
            row = i // 2
            col = (i % 2) * 3
            
            ranking_layout.addWidget(QLabel(f"{pos}:"), row, col)
            
            edit = QLineEdit()
            edit.setPlaceholderText(f"Enter {pos} place name")
            self.rank_edits[pos] = edit
            ranking_layout.addWidget(edit, row, col + 1)
            
            pos_edit = QLineEdit(self.default_rank_positions.get(pos, "2980,125"))
            pos_edit.setMaximumWidth(80)
            self.rank_pos_edits[pos] = pos_edit
            ranking_layout.addWidget(pos_edit, row, col + 2)
            
        layout.addWidget(ranking_group)
        
        # Apply button
        apply_btn = QPushButton("✅ Apply Ranking")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self.apply_ranking)
        layout.addWidget(apply_btn)
        
        # Set the scroll area as the tab's main widget
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        
    def create_final_tab(self):
        """Create final results tab with enhanced data paste functionality"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "🎖️ Final")
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll.setWidget(scroll_widget)
        
        layout = QVBoxLayout(scroll_widget)
        
        # Font Settings
        font_group = QGroupBox("🔤 Font Settings")
        font_layout = QHBoxLayout(font_group)
        
        font_layout.addWidget(QLabel("Font Size:"))
        self.final_font_size = QSpinBox()
        self.final_font_size.setRange(10, 200)
        self.final_font_size.setValue(120)
        font_layout.addWidget(self.final_font_size)
        
        font_layout.addWidget(QLabel("(Uses same font & color as ranking)"))
        
        layout.addWidget(font_group)
        
        # Data input controls
        input_group = QGroupBox("Data Input")
        input_layout = QVBoxLayout(input_group)
        
        # Paste data button
        paste_btn = QPushButton("📋 Paste Final Results Data")
        paste_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        paste_btn.clicked.connect(lambda: self.open_data_popup("final"))
        input_layout.addWidget(paste_btn)
        
        layout.addWidget(input_group)
        
        # Final results fields
        final_group = QGroupBox("Final Results")
        final_layout = QGridLayout(final_group)
        
        self.final_edits = {}
        self.final_pos_edits = {}
        final_labels = {
            'winner': '🥇 1st Place:', 'second': '🥈 2nd Place:', 'third': '🥉 3rd Place:',
            'fourth': '🏅 4th Place:', 'fifth': '🎖️ 5th Place:'
        }
        
        for i, (key, label) in enumerate(final_labels.items()):
            final_layout.addWidget(QLabel(label), i, 0)
            
            edit = QLineEdit()
            edit.setPlaceholderText(f"Enter {label.split()[1]} name")
            self.final_edits[key] = edit
            final_layout.addWidget(edit, i, 1)
            
            pos_edit = QLineEdit(self.default_final_positions.get(key, "3000,80"))
            pos_edit.setMaximumWidth(80)
            self.final_pos_edits[key] = pos_edit
            final_layout.addWidget(pos_edit, i, 2)
            
        layout.addWidget(final_group)
        
        # Apply button
        apply_btn = QPushButton("🏆 Apply Final Results")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        apply_btn.clicked.connect(self.apply_final_results)
        layout.addWidget(apply_btn)
        
        # Set the scroll area as the tab's main widget
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        
    def create_settings_tab(self):
        """Create settings and debug tab"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "⚙️ Settings")
        
        layout = QVBoxLayout(tab)
        
        # Monitor settings
        monitor_group = QGroupBox("Monitor Settings")
        monitor_layout = QGridLayout(monitor_group)
        
        self.monitor_settings_combo = QComboBox()
        for monitor_name in self.available_monitors:
            self.monitor_settings_combo.addItem(monitor_name)
                
        monitor_layout.addWidget(QLabel("Target Monitor:"), 0, 0)
        monitor_layout.addWidget(self.monitor_settings_combo, 0, 1)
        
        layout.addWidget(monitor_group)
        
        # Debug area
        debug_group = QGroupBox("Debug Information")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(200)
        self.debug_text.setReadOnly(True)
        debug_layout.addWidget(self.debug_text)
        
        # Debug buttons
        debug_button_layout = QHBoxLayout()
        
        info_btn = QPushButton("📋 Request Client Info")
        info_btn.clicked.connect(self.request_client_info)
        debug_button_layout.addWidget(info_btn)
        
        test_btn = QPushButton("🔍 Test Connection")
        test_btn.clicked.connect(self.test_connection)
        debug_button_layout.addWidget(test_btn)
        
        clear_btn = QPushButton("🗑️ Clear Debug")
        clear_btn.clicked.connect(lambda: self.debug_text.clear())
        debug_button_layout.addWidget(clear_btn)
        
        debug_layout.addLayout(debug_button_layout)
        layout.addWidget(debug_group)
        
        layout.addStretch()
        
    def open_data_popup(self, tab_type):
        """Open the data input popup"""
        debug_print(f"🎪 Opening data popup for {tab_type}")
        popup = DataInputPopup(self, tab_type)
        result = popup.exec_()
        
        if result == QDialog.Accepted:
            debug_print(f"✅ Data popup accepted for {tab_type}")
        else:
            debug_print(f"❌ Data popup cancelled for {tab_type}")
            
    def update_fields_from_popup(self, parsed_data, tab_type):
        """Update fields based on data from popup"""
        debug_print(f"📊 Updating {tab_type} fields with {len(parsed_data)} rows")
        
        if not parsed_data:
            debug_print("❌ No parsed data to update fields")
            return
            
        # Update round information
        if parsed_data[0].get('round'):
            self.round_edit.setText(str(parsed_data[0]['round']))
            
        if tab_type == "rank":
            # Update ranking fields with new data structure
            positions = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]
            for i, row in enumerate(parsed_data[:10]):  # Only take first 10 for ranking
                if i < len(positions):
                    pos = positions[i]
                    if pos in self.rank_edits:
                        name = row.get('name', '')  # This is the rank value from column 2
                        self.rank_edits[pos].setText(name)
                        debug_print(f"✅ Updated {pos}: {name}")
                        
        elif tab_type == "final":
            # Update final results fields
            final_keys = ['winner', 'second', 'third', 'fourth', 'fifth']
            for i, row in enumerate(parsed_data[:5]):  # Only take first 5 for final
                if i < len(final_keys):
                    key = final_keys[i]
                    if key in self.final_edits:
                        name = row.get('name', '')
                        self.final_edits[key].setText(name)
                        debug_print(f"✅ Updated {key}: {name}")
                        
        debug_print(f"✅ Fields updated successfully for {tab_type}")
        
    def setup_mqtt(self):
        """Setup MQTT handler"""
        debug_print("🔧 Setting up MQTT handler...")
        self.mqtt_handler = MQTTRemoteHandler()
        
        # Connect signals
        self.mqtt_handler.connection_changed.connect(self.handle_connection_changed)
        self.mqtt_handler.status_received.connect(self.handle_status_received)
        self.mqtt_handler.heartbeat_received.connect(self.handle_heartbeat_received)
        self.mqtt_handler.debug_message.connect(self.handle_debug_message)
        
        # Connect to broker
        if self.mqtt_handler.connect():
            debug_print("✅ MQTT connection initiated")
        else:
            debug_print("❌ Failed to initiate MQTT connection")
            
    def handle_debug_message(self, message):
        """Handle debug message from MQTT handler"""
        self.debug_text.append(message)
            
    def handle_connection_changed(self, connected):
        """Handle MQTT connection status change"""
        if connected:
            self.mqtt_status.setText("🟢 MQTT: Connected")
            self.mqtt_status.setStyleSheet("font-weight: bold; color: green;")
            debug_print("✅ MQTT connection established")
        else:
            self.mqtt_status.setText("🔴 MQTT: Disconnected")
            self.mqtt_status.setStyleSheet("font-weight: bold; color: red;")
            debug_print("❌ MQTT connection lost")
            
    def handle_status_received(self, data):
        """Handle status message from client"""
        debug_print(f"📊 Status received: {data}")
        self.last_update.setText(f"📅 Last: {datetime.now().strftime('%H:%M:%S')}")
        
        status = data.get('status', 'unknown')
        message = data.get('message', '')
        timestamp = data.get('timestamp', time.time())
        
        debug_print("🎯 CLIENT STATUS UPDATE RECEIVED:")
        debug_print(f"   Status: {status}")
        debug_print(f"   Message: {message}")
        debug_print(f"   Timestamp: {timestamp}")
        debug_print(f"   Time: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
        
        # Add status info to debug text
        status_msg = f"🎯 STATUS: {status} - {message} ({time.strftime('%H:%M:%S', time.localtime(timestamp))})"
        self.debug_text.append(status_msg)
        
        # Check for additional data in status
        if 'display_info' in data:
            debug_print(f"   Display Info: {data['display_info']}")
            self.debug_text.append(f"   Display Info: {data['display_info']}")
        if 'monitor_info' in data:
            debug_print(f"   Monitor Info: {data['monitor_info']}")
            self.debug_text.append(f"   Monitor Info: {data['monitor_info']}")
            # Update monitor info when received
            self.update_monitors_from_client(data['monitor_info'])
        if 'background_folder' in data:
            debug_print(f"   Background Folder: {data['background_folder']}")
            self.debug_text.append(f"   Background Folder: {data['background_folder']}")
        if 'error_details' in data:
            debug_print(f"   Error: {data['error_details']}")
            self.debug_text.append(f"   ❌ Error: {data['error_details']}")
        if 'command_result' in data:
            debug_print(f"   Command Result: {data['command_result']}")
        
        # Update client status
        if status == 'online':
            debug_print("✅ Client is ONLINE and ready!")
            self.client_status.setText("🟢 Client: Online")
            self.client_status.setStyleSheet("font-weight: bold; color: green;")
        elif status == 'error':
            debug_print("❌ Client reported an ERROR!")
            self.client_status.setText("🔴 Client: Error")
            self.client_status.setStyleSheet("font-weight: bold; color: red;")
        else:
            debug_print(f"ℹ️ Client status: {status}")
            self.client_status.setText(f"🔵 Client: {status.title()}")
            self.client_status.setStyleSheet("font-weight: bold; color: blue;")
            
        # Add detailed status to debug text
        status_text = f"[{datetime.now().strftime('%H:%M:%S')}] Status: {status}"
        if message:
            status_text += f" - {message}"
        
        # Add extra details for client info responses
        if 'display_info' in data:
            status_text += f"\nDisplay Info: {data['display_info']}"
        if 'monitor_info' in data:
            status_text += f"\nMonitor Info: {data['monitor_info']}"
        if 'background_folder' in data:
            status_text += f"\nBackground Folder: {data['background_folder']}"
        if 'error_details' in data:
            status_text += f"\nError: {data['error_details']}"
        if 'command_result' in data:
            status_text += f"\nCommand Result: {data['command_result']}"
            
        status_text += "\n"
        if hasattr(self, 'debug_text'):
            self.debug_text.append(status_text)
        
    def handle_heartbeat_received(self, data):
        """Handle heartbeat from client"""
        self.last_heartbeat = datetime.now()
        self.client_online = True
        self.client_status.setText("🟢 Client: Online")
        self.client_status.setStyleSheet("font-weight: bold; color: green;")
        
        timestamp = data.get('timestamp', time.time())
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        
        debug_print("💓 CLIENT HEARTBEAT RECEIVED:")
        debug_print(f"   Timestamp: {timestamp}")
        debug_print(f"   Time: {time_str}")
        
        # Extract and display detailed heartbeat info
        if 'display_status' in data:
            debug_print(f"   Display Status: {data['display_status']}")
        if 'current_background' in data:
            debug_print(f"   Current Background: {data['current_background']}")
        if 'system_info' in data:
            sys_info = data['system_info']
            debug_print(f"   System Info:")
            for key, value in sys_info.items():
                debug_print(f"     - {key}: {value}")
        if 'client_version' in data:
            debug_print(f"   Client Version: {data['client_version']}")
        if 'uptime' in data:
            debug_print(f"   Client Uptime: {data['uptime']} seconds")
        if 'monitor_info' in data:
            debug_print(f"   Monitor Info: {data['monitor_info']}")
            # Update monitors from client heartbeat
            self.update_monitors_from_client(data['monitor_info'])
        
        debug_print("💓 Heartbeat processed successfully")
            
        # Update debug text with detailed heartbeat info
        heartbeat_msg = f"💓 HEARTBEAT ({time_str}): "
        if 'display_status' in data:
            heartbeat_msg += f"Display: {data['display_status']}, "
        if 'current_background' in data:
            heartbeat_msg += f"Background: {data['current_background']}, "
        if 'client_version' in data:
            heartbeat_msg += f"Version: {data['client_version']}"
        
        self.debug_text.append(heartbeat_msg)
        
    def check_client_status(self):
        """Check if client is still online based on heartbeat"""
        if self.last_heartbeat:
            time_diff = (datetime.now() - self.last_heartbeat).total_seconds()
            if time_diff > 30:  # No heartbeat for 30 seconds
                self.client_online = False
                self.client_status.setText("🔴 Client: Offline")
                self.client_status.setStyleSheet("font-weight: bold; color: red;")
                debug_print("⚠️ Client appears to be offline (no heartbeat)")
                
    def browse_background_folder(self):
        """Browse for background folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Background Folder")
        if folder:
            self.bg_folder_edit.setText(folder)
            debug_print(f"📁 Background folder selected: {folder}")
            
            # Send background folder to client
            target_client = self.get_target_client()
            data = {
                'action': 'set_background_folder',
                'background_folder': folder
            }
            
            if self.mqtt_handler.send_command('set_background_folder', data, target_client):
                debug_print(f"📤 Sent background folder to target: {target_client}, folder: {folder}")
            else:
                debug_print(f"❌ Failed to send background folder to client")
                
    def load_background_list(self):
        """Load background files from selected folder"""
        folder = self.bg_folder_edit.text()
        if not folder or not os.path.exists(folder):
            QMessageBox.warning(self, "Warning", "Please select a valid background folder first!")
            return
            
        try:
            self.bg_file_combo.clear()
            
            # Add default options
            self.bg_file_combo.addItem("00.jpg (Wait)")
            self.bg_file_combo.addItem("01.png (Ranking)")
            self.bg_file_combo.addItem("02.png (Final)")
            
            # Scan folder for image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
            files = []
            
            for file in os.listdir(folder):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    files.append(file)
                    
            # Sort files
            files.sort()
            
            # Add custom files if any
            for file in files:
                if not file.startswith(('00.', '01.', '02.')):
                    self.bg_file_combo.addItem(f"{file}")
                    
            debug_print(f"📂 Loaded {len(files)} background files from: {folder}")
            
        except Exception as e:
            debug_print(f"❌ Error loading background list: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load background list:\n{e}")
            
    def open_display(self):
        """Send open display command"""
        target_client = self.get_target_client()
        data = {
            'action': 'open_display',
            'monitor_index': self.monitor_spin.value(),
            'background_folder': self.bg_folder_edit.text()
        }
        
        if self.mqtt_handler.send_command('commands', data, target_client):
            # Update current monitor index and state
            self.current_monitor_index = self.monitor_spin.value()
            self.monitor_states[self.current_monitor_index]["display_open"] = True
            
            debug_print(f"📤 Sent open display command to target: {target_client}")
            debug_print(f"💾 Set monitor {self.current_monitor_index} display_open to True")
            
            if hasattr(self, 'status_log'):
                self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Open display command to {target_client}")
            # Tự động hiển thị WAIT(00) sau khi mở display
            QTimer.singleShot(1000, lambda: self.show_background("00"))
        else:
            debug_print("❌ Failed to send open display command")
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def close_display(self):
        """Send close display command"""
        target_client = self.get_target_client()
        data = {'action': 'close_display'}
        
        if self.mqtt_handler.send_command('commands', data, target_client):
            # Update current monitor state
            self.monitor_states[self.current_monitor_index]["display_open"] = False
            self.monitor_states[self.current_monitor_index]["fullscreen"] = False
            self.current_display_mode = "windowed"
            
            debug_print(f"📤 Sent close display command to target: {target_client}")
            debug_print(f"💾 Set monitor {self.current_monitor_index} display_open to False")
            
            if hasattr(self, 'status_log'):
                self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Close display command to {target_client}")
        else:
            debug_print("❌ Failed to send close display command")
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def toggle_fullscreen(self):
        """Send toggle fullscreen command"""
        target_client = self.get_target_client()
        data = {'action': 'toggle_fullscreen'}
        
        if self.mqtt_handler.send_command('commands', data, target_client):
            # Chuyển đổi trạng thái hiển thị
            self.current_display_mode = 'fullscreen' if self.current_display_mode == 'windowed' else 'windowed'
            
            # Update current monitor state
            self.monitor_states[self.current_monitor_index]["fullscreen"] = (self.current_display_mode == "fullscreen")
            
            debug_print(f"📤 Sent toggle fullscreen command to target: {target_client}")
            debug_print(f"💾 Updated monitor {self.current_monitor_index} fullscreen state to: {self.current_display_mode}")
            
            if hasattr(self, 'status_log'):
                self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Toggle fullscreen command to {target_client} (now {self.current_display_mode})")
        else:
            debug_print("❌ Failed to send toggle fullscreen command")
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def switch_monitor(self):
        """Send switch monitor command with state preservation"""
        target_client = self.get_target_client()
        selected_monitor = self.monitor_spin.value()
        
        # Debug current state before switching
        debug_print("🔄 BEFORE SWITCHING:")
        self.debug_monitor_states()
        
        # Save current monitor state before switching
        self.save_current_monitor_state()
        
        # Update current monitor index
        old_monitor = self.current_monitor_index
        self.current_monitor_index = selected_monitor
        
        debug_print(f"🔄 Switching from monitor {old_monitor} to monitor {selected_monitor}")
        debug_print(f"💾 Saved state for monitor {old_monitor}: {self.monitor_states[old_monitor]}")
        debug_print(f"🔍 Loading state for monitor {selected_monitor}: {self.monitor_states[selected_monitor]}")
        
        data = {
            'action': 'switch_monitor',
            'monitor_index': selected_monitor
        }
        
        if self.mqtt_handler.send_command('commands', data, target_client):
            debug_print(f"📤 Sent switch monitor command to target: {target_client}, monitor: {selected_monitor}")
            
            # Wait a moment for monitor switch to complete, then restore state
            QTimer.singleShot(1000, self.restore_monitor_state)
            
            if hasattr(self, 'status_log'):
                self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Switch to monitor {selected_monitor} on {target_client}")
        else:
            debug_print("❌ Failed to send switch monitor command")
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def show_background(self, bg_id):
        """Send show background command"""
        target_client = self.get_target_client()
        self.current_background = bg_id
        self.current_content_type = 'background'
        
        # Update current monitor state
        self.monitor_states[self.current_monitor_index]["background"] = bg_id
        
        # Use "display" topic like in enhanced version
        data = {
            'action': 'show_background',
            'background_id': bg_id
        }
        
        # Send to display topic instead of commands
        if self.mqtt_handler.send_command('display', data, target_client):
            debug_print(f"📤 Sent show background command to target: {target_client}, bg_id: {bg_id}")
            debug_print(f"💾 Updated monitor {self.current_monitor_index} background state to: {bg_id}")
            if hasattr(self, 'status_log'):
                self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Show background {bg_id} on {target_client}")
        else:
            debug_print(f"❌ Failed to send show background command: {bg_id}")
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
    
    def save_current_monitor_state(self):
        """Save current monitor state before switching"""
        current_state = self.monitor_states[self.current_monitor_index]
        current_state["background"] = self.current_background
        current_state["fullscreen"] = (self.current_display_mode == "fullscreen")
        current_state["display_open"] = True  # Assume display is open if we're switching
        
        debug_print(f"💾 Saved state for monitor {self.current_monitor_index}: {current_state}")
    
    def restore_monitor_state(self):
        """Restore state for the newly switched monitor"""
        target_state = self.monitor_states[self.current_monitor_index]
        target_client = self.get_target_client()
        
        debug_print(f"🔄 Restoring state for monitor {self.current_monitor_index}: {target_state}")
        
        # Restore background
        if target_state["background"]:
            debug_print(f"🖼️ Restoring background: {target_state['background']}")
            self.show_background(target_state["background"])
            
            # Wait before applying fullscreen state
            if target_state["fullscreen"]:
                debug_print(f"🖥️ Restoring fullscreen mode")
                QTimer.singleShot(1500, self.restore_fullscreen_state)
            else:
                debug_print(f"🪟 Keeping windowed mode")
        
        # Update UI to reflect current state
        self.current_background = target_state["background"]
        self.current_display_mode = "fullscreen" if target_state["fullscreen"] else "windowed"
        
        # Debug final state after switching
        QTimer.singleShot(2000, lambda: (
            debug_print("🔄 AFTER SWITCHING:"),
            self.debug_monitor_states()
        ))
    
    def restore_fullscreen_state(self):
        """Restore fullscreen state after background is set"""
        target_client = self.get_target_client()
        data = {
            'action': 'toggle_fullscreen'
        }
        
        if self.mqtt_handler.send_command('commands', data, target_client):
            debug_print(f"📤 Sent restore fullscreen command to target: {target_client}")
            self.current_display_mode = "fullscreen"
        else:
            debug_print("❌ Failed to restore fullscreen state")
            
    def show_selected_background(self):
        """Show background selected from combo box"""
        selected_text = self.bg_file_combo.currentText()
        if not selected_text:
            return
            
        # Extract background ID from combo box text
        if "00." in selected_text or "(Wait)" in selected_text:
            bg_id = "00"
        elif "01." in selected_text or "(Ranking)" in selected_text:
            bg_id = "01"
        elif "02." in selected_text or "(Final)" in selected_text:
            bg_id = "02"
        else:
            # Custom background file
            bg_id = selected_text.split()[0]  # Get filename part
            
        self.show_background(bg_id)
        
    def hide_background(self):
        """Hide background"""
        target_client = self.get_target_client()
        data = {
            'action': 'hide_background'
        }
        
        if self.mqtt_handler.send_command('hide_background', data, target_client):
            debug_print(f"📤 Sent hide background command to target: {target_client}")
        else:
            debug_print("❌ Failed to send hide background command")
            
    def apply_ranking(self):
        """Apply ranking data"""
        # Collect ranking data
        overlay_data = {'round': self.round_edit.text()}
        
        # Count actual ranks with data
        rank_count = 0
        for rank in self.rank_edits:
            if self.rank_edits[rank].text().strip():
                overlay_data[rank] = self.rank_edits[rank].text().strip()
                rank_count += 1
        
        # Collect positions
        positions = {}
        try:
            positions['round'] = self.round_pos_edit.text()
        except:
            positions['round'] = self.default_round_position
            
        for rank in self.rank_pos_edits:
            if self.rank_pos_edits[rank].text():
                positions[rank] = self.rank_pos_edits[rank].text()
                
        overlay_data['positions'] = positions
        
        # Font settings
        font_settings = {
            'font_name': self.rank_font_combo.currentText(),
            'rank_font_size': self.rank_font_size.value(),
            'round_font_size': self.rank_font_size.value(),
            'color': self.rank_font_color.currentText()
        }
        overlay_data['font_settings'] = font_settings
        
        debug_print(f"📤 Sending ranking data:")
        debug_print(f"   Round: {overlay_data.get('round', '')}")
        debug_print(f"   Ranks with data: {rank_count}")
        for rank in ['1st', '2nd', '3rd', '4th', '5th']:
            if rank in overlay_data:
                debug_print(f"   {rank}: {overlay_data[rank]}")
        
        target_client = self.get_target_client()
        if self.mqtt_handler.send_command('ranking', overlay_data, target_client):
            debug_print(f"✅ Sent ranking update with {rank_count} ranks to target: {target_client}")
        else:
            debug_print("❌ Failed to send ranking update")
            
    def apply_final_results(self):
        """Apply final results"""
        # Collect final results data
        overlay_data = {}
        for key in self.final_edits:
            if self.final_edits[key].text():
                overlay_data[key] = self.final_edits[key].text()
        
        # Collect positions
        positions = {}
        for key in self.final_pos_edits:
            if self.final_pos_edits[key].text():
                positions[key] = self.final_pos_edits[key].text()
                
        overlay_data['positions'] = positions
        
        # Font settings (use same as ranking but with different size)
        font_settings = {
            'font_name': self.rank_font_combo.currentText(),
            'font_size': self.final_font_size.value(),
            'color': self.rank_font_color.currentText()
        }
        overlay_data['font_settings'] = font_settings
        
        target_client = self.get_target_client()
        if self.mqtt_handler.send_command('final', overlay_data, target_client):
            debug_print(f"📤 Sent final results with {len([k for k in overlay_data if k not in ['positions', 'font_settings']])} positions to target: {target_client}")
        else:
            debug_print("❌ Failed to send final results")
            
    def request_client_info(self):
        """Request client information"""
        target_client = self.get_target_client()
        data = {'action': 'request_info'}
        if self.mqtt_handler.send_command('commands', data, target_client):
            debug_print(f"📤 Sent client info request to target: {target_client}")
            if hasattr(self, 'status_log'):
                self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Client info request to {target_client}")
        else:
            debug_print("❌ Failed to send client info request")
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def test_connection(self):
        """Test MQTT connection"""
        target_client = self.get_target_client()
        data = {'action': 'test_connection', 'timestamp': datetime.now().isoformat()}
        if self.mqtt_handler.send_command('commands', data, target_client):
            debug_print(f"📤 Sent test connection command to target: {target_client}")
            if hasattr(self, 'debug_text'):
                self.debug_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Test connection sent to {target_client}")
            if hasattr(self, 'status_log'):
                self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Test connection to {target_client}")
        else:
            debug_print("❌ Failed to send test connection")
            if hasattr(self, 'debug_text'):
                self.debug_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Test connection failed")
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def reconnect_mqtt(self):
        """Reconnect to MQTT broker"""
        if self.mqtt_handler:
            debug_print("🔄 Attempting MQTT reconnection...")
            self.mqtt_handler.disconnect()
            time.sleep(1)
            self.mqtt_handler.connect()
            
    def closeEvent(self, event):
        """Handle application close"""
        debug_print("🔚 Closing ScoShow Remote Control Super...")
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
        event.accept()

def main():
    """Main application entry point"""
    print("🚀 Starting ScoShow Remote Control Super Enhanced Version")
    print("Console logging is enabled for debugging MQTT communication")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    app.setApplicationName("ScoShow Remote Control Super")
    app.setApplicationVersion("2.0")
    
    try:
        debug_print("🎪 Starting ScoShow Remote Control Super...")
        window = ScoShowRemoteControlSuper()
        window.show()
        
        debug_print("✅ Application started successfully")
        sys.exit(app.exec_())
        
    except Exception as e:
        debug_print(f"❌ Fatal error: {e}")
        QMessageBox.critical(None, "Fatal Error", f"Application failed to start:\n{e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
