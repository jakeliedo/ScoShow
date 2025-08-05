"""
ScoShow MQTT Remote Control - Remote Application
This runs on the remote computer for controlling the client display
"""

import sys
import json
import time
import os
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

class MQTTRemoteHandler(QObject):
    """Handle MQTT communication for remote control"""
    
    # Signals
    status_received = pyqtSignal(dict)
    heartbeat_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.client = mqtt.Client()
        self.connected = False
        
        # Setup MQTT client
        self.setup_mqtt()
        
    def setup_mqtt(self):
        """Setup MQTT client"""
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Set authentication if provided
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
    def connect(self):
        """Connect to MQTT broker"""
        try:
            print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
            self.connection_changed.emit(True)
            
            # Subscribe to status and heartbeat topics
            client.subscribe(MQTT_TOPICS['status'], MQTT_QOS)
            client.subscribe(MQTT_TOPICS['heartbeat'], MQTT_QOS)
            
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}")
            self.connected = False
            self.connection_changed.emit(False)
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        print("Disconnected from MQTT broker")
        self.connected = False
        self.connection_changed.emit(False)
        
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if topic == MQTT_TOPICS['status']:
                self.status_received.emit(payload)
            elif topic == MQTT_TOPICS['heartbeat']:
                self.heartbeat_received.emit(payload)
                
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def send_command(self, command_type, data):
        """Send command to client"""
        if not self.connected:
            return False
            
        topic = MQTT_TOPICS.get(command_type, MQTT_TOPICS['commands'])
        message = json.dumps(data)
        
        try:
            self.client.publish(topic, message, MQTT_QOS)
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

class ScoShowRemoteControl(QMainWindow):
    """Remote Control UI for ScoShow"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.mqtt_handler = None
        self.client_status = "Disconnected"
        self.last_heartbeat = None
        self.current_background = "00"  # Track current background
        self.config_file = "remote_config.json"  # Config file for settings
        
        # Setup window
        self.setup_window()
        
        # Setup variables
        self.setup_variables()
        
        # Load saved settings
        self.load_settings()
        
        # Setup UI
        self.setup_ui()
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Setup status check timer
        self.setup_status_timer()
        
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
        """Detect available monitors"""
        try:
            from screeninfo import get_monitors
            monitors = get_monitors()
            self.available_monitors = []
            for i, monitor in enumerate(monitors):
                monitor_name = f"Monitor {i+1} ({monitor.width}x{monitor.height})"
                self.available_monitors.append(monitor_name)
        except:
            self.available_monitors = ["Monitor 1 (Primary)"]
            
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
            self.connection_label.setText("MQTT: Connected")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_label.setText("MQTT: Disconnected")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
            
    def handle_status_received(self, data):
        """Handle status message from client"""
        status = data.get('status', 'unknown')
        message = data.get('message', '')
        timestamp = data.get('timestamp', time.time())
        
        # Update client status
        if status == 'online':
            self.client_label.setText("Client: Online")
            self.client_label.setStyleSheet("color: green; font-weight: bold;")
        elif status == 'error':
            self.client_label.setText("Client: Error")
            self.client_label.setStyleSheet("color: red; font-weight: bold;")
        else:
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
        self.heartbeat_label.setText(f"Last Heartbeat: {time_str}")
        
    def check_client_status(self):
        """Check if client is still alive based on heartbeat"""
        if self.last_heartbeat:
            time_since_heartbeat = time.time() - self.last_heartbeat
            if time_since_heartbeat > 60:  # No heartbeat for 1 minute
                self.client_label.setText("Client: Timeout")
                self.client_label.setStyleSheet("color: orange; font-weight: bold;")
                
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
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Toggle fullscreen command")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def switch_monitor(self):
        """Send switch monitor command và maintain current content"""
        data = {
            'action': 'switch_monitor',
            'monitor_index': self.monitor_spin.value(),
            'maintain_content': True
        }
        
        # Nếu có background đang hiển thị, gửi thông tin để duy trì
        if hasattr(self, 'current_background') and self.current_background:
            data['current_background'] = self.current_background
        
        if self.mqtt_handler.send_command('commands', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Switch monitor command")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def show_background(self, bg_id):
        """Send show background command"""
        # Lưu background hiện tại
        self.current_background = bg_id
        
        data = {
            'action': 'show_background',
            'background_id': bg_id
        }
        
        if self.mqtt_handler.send_command('display', data):
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Show background {bg_id}")
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
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Ranking update")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
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
            self.status_log.append(f"[{time.strftime('%H:%M:%S')}] SENT: Final results update")
        else:
            QMessageBox.warning(self, "Error", "Failed to send command - MQTT not connected")
            
    def clear_status_log(self):
        """Clear status log"""
        self.status_log.clear()
        
    def reconnect_mqtt(self):
        """Reconnect to MQTT broker"""
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
            time.sleep(1)
            self.mqtt_handler.connect()
            
    def closeEvent(self, event):
        """Handle close event"""
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
        event.accept()

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("ScoShow Remote Control")
    
    try:
        window = ScoShowRemoteControl()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
