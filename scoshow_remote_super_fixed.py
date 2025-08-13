"""
ScoShow MQTT Remote Control - Super Enhanced Version
This runs on the remote computer for controlling the client display
Enhanced with Data Paste Pop-up and Improved UI
"""

import sys
import json
import time
import os
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
        """Parse the raw data into structured format"""
        rows = raw_data.split('\n')
        parsed_data = []
        
        # Skip header row if present
        data_rows = []
        for row in rows:
            if row.strip() and not row.strip().upper().startswith(('ROUND', 'MB', 'NAME')):
                data_rows.append(row.strip())
        
        for row_index, row in enumerate(data_rows):
            if not row.strip():
                continue
                
            # Try tab-separated first, then comma, then space
            columns = row.split('\t')
            if len(columns) < 3:
                columns = row.split(',')
            if len(columns) < 3:
                columns = row.split()
                
            if len(columns) >= 3:
                try:
                    round_info = columns[0].strip()
                    mb_number = columns[1].strip()
                    name = columns[2].strip()
                    
                    # Extract round number from "Round X" format
                    import re
                    round_num = 1
                    if 'round' in round_info.lower():
                        round_match = re.search(r'round\s*(\d+)', round_info.lower())
                        if round_match:
                            round_num = int(round_match.group(1))
                    
                    # Use row index + 1 as position (rank)
                    position = row_index + 1
                    
                    # Extract just the number from mb_number
                    mb_clean = mb_number
                    if mb_number:
                        number_match = re.search(r'^\d+', mb_number)
                        if number_match:
                            mb_clean = number_match.group(0)
                    
                    data_row = {
                        'round': round_num,
                        'position': position,
                        'mb': mb_clean,
                        'name': name,
                        'credit': columns[3].strip() if len(columns) > 3 else '',
                        'last_bet': columns[4].strip() if len(columns) > 4 else ''
                    }
                    parsed_data.append(data_row)
                except (ValueError, IndexError) as e:
                    debug_print(f"Error parsing row {row_index + 1}: {e}")
                    continue
                
        return parsed_data

class MQTTRemoteHandler(QObject):
    """Handle MQTT communication for remote control"""
    
    # Signals
    status_received = pyqtSignal(dict)
    heartbeat_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    
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
            
            if topic == MQTT_TOPICS['status']:
                self.status_received.emit(payload)
            elif topic == MQTT_TOPICS['heartbeat']:
                self.heartbeat_received.emit(payload)
                
        except Exception as e:
            debug_print(f"❌ Error processing MQTT message: {e}")
            
    def send_command(self, command_type, data=None):
        """Send command via MQTT"""
        if not self.connected:
            debug_print("❌ Cannot send command: Not connected to MQTT broker")
            return False
            
        try:
            # Use different topic based on command type
            if command_type in ['ranking', 'final']:
                topic = MQTT_TOPICS.get(command_type, MQTT_TOPICS['commands'])
            else:
                topic = MQTT_TOPICS['commands']
                
            # Prepare data based on enhanced version format
            if command_type == 'ranking':
                message = json.dumps(data, ensure_ascii=False)
            elif command_type == 'final':
                message = json.dumps(data, ensure_ascii=False)  
            else:
                payload = {
                    'action': command_type,
                    'data': data or {},
                    'timestamp': datetime.now().isoformat(),
                    'session_id': UNIQUE_ID
                }
                message = json.dumps(payload)
            
            debug_print(f"📤 Sending command '{command_type}' to topic '{topic}'")
            debug_print(f"📦 Payload: {message}")
            
            result = self.client.publish(topic, message, qos=MQTT_QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                debug_print(f"✅ Command '{command_type}' sent successfully")
                return True
            else:
                debug_print(f"❌ Failed to send command '{command_type}', error code: {result.rc}")
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
        
        # Reconnect button
        reconnect_btn = QPushButton("🔄 Reconnect")
        reconnect_btn.clicked.connect(self.reconnect_mqtt)
        status_layout.addWidget(reconnect_btn)
        
        main_layout.addWidget(status_frame)
        
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
        bg_layout = QHBoxLayout(bg_group)
        
        bg00_btn = QPushButton("⏸️ Wait (00)")
        bg00_btn.clicked.connect(lambda: self.show_background("00"))
        bg_layout.addWidget(bg00_btn)
        
        bg01_btn = QPushButton("📊 Ranking (01)")
        bg01_btn.clicked.connect(lambda: self.show_background("01"))
        bg_layout.addWidget(bg01_btn)
        
        bg02_btn = QPushButton("🏆 Final (02)")
        bg02_btn.clicked.connect(lambda: self.show_background("02"))
        bg_layout.addWidget(bg02_btn)
        
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
            self.round_edit.setText(f"Round {parsed_data[0]['round']}")
            
        if tab_type == "rank":
            # Update ranking fields
            positions = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]
            for i, row in enumerate(parsed_data[:10]):  # Only take first 10 for ranking
                if i < len(positions):
                    pos = positions[i]
                    if pos in self.rank_edits:
                        name = row.get('name', '')
                        mb = row.get('mb', '')
                        if mb:
                            display_text = f"MB {mb} - {name}"
                        else:
                            display_text = name
                        self.rank_edits[pos].setText(display_text)
                        
        elif tab_type == "final":
            # Update final results fields
            final_keys = ['winner', 'second', 'third', 'fourth', 'fifth']
            for i, row in enumerate(parsed_data[:5]):  # Only take first 5 for final
                if i < len(final_keys):
                    key = final_keys[i]
                    if key in self.final_edits:
                        name = row.get('name', '')
                        mb = row.get('mb', '')
                        if mb:
                            display_text = f"MB {mb} - {name}"
                        else:
                            display_text = name
                        self.final_edits[key].setText(display_text)
                        
        debug_print(f"✅ Fields updated successfully for {tab_type}")
        
    def setup_mqtt(self):
        """Setup MQTT handler"""
        debug_print("🔧 Setting up MQTT handler...")
        self.mqtt_handler = MQTTRemoteHandler()
        
        # Connect signals
        self.mqtt_handler.connection_changed.connect(self.handle_connection_changed)
        self.mqtt_handler.status_received.connect(self.handle_status_received)
        self.mqtt_handler.heartbeat_received.connect(self.handle_heartbeat_received)
        
        # Connect to broker
        if self.mqtt_handler.connect():
            debug_print("✅ MQTT connection initiated")
        else:
            debug_print("❌ Failed to initiate MQTT connection")
            
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
        
        # Update debug text
        status_text = f"[{datetime.now().strftime('%H:%M:%S')}] Status: {data}\n"
        self.debug_text.append(status_text)
        
    def handle_heartbeat_received(self, data):
        """Handle heartbeat from client"""
        self.last_heartbeat = datetime.now()
        self.client_online = True
        self.client_status.setText("🟢 Client: Online")
        self.client_status.setStyleSheet("font-weight: bold; color: green;")
        debug_print("💓 Heartbeat received from client")
        
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
            
    def open_display(self):
        """Send open display command"""
        data = {
            'action': 'open_display',
            'monitor_index': self.monitor_spin.value(),
            'background_folder': self.bg_folder_edit.text()
        }
        
        if self.mqtt_handler.send_command('open_display', data):
            debug_print("📤 Sent open display command")
        else:
            debug_print("❌ Failed to send open display command")
            
    def close_display(self):
        """Send close display command"""
        data = {'action': 'close_display'}
        
        if self.mqtt_handler.send_command('close_display', data):
            debug_print("📤 Sent close display command")
        else:
            debug_print("❌ Failed to send close display command")
            
    def toggle_fullscreen(self):
        """Send toggle fullscreen command"""
        data = {'action': 'toggle_fullscreen'}
        
        if self.mqtt_handler.send_command('toggle_fullscreen', data):
            debug_print("📤 Sent toggle fullscreen command")
        else:
            debug_print("❌ Failed to send toggle fullscreen command")
            
    def switch_monitor(self):
        """Send switch monitor command"""
        data = {
            'action': 'switch_monitor',
            'monitor_index': self.monitor_spin.value(),
            'maintain_content': True
        }
        
        if self.mqtt_handler.send_command('switch_monitor', data):
            debug_print(f"📤 Sent switch monitor command: {self.monitor_spin.value()}")
        else:
            debug_print("❌ Failed to send switch monitor command")
            
    def show_background(self, bg_id):
        """Send show background command"""
        self.current_background = bg_id
        self.current_content_type = 'background'
        
        data = {
            'action': 'show_background',
            'background_id': bg_id
        }
        
        if self.mqtt_handler.send_command('show_background', data):
            debug_print(f"📤 Sent show background command: {bg_id}")
        else:
            debug_print(f"❌ Failed to send show background command: {bg_id}")
            
    def apply_ranking(self):
        """Apply ranking data"""
        # Collect ranking data
        overlay_data = {'round': self.round_edit.text()}
        
        for rank in self.rank_edits:
            if self.rank_edits[rank].text():
                overlay_data[rank] = self.rank_edits[rank].text()
        
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
        
        if self.mqtt_handler.send_command('ranking', overlay_data):
            debug_print(f"📤 Sent ranking update with {len([k for k in overlay_data if k not in ['positions', 'font_settings', 'round']])} ranks")
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
        
        if self.mqtt_handler.send_command('final', overlay_data):
            debug_print(f"📤 Sent final results with {len([k for k in overlay_data if k not in ['positions', 'font_settings']])} positions")
        else:
            debug_print("❌ Failed to send final results")
            
    def request_client_info(self):
        """Request client information"""
        data = {'action': 'request_info'}
        if self.mqtt_handler.send_command('request_info', data):
            debug_print("📤 Sent client info request")
        else:
            debug_print("❌ Failed to send client info request")
            
    def test_connection(self):
        """Test MQTT connection"""
        data = {'action': 'test_connection', 'timestamp': datetime.now().isoformat()}
        if self.mqtt_handler.send_command('test_connection', data):
            debug_print("📤 Sent test connection command")
            self.debug_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Test connection sent\n")
        else:
            debug_print("❌ Failed to send test connection")
            self.debug_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] Test connection failed\n")
            
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
