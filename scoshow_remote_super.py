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
import paho.mqtt.client as mqtt
from mqtt_config import *

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
        sys.stdout.flush()  # Force immediate output

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
                    
                    # Use row index + 1 as position (rank) - this is the key fix!
                    position = row_index + 1
                    
                    # Extract just the number from mb_number (in case it contains text)
                    mb_clean = mb_number
                    if mb_number:
                        # Extract numbers from the beginning of the string
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
            payload = {
                'command': command_type,
                'data': data or {},
                'timestamp': datetime.now().isoformat(),
                'session_id': UNIQUE_ID
            }
            
            topic = MQTT_TOPICS['command']
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
        
        # Setup UI
        self.init_ui()
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Setup status check timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_client_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        
        debug_print("✅ ScoShow Remote Control Super initialized")
        
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
        
        # Background controls
        bg_group = QGroupBox("Background Control")
        bg_layout = QGridLayout(bg_group)
        
        # Background folder
        self.bg_folder_edit = QLineEdit()
        self.bg_folder_edit.setPlaceholderText("Select background folder...")
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse_background_folder)
        
        bg_layout.addWidget(QLabel("Background Folder:"), 0, 0)
        bg_layout.addWidget(self.bg_folder_edit, 0, 1)
        bg_layout.addWidget(browse_btn, 0, 2)
        
        # Background selection
        self.bg_combo = QComboBox()
        bg_layout.addWidget(QLabel("Select Background:"), 1, 0)
        bg_layout.addWidget(self.bg_combo, 1, 1, 1, 2)
        
        # Display controls
        control_layout = QHBoxLayout()
        
        show_btn = QPushButton("👁️ Show Background")
        show_btn.clicked.connect(self.show_background)
        control_layout.addWidget(show_btn)
        
        hide_btn = QPushButton("🙈 Hide Background")
        hide_btn.clicked.connect(self.hide_background)
        control_layout.addWidget(hide_btn)
        
        fullscreen_btn = QPushButton("⛶ Toggle Fullscreen")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        control_layout.addWidget(fullscreen_btn)
        
        switch_btn = QPushButton("🖥️ Switch Monitor")
        switch_btn.clicked.connect(self.switch_monitor)
        control_layout.addWidget(switch_btn)
        
        bg_layout.addLayout(control_layout, 2, 0, 1, 3)
        
        layout.addWidget(bg_group)
        layout.addStretch()
        
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
        
        # Round information
        round_group = QGroupBox("Round Information")
        round_layout = QHBoxLayout(round_group)
        
        self.round_edit = QLineEdit()
        self.round_edit.setPlaceholderText("e.g., Round 1")
        round_layout.addWidget(QLabel("Round:"))
        round_layout.addWidget(self.round_edit)
        
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
        positions = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]
        
        for i, pos in enumerate(positions):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(f"Rank {pos}:")
            edit = QLineEdit()
            edit.setPlaceholderText(f"Member ID for {pos} place")
            
            ranking_layout.addWidget(label, row, col)
            ranking_layout.addWidget(edit, row, col + 1)
            
            self.rank_edits[pos] = edit
            
        layout.addWidget(ranking_group)
        
        # Position settings
        pos_group = QGroupBox("Position Settings")
        pos_layout = QGridLayout(pos_group)
        
        self.rank_positions = {}
        for i, pos in enumerate(positions):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(f"{pos} Position:")
            edit = QLineEdit()
            edit.setPlaceholderText("x,y coordinates")
            
            pos_layout.addWidget(label, row, col)
            pos_layout.addWidget(edit, row, col + 1)
            
            self.rank_positions[pos] = edit
            
        layout.addWidget(pos_group)
        
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
        positions = ["winner", "second", "third", "fourth", "fifth"]
        labels = ["🥇 Winner", "🥈 Second", "🥉 Third", "4th Place", "5th Place"]
        
        for i, (pos, label_text) in enumerate(zip(positions, labels)):
            label = QLabel(f"{label_text}:")
            edit = QLineEdit()
            edit.setPlaceholderText(f"Member ID for {label_text}")
            
            final_layout.addWidget(label, i, 0)
            final_layout.addWidget(edit, i, 1)
            
            self.final_edits[pos] = edit
            
        layout.addWidget(final_group)
        
        # Position settings
        pos_group = QGroupBox("Position Settings")
        pos_layout = QGridLayout(pos_group)
        
        self.final_positions = {}
        for i, (pos, label_text) in enumerate(zip(positions, labels)):
            label = QLabel(f"{label_text} Position:")
            edit = QLineEdit()
            edit.setPlaceholderText("x,y coordinates")
            
            pos_layout.addWidget(label, i, 0)
            pos_layout.addWidget(edit, i, 1)
            
            self.final_positions[pos] = edit
            
        layout.addWidget(pos_group)
        
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
        
        self.monitor_combo = QComboBox()
        try:
            monitors = get_monitors()
            for i, monitor in enumerate(monitors):
                self.monitor_combo.addItem(f"Monitor {i+1}: {monitor.width}x{monitor.height}")
        except:
            for i in range(4):
                self.monitor_combo.addItem(f"Monitor {i+1}: 1920x1080")
                
        monitor_layout.addWidget(QLabel("Target Monitor:"), 0, 0)
        monitor_layout.addWidget(self.monitor_combo, 0, 1)
        
        layout.addWidget(monitor_group)
        
        # Font settings
        font_group = QGroupBox("Font Settings")
        font_layout = QGridLayout(font_group)
        
        self.rank_font_size = QSpinBox()
        self.rank_font_size.setRange(20, 200)
        self.rank_font_size.setValue(80)
        
        self.final_font_size = QSpinBox()
        self.final_font_size.setRange(20, 200)
        self.final_font_size.setValue(120)
        
        font_layout.addWidget(QLabel("Ranking Font Size:"), 0, 0)
        font_layout.addWidget(self.rank_font_size, 0, 1)
        font_layout.addWidget(QLabel("Final Font Size:"), 1, 0)
        font_layout.addWidget(self.final_font_size, 1, 1)
        
        layout.addWidget(font_group)
        
        # Debug area
        debug_group = QGroupBox("Debug Information")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_text = QTextEdit()
        self.debug_text.setMaximumHeight(200)
        self.debug_text.setReadOnly(True)
        debug_layout.addWidget(self.debug_text)
        
        layout.addWidget(debug_group)
        
        layout.addStretch()
        
    def open_data_popup(self, tab_type):
        """Open the data input popup"""
        debug_print(f"🎪 Opening data popup for {tab_type}")
        popup = DataInputPopup(self, tab_type)
        result = popup.exec_()
        
        if result == QDialog.Accepted:
            debug_print(f"✅ Data accepted for {tab_type}")
        else:
            debug_print(f"❌ Data input cancelled for {tab_type}")
            
    def update_fields_from_popup(self, parsed_data, tab_type):
        """Update fields based on data from popup"""
        debug_print(f"📊 Updating {tab_type} fields with {len(parsed_data)} rows")
        
        if not parsed_data:
            return
            
        # Update round information
        if parsed_data[0].get('round'):
            self.round_edit.setText(str(parsed_data[0]['round']))
            self.current_round = str(parsed_data[0]['round'])
            
        if tab_type == "rank":
            # Update ranking fields
            positions = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]
            for i, row in enumerate(parsed_data[:10]):  # Limit to 10 ranks
                if i < len(positions):
                    mb_value = row.get('mb', '')
                    if mb_value:
                        self.rank_edits[positions[i]].setText(str(mb_value))  # Use member number instead of name
                        self.rank_data[positions[i]] = str(mb_value)
                        
        elif tab_type == "final":
            # Update final results fields
            positions = ["winner", "second", "third", "fourth", "fifth"]
            for i, row in enumerate(parsed_data[:5]):  # Limit to 5 final positions
                if i < len(positions):
                    mb_value = row.get('mb', '')
                    if mb_value:
                        self.final_edits[positions[i]].setText(mb_value)
                        self.final_data[positions[i]] = mb_value
                        
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
            debug_print("✅ MQTT setup completed")
        else:
            debug_print("❌ MQTT setup failed")
            
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
            if time_diff > 30:  # 30 seconds timeout
                self.client_online = False
                self.client_status.setText("🔴 Client: Offline")
                self.client_status.setStyleSheet("font-weight: bold; color: red;")
                
    def browse_background_folder(self):
        """Browse for background folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Background Folder")
        if folder:
            self.bg_folder_edit.setText(folder)
            self.load_background_list(folder)
            
    def load_background_list(self, folder):
        """Load background files from folder"""
        self.bg_combo.clear()
        try:
            files = os.listdir(folder)
            image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            image_files.sort()
            self.bg_combo.addItems(image_files)
        except Exception as e:
            debug_print(f"❌ Error loading background files: {e}")
            
    def show_background(self):
        """Show selected background"""
        bg_file = self.bg_combo.currentText()
        if bg_file and self.mqtt_handler:
            self.mqtt_handler.send_command("show_background", {"background": bg_file})
            debug_print(f"📤 Sent show background command: {bg_file}")
            
    def hide_background(self):
        """Hide background"""
        if self.mqtt_handler:
            self.mqtt_handler.send_command("hide_background")
            debug_print("📤 Sent hide background command")
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.mqtt_handler:
            self.mqtt_handler.send_command("toggle_fullscreen")
            debug_print("📤 Sent toggle fullscreen command")
            
    def switch_monitor(self):
        """Switch monitor"""
        monitor_index = self.monitor_combo.currentIndex()
        if self.mqtt_handler:
            self.mqtt_handler.send_command("switch_monitor", {"monitor": monitor_index})
            debug_print(f"📤 Sent switch monitor command: {monitor_index}")
            
    def apply_ranking(self):
        """Apply ranking data"""
        ranking_data = {}
        for pos, edit in self.rank_edits.items():
            if edit.text():
                ranking_data[pos] = edit.text()
                
        positions = {}
        for pos, edit in self.rank_positions.items():
            if edit.text():
                positions[pos] = edit.text()
                
        if self.mqtt_handler and ranking_data:
            data = {
                "round": self.round_edit.text(),
                "ranking": ranking_data,
                "positions": positions,
                "font_size": self.rank_font_size.value()
            }
            self.mqtt_handler.send_command("update_ranking", data)
            debug_print(f"📤 Sent ranking update: {len(ranking_data)} ranks")
            
    def apply_final_results(self):
        """Apply final results"""
        final_data = {}
        for pos, edit in self.final_edits.items():
            if edit.text():
                final_data[pos] = edit.text()
                
        positions = {}
        for pos, edit in self.final_positions.items():
            if edit.text():
                positions[pos] = edit.text()
                
        if self.mqtt_handler and final_data:
            data = {
                "final": final_data,
                "positions": positions,
                "font_size": self.final_font_size.value()
            }
            self.mqtt_handler.send_command("update_final", data)
            debug_print(f"📤 Sent final results: {len(final_data)} positions")
            
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
