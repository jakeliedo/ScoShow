"""
ScoShow MQTT Remote Control - Remote Application (Enhanced with Debug)
This runs on the remote computer for controlling the client display
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
                             QSpinBox, QCheckBox)
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
            debug_print("✅ Connected to MQTT broker successfully!")
            self.connected = True
            self.connection_changed.emit(True)
            
            # Subscribe to status and heartbeat topics
            debug_print(f"📬 Subscribing to status topic: {MQTT_TOPICS['status']}")
            client.subscribe(MQTT_TOPICS['status'], MQTT_QOS)
            
            debug_print(f"💓 Subscribing to heartbeat topic: {MQTT_TOPICS['heartbeat']}")
            client.subscribe(MQTT_TOPICS['heartbeat'], MQTT_QOS)
            
            debug_print("🎯 Remote is now ready to receive messages from client!")
            
        else:
            debug_print(f"❌ Failed to connect to MQTT broker, return code: {rc}")
            debug_print(f"   RC meanings: 0=Success, 1=Protocol, 2=Client ID, 3=Server unavailable, 4=Bad user/pass, 5=Not authorized")
            self.connected = False
            self.connection_changed.emit(False)
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        debug_print(f"🔌 Disconnected from MQTT broker (RC: {rc})")
        self.connected = False
        self.connection_changed.emit(False)
        
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode()
            payload = json.loads(payload_str)
            
            debug_print("="*60)
            debug_print(f"📨 RECEIVED MESSAGE FROM CLIENT")
            debug_print(f"   Topic: {topic}")
            debug_print(f"   Raw Payload: {payload_str}")
            debug_print(f"   Parsed Data: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            if topic == MQTT_TOPICS['status']:
                debug_print(f"📊 Processing STATUS message...")
                debug_print(f"   Status: {payload.get('status', 'unknown')}")
                debug_print(f"   Message: {payload.get('message', 'N/A')}")
                debug_print(f"   Timestamp: {payload.get('timestamp', 'N/A')}")
                self.status_received.emit(payload)
                
            elif topic == MQTT_TOPICS['heartbeat']:
                debug_print(f"💓 Processing HEARTBEAT message...")
                debug_print(f"   Client alive at: {payload.get('timestamp', 'N/A')}")
                debug_print(f"   Display status: {payload.get('display_status', 'unknown')}")
                debug_print(f"   Background: {payload.get('current_background', 'unknown')}")
                if 'system_info' in payload:
                    debug_print(f"   System info: {payload['system_info']}")
                self.heartbeat_received.emit(payload)
            else:
                debug_print(f"❓ Unknown topic received: {topic}")
            
            debug_print("="*60)
                
        except Exception as e:
            debug_print(f"❌ Error processing message: {e}")
            debug_print(f"   Topic: {msg.topic}")
            debug_print(f"   Raw payload: {msg.payload}")
            debug_print("="*60)
            
    def send_command(self, command_type, data):
        """Send command to client"""
        if not self.connected:
            debug_print(f"❌ Cannot send command - MQTT not connected!")
            return False
            
        topic = MQTT_TOPICS.get(command_type, MQTT_TOPICS['commands'])
        message = json.dumps(data, ensure_ascii=False)
        
        try:
            debug_print(f"📤 SENDING COMMAND TO CLIENT")
            debug_print(f"   Command Type: {command_type}")
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

class ScoShowRemoteControl(QMainWindow):
    """Remote Control UI for ScoShow"""
    
    def __init__(self):
        super().__init__()
        
        debug_print("🚀 ScoShow Remote Control starting...")
        debug_print("="*50)
        
        # Initialize variables
        self.mqtt_handler = None
        self.client_status = "Disconnected"
        self.last_heartbeat = None
        self.current_background = "00"  # Track current background
        self.current_display_mode = "windowed"  # Track fullscreen/windowed state
        self.current_content_type = None  # Track what's currently displayed (background/ranking/final)
        self.config_file = "remote_config.json"  # Config file for settings
        
        # Setup window
        debug_print("🔧 Setting up main window...")
        self.setup_window()
        
        # Setup variables
        debug_print("🔧 Setting up variables...")
        self.setup_variables()
        
        # Load saved settings
        debug_print("📁 Loading saved settings...")
        self.load_settings()
        
        # Setup UI
        debug_print("🎨 Setting up user interface...")
        self.setup_ui()
        
        # Setup MQTT
        debug_print("📡 Setting up MQTT connection...")
        self.setup_mqtt()
        
        # Setup status check timer
        debug_print("⏰ Setting up status timer...")
        self.setup_status_timer()
        
        debug_print("✅ ScoShow Remote Control initialization complete!")
        debug_print("="*50)
        
    def setup_window(self):
        """Setup main window"""
        self.setWindowTitle("ScoShow - Remote Control")
        self.setGeometry(100, 100, 1000, 800)
        
    def setup_variables(self):
        """Setup default variables"""
        # Default positions for ranking
        self.default_rank_positions = {
            '1st': "2980,125", '2nd': "2980,220", '3rd': "2980,318", 
            '4th': "2980,402", '5th': "2980,495", '6th': "2980,578", 
            '7th': "2980,672", '8th': "2980,762", '9th': "2980,850", 
            '10th': "2980,939"
        }
        self.default_rank_font_size = 80  # Font size for ranking

        # Default positions for final results
        self.default_final_positions = {
            'winner': "3000,80", 'second': "3000,280", 'third': "3000,480", 
            'fourth': "3000,680", 'fifth': "3000,880"
        }
        self.default_final_font_size = 120  # Font size for final results

        # Default position for Round
        self.default_round_position = "1286,935"
        
        # Available monitors list
        self.available_monitors = []
        self.detect_monitors()
        
    def detect_monitors(self):
        """Detect available monitors - Will be updated from client"""
        # Default monitors (will be updated when client connects)
        self.available_monitors = ["Monitor 1 (Primary)", "Monitor 2", "Monitor 3", "Monitor 4"]
        debug_print("🖥️ Using default monitor list (will be updated from client)")
        debug_print(f"   Default monitors: {self.available_monitors}")
            
    def update_monitors_from_client(self, monitor_info):
        """Update monitor information received from client"""
        try:
            if isinstance(monitor_info, list) and len(monitor_info) > 0:
                self.available_monitors = monitor_info
                debug_print("🖥️ MONITOR INFO UPDATED FROM CLIENT:")
                for i, monitor in enumerate(self.available_monitors):
                    debug_print(f"   Monitor {i}: {monitor}")
                
                # Update UI if monitor combo exists
                if hasattr(self, 'monitor_combo'):
                    current_selection = self.monitor_combo.currentText()
                    self.monitor_combo.clear()
                    for monitor_name in self.available_monitors:
                        self.monitor_combo.addItem(monitor_name)
                    
                    # Try to restore previous selection
                    index = self.monitor_combo.findText(current_selection)
                    if index >= 0:
                        self.monitor_combo.setCurrentIndex(index)
                        
                # Update spin box range
                if hasattr(self, 'monitor_spin'):
                    current_value = self.monitor_spin.value()
                    self.monitor_spin.setRange(0, len(self.available_monitors)-1)
                    if current_value < len(self.available_monitors):
                        self.monitor_spin.setValue(current_value)
                        
                return True
        except Exception as e:
            debug_print(f"❌ Error updating monitors from client: {e}")
            return False
            
    def load_settings(self):
        """Load saved settings from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # Store settings to apply after UI creation
                self.saved_settings = config
            else:
                self.saved_settings = {}
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.saved_settings = {}
            
    def save_settings(self):
        """Save current settings to config file"""
        try:
            config = {
                'monitor_index': self.monitor_spin.value() if hasattr(self, 'monitor_spin') else 0,
                'background_folder': self.bg_folder_edit.text() if hasattr(self, 'bg_folder_edit') else "",
                'rank_font': self.rank_font_combo.currentText() if hasattr(self, 'rank_font_combo') else "arial.ttf",
                'rank_font_size': self.rank_font_size.value() if hasattr(self, 'rank_font_size') else 60,
                'rank_font_color': self.rank_font_color.currentText() if hasattr(self, 'rank_font_color') else "white",
                'final_font_size': self.final_font_size.value() if hasattr(self, 'final_font_size') else 120,
                'current_background': self.current_background,
                'current_display_mode': self.current_display_mode,
                'current_content_type': self.current_content_type,
                'round_text': self.round_edit.text() if hasattr(self, 'round_edit') else "",
                'round_position': self.round_pos_edit.text() if hasattr(self, 'round_pos_edit') else "1286,917"
            }
            
            # Save ranking data
            if hasattr(self, 'rank_edits'):
                config['ranking_data'] = {rank: edit.text() for rank, edit in self.rank_edits.items()}
                config['ranking_positions'] = {rank: edit.text() for rank, edit in self.rank_pos_edits.items()}
                
            # Save final results data
            if hasattr(self, 'final_edits'):
                config['final_data'] = {key: edit.text() for key, edit in self.final_edits.items()}
                config['final_positions'] = {key: edit.text() for key, edit in self.final_pos_edits.items()}
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def apply_saved_settings(self):
        """Apply saved settings to UI elements"""
        if not self.saved_settings:
            # Set default font size for final results to 120
            if hasattr(self, 'final_font_size'):
                self.final_font_size.setValue(120)
            return
            
        try:
            # Apply monitor setting
            if hasattr(self, 'monitor_combo') and 'monitor_index' in self.saved_settings:
                monitor_index = self.saved_settings['monitor_index']
                if monitor_index < self.monitor_combo.count():
                    self.monitor_combo.setCurrentIndex(monitor_index)
                    
            # Apply background folder
            if hasattr(self, 'bg_folder_edit') and 'background_folder' in self.saved_settings:
                self.bg_folder_edit.setText(self.saved_settings['background_folder'])
                
            # Apply font settings
            if hasattr(self, 'rank_font_combo') and 'rank_font' in self.saved_settings:
                index = self.rank_font_combo.findText(self.saved_settings['rank_font'])
                if index >= 0:
                    self.rank_font_combo.setCurrentIndex(index)
                    
            if hasattr(self, 'rank_font_size') and 'rank_font_size' in self.saved_settings:
                self.rank_font_size.setValue(self.saved_settings['rank_font_size'])
                
            if hasattr(self, 'rank_font_color') and 'rank_font_color' in self.saved_settings:
                index = self.rank_font_color.findText(self.saved_settings['rank_font_color'])
                if index >= 0:
                    self.rank_font_color.setCurrentIndex(index)
                    
            # Apply final font size (default 120 if not saved)
            if hasattr(self, 'final_font_size'):
                final_size = self.saved_settings.get('final_font_size', 120)
                self.final_font_size.setValue(final_size)
                
            # Apply current background
            if 'current_background' in self.saved_settings:
                self.current_background = self.saved_settings['current_background']
                
            # Apply current display mode
            if 'current_display_mode' in self.saved_settings:
                self.current_display_mode = self.saved_settings['current_display_mode']
                
            # Apply current content type
            if 'current_content_type' in self.saved_settings:
                self.current_content_type = self.saved_settings['current_content_type']
                
            # Apply round settings
            if hasattr(self, 'round_edit') and 'round_text' in self.saved_settings:
                self.round_edit.setText(self.saved_settings['round_text'])
                
            if hasattr(self, 'round_pos_edit') and 'round_position' in self.saved_settings:
                self.round_pos_edit.setText(self.saved_settings['round_position'])
                
            # Apply ranking data
            if hasattr(self, 'rank_edits') and 'ranking_data' in self.saved_settings:
                for rank, text in self.saved_settings['ranking_data'].items():
                    if rank in self.rank_edits:
                        self.rank_edits[rank].setText(text)
                        
            if hasattr(self, 'rank_pos_edits') and 'ranking_positions' in self.saved_settings:
                for rank, pos in self.saved_settings['ranking_positions'].items():
                    if rank in self.rank_pos_edits:
                        self.rank_pos_edits[rank].setText(pos)
                        
            # Apply final data
            if hasattr(self, 'final_edits') and 'final_data' in self.saved_settings:
                for key, text in self.saved_settings['final_data'].items():
                    if key in self.final_edits:
                        self.final_edits[key].setText(text)
                        
            if hasattr(self, 'final_pos_edits') and 'final_positions' in self.saved_settings:
                for key, pos in self.saved_settings['final_positions'].items():
                    if key in self.final_pos_edits:
                        self.final_pos_edits[key].setText(pos)
                        
        except Exception as e:
            print(f"Error applying saved settings: {e}")
        
    def setup_ui(self):
        """Setup user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Connection status
        self.create_connection_section(main_layout)
        
        # Control tabs
        self.create_control_tabs(main_layout)
        
        # Status log
        self.create_status_section(main_layout)
        
        # Apply default round position and font size for Ranking
        if hasattr(self, 'round_pos_edit'):
            self.round_pos_edit.setText(self.default_round_position)
        if hasattr(self, 'rank_font_size'):
            self.rank_font_size.setValue(self.default_rank_font_size)

        # Apply default font size for Final results
        if hasattr(self, 'final_font_size'):
            self.final_font_size.setValue(self.default_final_font_size)
        
    def create_connection_section(self, layout):
        """Create connection status section"""
        group = QGroupBox("🌐 Connection Status")
        group.setMaximumHeight(100)
        group_layout = QHBoxLayout(group)
        
        self.connection_label = QLabel("MQTT: Disconnected")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        group_layout.addWidget(self.connection_label)
        
        self.client_label = QLabel("Client: Unknown")
        self.client_label.setStyleSheet("color: orange; font-weight: bold;")
        group_layout.addWidget(self.client_label)
        
        self.heartbeat_label = QLabel("Last Heartbeat: Never")
        group_layout.addWidget(self.heartbeat_label)
        
        reconnect_btn = QPushButton("🔄 Reconnect")
        reconnect_btn.clicked.connect(self.reconnect_mqtt)
        group_layout.addWidget(reconnect_btn)
        
        layout.addWidget(group)
        
    def create_control_tabs(self, layout):
        """Create control tabs"""
        tab_widget = QTabWidget()
        
        # Display Control Tab
        display_tab = QWidget()
        self.create_display_tab(display_tab)
        tab_widget.addTab(display_tab, "📺 Display Control")
        
        # Ranking Tab
        ranking_tab = QWidget()
        self.create_ranking_tab(ranking_tab)
        tab_widget.addTab(ranking_tab, "📊 Ranking")
        
        # Final Results Tab
        final_tab = QWidget()
        self.create_final_tab(final_tab)
        tab_widget.addTab(final_tab, "🏆 Final Results")
        
        # Debug Tab
        debug_tab = QWidget()
        self.create_debug_tab(debug_tab)
        tab_widget.addTab(debug_tab, "🐛 Debug")
        
        layout.addWidget(tab_widget)
        
    def create_display_tab(self, tab):
        """Create display control tab"""
        layout = QVBoxLayout(tab)
        
        # Monitor and Background Setup
        setup_group = QGroupBox("🖥️ Setup")
        setup_layout = QGridLayout(setup_group)
        
        # Monitor selection with detected monitors
        setup_layout.addWidget(QLabel("Monitor:"), 0, 0)
        self.monitor_combo = QComboBox()
        for monitor_name in self.available_monitors:
            self.monitor_combo.addItem(monitor_name)
        setup_layout.addWidget(self.monitor_combo, 0, 1)
        
        # Keep spin box for compatibility but hidden
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
        
    def create_ranking_tab(self, tab):
        """Create ranking control tab"""
        layout = QVBoxLayout(tab)
        
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
        self.rank_font_size.setValue(60)
        font_layout.addWidget(self.rank_font_size)
        
        font_layout.addWidget(QLabel("Color:"))
        self.rank_font_color = QComboBox()
        self.rank_font_color.addItems(["white", "black", "red", "blue", "yellow"])
        font_layout.addWidget(self.rank_font_color)
        
        layout.addWidget(font_group)
        
        # Round Input
        round_group = QGroupBox("🔢 Round")
        round_layout = QHBoxLayout(round_group)
        
        round_layout.addWidget(QLabel("Round:"))
        self.round_edit = QLineEdit()
        round_layout.addWidget(self.round_edit)
        
        round_layout.addWidget(QLabel("Position:"))
        self.round_pos_edit = QLineEdit("1286,917")
        round_layout.addWidget(self.round_pos_edit)
        
        layout.addWidget(round_group)
        
        # Ranking Inputs
        ranking_group = QGroupBox("🏆 Rankings")
        ranking_layout = QGridLayout(ranking_group)
        
        self.rank_edits = {}
        self.rank_pos_edits = {}
        
        ranks = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']
        for i, rank in enumerate(ranks):
            row = i % 5
            col = (i // 5) * 4
            
            # Rank label
            ranking_layout.addWidget(QLabel(f"{rank}:"), row, col)
            
            # Name input
            self.rank_edits[rank] = QLineEdit()
            ranking_layout.addWidget(self.rank_edits[rank], row, col + 1)
            
            # Position label
            ranking_layout.addWidget(QLabel("Pos:"), row, col + 2)
            
            # Position input
            self.rank_pos_edits[rank] = QLineEdit(self.default_rank_positions[rank])
            ranking_layout.addWidget(self.rank_pos_edits[rank], row, col + 3)
            
        layout.addWidget(ranking_group)
        
        # Apply Button
        apply_ranking_btn = QPushButton("✅ Apply Ranking")
        apply_ranking_btn.clicked.connect(self.apply_ranking)
        apply_ranking_btn.setStyleSheet("background-color: #2ECC71; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(apply_ranking_btn)
        
    def create_final_tab(self, tab):
        """Create final results tab"""
        layout = QVBoxLayout(tab)
        
        # Font Settings
        font_group = QGroupBox("🔤 Font Settings")
        font_layout = QHBoxLayout(font_group)
        
        font_layout.addWidget(QLabel("Font Size:"))
        self.final_font_size = QSpinBox()
        self.final_font_size.setRange(10, 200)
        self.final_font_size.setValue(60)
        font_layout.addWidget(self.final_font_size)
        
        font_layout.addWidget(QLabel("(Uses same font & color as ranking)"))
        
        layout.addWidget(font_group)
        
        # Final Results Inputs
        final_group = QGroupBox("🏆 Final Results")
        final_layout = QGridLayout(final_group)
        
        self.final_edits = {}
        self.final_pos_edits = {}
        
        final_labels = {
            'winner': '🥇 1st Place:', 'second': '🥈 2nd Place:', 'third': '🥉 3rd Place:',
            'fourth': '🏅 4th Place:', 'fifth': '🎖️ 5th Place:'
        }
        
        for i, (key, label) in enumerate(final_labels.items()):
            row = i % 3
            col = (i // 3) * 4
            
            # Label
            final_layout.addWidget(QLabel(label), row, col)
            
            # Name input
            self.final_edits[key] = QLineEdit()
            final_layout.addWidget(self.final_edits[key], row, col + 1)
            
            # Position label
            final_layout.addWidget(QLabel("Pos:"), row, col + 2)
            
            # Position input
            self.final_pos_edits[key] = QLineEdit(self.default_final_positions[key])
            final_layout.addWidget(self.final_pos_edits[key], row, col + 3)
            
        layout.addWidget(final_group)
        
        # Apply Button
        apply_final_btn = QPushButton("🏆 Apply Final Results")
        apply_final_btn.clicked.connect(self.apply_final_results)
        apply_final_btn.setStyleSheet("background-color: #E67E22; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(apply_final_btn)
        
    def create_debug_tab(self, tab):
        """Create debug control tab"""
        layout = QVBoxLayout(tab)
        
        # Debug Commands Group
        debug_group = QGroupBox("🐛 Debug Commands")
        debug_layout = QGridLayout(debug_group)
        
        # Request Client Info
        info_btn = QPushButton("📋 Request Client Info")
        info_btn.clicked.connect(self.request_client_info)
        info_btn.setStyleSheet("background-color: #3498DB; color: white; font-weight: bold; padding: 10px;")
        debug_layout.addWidget(info_btn, 0, 0)
        
        # Request Monitor Info
        monitor_btn = QPushButton("🖥️ Request Monitor Info")
        monitor_btn.clicked.connect(self.request_monitor_info)
        monitor_btn.setStyleSheet("background-color: #9B59B6; color: white; font-weight: bold; padding: 10px;")
        debug_layout.addWidget(monitor_btn, 0, 1)
        
        # Test Connection
        test_btn = QPushButton("🔍 Test Connection")
        test_btn.clicked.connect(self.test_connection)
        test_btn.setStyleSheet("background-color: #E74C3C; color: white; font-weight: bold; padding: 10px;")
        debug_layout.addWidget(test_btn, 1, 0)
        
        # Generate Debug Report
        report_btn = QPushButton("📄 Generate Debug Report")
        report_btn.clicked.connect(self.generate_debug_report)
        report_btn.setStyleSheet("background-color: #F39C12; color: white; font-weight: bold; padding: 10px;")
        debug_layout.addWidget(report_btn, 1, 1)
        
        layout.addWidget(debug_group)
        
        # Debug Info Display
        info_group = QGroupBox("📊 Debug Information")
        info_layout = QVBoxLayout(info_group)
        
        self.debug_info = QTextEdit()
        self.debug_info.setReadOnly(True)
        self.debug_info.setMaximumHeight(200)
        self.debug_info.setPlainText("Debug information will appear here...")
        info_layout.addWidget(self.debug_info)
        
        clear_debug_btn = QPushButton("🗑️ Clear Debug Info")
        clear_debug_btn.clicked.connect(lambda: self.debug_info.clear())
        info_layout.addWidget(clear_debug_btn)
        
        layout.addWidget(info_group)
        
        # Export Debug Log
        export_group = QGroupBox("💾 Export Debug")
        export_layout = QHBoxLayout(export_group)
        
        export_btn = QPushButton("📤 Export Debug Log to File")
        export_btn.clicked.connect(self.export_debug_log)
        export_btn.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 10px;")
        export_layout.addWidget(export_btn)
        
        layout.addWidget(export_group)
        
    def create_status_section(self, layout):
        """Create status log section"""
        group = QGroupBox("📝 Status Log")
        group.setMaximumHeight(200)
        group_layout = QVBoxLayout(group)
        
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setMaximumHeight(150)
        group_layout.addWidget(self.status_log)
        
        clear_btn = QPushButton("🗑️ Clear Log")
        clear_btn.clicked.connect(self.clear_status_log)
        group_layout.addWidget(clear_btn)
        
        layout.addWidget(group)
        
    def setup_mqtt(self):
        """Setup MQTT handler"""
        self.mqtt_handler = MQTTRemoteHandler()
        self.mqtt_handler.status_received.connect(self.handle_status_received)
        self.mqtt_handler.heartbeat_received.connect(self.handle_heartbeat_received)
        self.mqtt_handler.connection_changed.connect(self.handle_connection_changed)
        
        # Connect to MQTT broker
        self.mqtt_handler.connect()
        
    def setup_status_timer(self):
        """Setup status check timer"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_client_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        
    def handle_connection_changed(self, connected):
        """Handle MQTT connection status change"""
        if connected:
            debug_print("🟢 MQTT Connection established!")
            self.connection_label.setText("MQTT: Connected")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            debug_print("🔴 MQTT Connection lost!")
            self.connection_label.setText("MQTT: Disconnected")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
            
    def handle_status_received(self, data):
        """Handle status message from client"""
        status = data.get('status', 'unknown')
        message = data.get('message', '')
        timestamp = data.get('timestamp', time.time())
        
        debug_print("🎯 CLIENT STATUS UPDATE RECEIVED:")
        debug_print(f"   Status: {status}")
        debug_print(f"   Message: {message}")
        debug_print(f"   Timestamp: {timestamp}")
        debug_print(f"   Time: {time.strftime('%H:%M:%S', time.localtime(timestamp))}")
        
        # Check for additional data in status
        if 'display_info' in data:
            debug_print(f"   Display Info: {data['display_info']}")
        if 'error_details' in data:
            debug_print(f"   Error Details: {data['error_details']}")
        if 'command_result' in data:
            debug_print(f"   Command Result: {data['command_result']}")
        
        # Update client status
        if status == 'online':
            debug_print("✅ Client is ONLINE and ready!")
            self.client_label.setText("Client: Online")
            self.client_label.setStyleSheet("color: green; font-weight: bold;")
        elif status == 'error':
            debug_print("❌ Client reported an ERROR!")
            self.client_label.setText("Client: Error")
            self.client_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            debug_print(f"ℹ️ Client status: {status}")
            self.client_label.setText(f"Client: {status.title()}")
            self.client_label.setStyleSheet("color: blue; font-weight: bold;")
            
        # Add to status log
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        log_entry = f"[{time_str}] {status.upper()}: {message}"
        self.status_log.append(log_entry)
        
    def handle_heartbeat_received(self, data):
        """Handle heartbeat from client"""
        self.last_heartbeat = time.time()
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
            # Update monitors from client
            self.update_monitors_from_client(data['monitor_info'])
        
        self.heartbeat_label.setText(f"Last Heartbeat: {time_str}")
        debug_print("💓 Heartbeat processed successfully")
        
    def check_client_status(self):
        """Check if client is still alive based on heartbeat"""
        if self.last_heartbeat:
            time_since_heartbeat = time.time() - self.last_heartbeat
            if time_since_heartbeat > 60:  # No heartbeat for 1 minute
                debug_print(f"⚠️ CLIENT TIMEOUT! Last heartbeat was {time_since_heartbeat:.1f} seconds ago")
                self.client_label.setText("Client: Timeout")
                self.client_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            debug_print("⚠️ No heartbeat received yet from client")
                
    def browse_background_folder(self):
        """Browse for background folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Background Folder")
        if folder:
            self.bg_folder_edit.setText(folder)
            
    def open_display(self):
        """Send open display command"""
        data = {
            'action': 'open_display',
            'monitor_index': self.monitor_spin.value(),
            'background_folder': self.bg_folder_edit.text()
        }
        
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Open display command")
            # Tự động hiển thị WAIT(00) sau khi mở display
            QTimer.singleShot(1000, lambda: self.show_background("00"))
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def close_display(self):
        """Send close display command"""
        data = {'action': 'close_display'}
        
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Close display command")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def toggle_fullscreen(self):
        """Send toggle fullscreen command"""
        data = {'action': 'toggle_fullscreen'}
        
        if self.mqtt_handler.send_command('commands', data):
            # Chuyển đổi trạng thái hiển thị
            self.current_display_mode = 'fullscreen' if self.current_display_mode == 'windowed' else 'windowed'
            self.save_settings()  # Lưu cài đặt
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Toggle fullscreen command (now {self.current_display_mode})")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def switch_monitor(self):
        """Send switch monitor command và maintain current content"""
        data = {
            'action': 'switch_monitor',
            'monitor_index': self.monitor_spin.value(),
            'maintain_content': True
        }
        
        # Lưu thông tin hiển thị hiện tại để duy trì sau khi chuyển màn hình
        if hasattr(self, 'current_background') and self.current_background:
            data['current_background'] = self.current_background
            
        if hasattr(self, 'current_display_mode') and self.current_display_mode:
            data['current_display_mode'] = self.current_display_mode
            
        if hasattr(self, 'current_content_type') and self.current_content_type:
            data['current_content_type'] = self.current_content_type
            
        # Gửi lệnh chuyển màn hình với thông tin duy trì trạng thái
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Switch monitor command (maintaining content)")
            
            # Tự động áp dụng lại nội dung hiện tại sau khi chuyển màn hình
            QTimer.singleShot(1000, self.restore_current_display)  # Delay 1 giây để đảm bảo màn hình đã chuyển
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def restore_current_display(self):
        """Khôi phục lại nội dung hiển thị sau khi chuyển màn hình"""
        if not hasattr(self, 'current_content_type') or not self.current_content_type:
            return
            
        debug_print(f"🔄 Restoring display content: {self.current_content_type}")
        
        if self.current_content_type == 'background':
            # Hiển thị lại background hiện tại
            self.show_background(self.current_background)
        elif self.current_content_type == 'ranking':
            # Hiển thị lại bảng xếp hạng
            self.send_ranking()
        elif self.current_content_type == 'final':
            # Hiển thị lại kết quả chung cuộc
            self.send_final()
            
        # Khôi phục chế độ fullscreen nếu cần
        if hasattr(self, 'current_display_mode') and self.current_display_mode == 'fullscreen':
            QTimer.singleShot(500, self.restore_fullscreen)  # Delay thêm 0.5s
            
    def restore_fullscreen(self):
        """Khôi phục chế độ fullscreen"""
        debug_print("🖥️ Restoring fullscreen mode")
        data = {'action': 'toggle_fullscreen', 'force_fullscreen': True}
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Restore fullscreen mode")
            
    def show_background(self, bg_id):
        """Send show background command"""
        # Lưu background hiện tại và trạng thái hiển thị
        self.current_background = bg_id
        self.current_content_type = 'background'
        
        data = {
            'action': 'show_background',
            'background_id': bg_id
        }
        
        if self.mqtt_handler.send_command('display', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Show background {bg_id}")
            # Lưu cài đặt sau khi thay đổi
            self.save_settings()
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def apply_ranking(self):
        """Send ranking update command"""
        # Collect ranking data
        overlay_data = {'round': self.round_edit.text()}
        
        for rank in self.rank_edits:
            overlay_data[rank] = self.rank_edits[rank].text()
            
        # Collect positions
        positions = {}
        try:
            round_pos = self.round_pos_edit.text().split(',')
            positions['round'] = (int(round_pos[0]), int(round_pos[1]))
        except:
            positions['round'] = (1286, 917)
            
        for rank in self.rank_pos_edits:
            try:
                pos = self.rank_pos_edits[rank].text().split(',')
                positions[rank] = (int(pos[0]), int(pos[1]))
            except:
                positions[rank] = None
                
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
            # Cập nhật trạng thái hiển thị hiện tại
            self.current_content_type = 'ranking'
            self.save_settings()  # Lưu cài đặt
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Ranking update")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def send_ranking(self):
        """Alias for apply_ranking to maintain compatibility"""
        self.apply_ranking()
            
    def apply_final_results(self):
        """Send final results update command"""
        # Collect final results data
        overlay_data = {}
        for key in self.final_edits:
            overlay_data[key] = self.final_edits[key].text()
            
        # Collect positions
        positions = {}
        for key in self.final_pos_edits:
            try:
                pos = self.final_pos_edits[key].text().split(',')
                positions[key] = (int(pos[0]), int(pos[1]))
            except:
                positions[key] = None
                
        overlay_data['positions'] = positions
        
        # Font settings
        font_settings = {
            'font_name': self.rank_font_combo.currentText(),
            'font_size': self.final_font_size.value(),
            'color': self.rank_font_color.currentText()
        }
        overlay_data['font_settings'] = font_settings
        
        if self.mqtt_handler.send_command('final', overlay_data):
            # Cập nhật trạng thái hiển thị hiện tại
            self.current_content_type = 'final'
            self.save_settings()  # Lưu cài đặt
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Final results update")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def send_final(self):
        """Alias for apply_final_results to maintain compatibility"""
        self.apply_final_results()
            
    def clear_status_log(self):
        """Clear status log"""
        self.status_log.clear()
        
    def reconnect_mqtt(self):
        """Reconnect to MQTT broker"""
        debug_print("🔄 Attempting to reconnect MQTT...")
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
            time.sleep(1)
            success = self.mqtt_handler.connect()
            if success:
                debug_print("✅ MQTT reconnection successful!")
            else:
                debug_print("❌ MQTT reconnection failed!")
    
    def request_client_info(self):
        """Request detailed client information"""
        debug_print("🔍 Requesting client info...")
        data = {
            'action': 'debug_info',
            'request_type': 'client_info',
            'timestamp': time.time()
        }
        
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Request client info")
            self.debug_info.append(f"[{time.strftime('%H:%M:%S')}] Requested client information...")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
    
    def request_monitor_info(self):
        """Request monitor information from client"""
        debug_print("🖥️ Requesting monitor info...")
        data = {
            'action': 'debug_info',
            'request_type': 'monitor_info',
            'timestamp': time.time()
        }
        
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Request monitor info")
            self.debug_info.append(f"[{time.strftime('%H:%M:%S')}] Requested monitor information...")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
    
    def test_connection(self):
        """Test connection with client"""
        debug_print("🔍 Testing connection...")
        data = {
            'action': 'ping',
            'timestamp': time.time(),
            'message': 'Connection test from remote'
        }
        
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Connection test")
            self.debug_info.append(f"[{time.strftime('%H:%M:%S')}] Connection test sent...")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
    
    def generate_debug_report(self):
        """Generate comprehensive debug report"""
        debug_print("📄 Generating debug report...")
        
        report = []
        report.append("=" * 60)
        report.append("ScoShow Remote Control - Debug Report")
        report.append("=" * 60)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Connection Info
        report.append("🌐 Connection Information:")
        report.append(f"   MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        report.append(f"   Session ID: {UNIQUE_ID}")
        report.append(f"   Connected: {self.mqtt_handler.connected if self.mqtt_handler else False}")
        report.append(f"   Client Status: {self.client_status}")
        report.append("")
        
        # Monitor Info
        report.append("🖥️ Monitor Information:")
        for i, monitor in enumerate(self.available_monitors):
            report.append(f"   Monitor {i}: {monitor}")
        report.append("")
        
        # Heartbeat Info
        if self.last_heartbeat:
            last_hb = time.strftime('%H:%M:%S', time.localtime(self.last_heartbeat))
            time_since = time.time() - self.last_heartbeat
            report.append(f"💓 Last Heartbeat: {last_hb} ({time_since:.1f}s ago)")
        else:
            report.append("💓 No heartbeat received")
        report.append("")
        
        # MQTT Topics
        report.append("📡 MQTT Topics:")
        for topic_name, topic in MQTT_TOPICS.items():
            report.append(f"   {topic_name}: {topic}")
        report.append("")
        
        # Current Settings
        report.append("⚙️ Current Settings:")
        if hasattr(self, 'bg_folder_edit'):
            report.append(f"   Background Folder: {self.bg_folder_edit.text()}")
        if hasattr(self, 'monitor_combo'):
            report.append(f"   Selected Monitor: {self.monitor_combo.currentText()}")
        report.append(f"   Current Background: {self.current_background}")
        
        report_text = "\n".join(report)
        self.debug_info.setPlainText(report_text)
        
        debug_print("✅ Debug report generated")
        self.status_log.append(f"[{time.strftime('%H:%M:%S')}] Debug report generated")
    
    def export_debug_log(self):
        """Export debug log to file"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Debug Log", 
                f"scoshow_debug_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("ScoShow Remote Control - Debug Log Export\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    f.write("Status Log:\n")
                    f.write("-" * 20 + "\n")
                    f.write(self.status_log.toPlainText())
                    f.write("\n\n")
                    
                    f.write("Debug Information:\n")
                    f.write("-" * 20 + "\n")
                    f.write(self.debug_info.toPlainText())
                    
                debug_print(f"✅ Debug log exported to: {filename}")
                QMessageBox.information(self, "Export Complete", f"Debug log exported to:\n{filename}")
                
        except Exception as e:
            debug_print(f"❌ Failed to export debug log: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export debug log:\n{e}")
            
    def closeEvent(self, event):
        """Handle close event"""
        debug_print("🔴 Application closing...")
        if self.mqtt_handler:
            debug_print("🔌 Disconnecting MQTT...")
            self.mqtt_handler.disconnect()
        debug_print("👋 ScoShow Remote Control closed.")
        event.accept()

def main():
    """Main function"""
    print("🚀 Starting ScoShow Remote Control (Enhanced Debug Version)")
    print("Console logging is enabled for debugging MQTT communication")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    app.setApplicationName("ScoShow Remote Control")
    
    try:
        window = ScoShowRemoteControl()
        window.show()
        debug_print("🎯 Application window shown, ready for use!")
        sys.exit(app.exec_())
    except Exception as e:
        debug_print(f"❌ Application error: {e}")
        QMessageBox.critical(None, "Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
