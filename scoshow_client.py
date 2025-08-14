"""
ScoShow MQTT Client - Display Application
This runs on the client computer connected to the displays
"""

import sys
import os
import json
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon
import paho.mqtt.client as mqtt
from main import TournamentDisplayWindow
from mqtt_config import *

class MQTTHandler(QObject):
    """Handle MQTT communication"""
    
    # Signals for UI updates
    command_received = pyqtSignal(str, dict)
    connection_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.client = mqtt.Client()
        self.connected = False
        self.reconnect_attempts = 0
        
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
            self.reconnect_attempts = 0
            self.connection_changed.emit(True)
            
            # Subscribe to all relevant topics
            for topic_name, topic in MQTT_TOPICS.items():
                if topic_name != 'status':  # Don't subscribe to status (we publish to it)
                    client.subscribe(topic, MQTT_QOS)
                    print(f"Subscribed to {topic}")
                    
            # Send initial status
            self.send_status("online", "Client connected and ready")
            
        else:
            print(f"Failed to connect to MQTT broker, return code {rc}")
            self.connected = False
            self.connection_changed.emit(False)
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        print("Disconnected from MQTT broker")
        self.connected = False
        self.connection_changed.emit(False)
        
        # Auto-reconnect
        if self.reconnect_attempts < MQTT_MAX_RECONNECT_ATTEMPTS:
            self.reconnect_attempts += 1
            print(f"Attempting to reconnect ({self.reconnect_attempts}/{MQTT_MAX_RECONNECT_ATTEMPTS})...")
            time.sleep(MQTT_RECONNECT_DELAY)
            self.connect()
            
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            print(f"Received message on {topic}: {payload}")
            
            # Emit signal with command type and data
            if topic == MQTT_TOPICS['commands']:
                self.command_received.emit('command', payload)
            elif topic == MQTT_TOPICS['ranking']:
                self.command_received.emit('ranking', payload)
            elif topic == MQTT_TOPICS['final']:
                self.command_received.emit('final', payload)
            elif topic == MQTT_TOPICS['display']:
                self.command_received.emit('display', payload)
            elif topic == MQTT_TOPICS['background']:
                self.command_received.emit('background', payload)
                
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def send_status(self, status, message=""):
        """Send status update"""
        if self.connected:
            data = {
                'status': status,
                'message': message,
                'timestamp': time.time()
            }
            self.client.publish(MQTT_TOPICS['status'], json.dumps(data), MQTT_QOS)
            
    def send_heartbeat(self):
        """Send heartbeat"""
        if self.connected:
            data = {
                'timestamp': time.time(),
                'client_id': 'scoshow_client'
            }
            self.client.publish(MQTT_TOPICS['heartbeat'], json.dumps(data), MQTT_QOS)

class ScoShowClient(QMainWindow):
    """ScoShow Client Application - Display only"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize variables
        self.display_window = None
        # Set default background folder to 'background' folder in same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_bg_folder = os.path.join(script_dir, "background")
        self.background_folder = default_bg_folder if os.path.exists(default_bg_folder) else ""
        self.current_mode = None
        self.mqtt_handler = None
        
        # Setup system tray
        self.setup_tray()
        
        # Setup MQTT
        self.setup_mqtt()
        
        # Setup heartbeat timer
        self.setup_heartbeat()
        
        # Hide main window (run in background)
        self.hide()
        
    def setup_tray(self):
        """Setup system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        self.status_action = QAction("Status: Disconnected", self)
        self.status_action.setEnabled(False)
        tray_menu.addAction(self.status_action)
        
        tray_menu.addSeparator()
        
        show_action = QAction("Show Display", self)
        show_action.triggered.connect(self.show_display)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide Display", self)
        hide_action.triggered.connect(self.hide_display)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        reconnect_action = QAction("Reconnect MQTT", self)
        reconnect_action.triggered.connect(self.reconnect_mqtt)
        tray_menu.addAction(reconnect_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Set icon (you can replace with your own icon)
        self.tray_icon.setToolTip("ScoShow Client")
        
    def setup_mqtt(self):
        """Setup MQTT handler"""
        self.mqtt_handler = MQTTHandler()
        self.mqtt_handler.command_received.connect(self.handle_mqtt_command)
        self.mqtt_handler.connection_changed.connect(self.handle_connection_change)
        
        # Connect to MQTT broker
        self.mqtt_handler.connect()
        
    def setup_heartbeat(self):
        """Setup heartbeat timer"""
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        self.heartbeat_timer.start(30000)  # Send heartbeat every 30 seconds
        
    def handle_connection_change(self, connected):
        """Handle MQTT connection status change"""
        if connected:
            self.status_action.setText("Status: Connected")
            self.tray_icon.setToolTip("ScoShow Client - Connected")
        else:
            self.status_action.setText("Status: Disconnected")
            self.tray_icon.setToolTip("ScoShow Client - Disconnected")
            
    def handle_mqtt_command(self, command_type, data):
        """Handle received MQTT commands"""
        try:
            if command_type == 'command':
                self.handle_general_command(data)
            elif command_type == 'ranking':
                self.handle_ranking_command(data)
            elif command_type == 'final':
                self.handle_final_command(data)
            elif command_type == 'display':
                self.handle_display_command(data)
            elif command_type == 'background':
                self.handle_background_command(data)
                
        except Exception as e:
            print(f"Error handling command: {e}")
            self.mqtt_handler.send_status("error", f"Command error: {e}")
            
    def handle_general_command(self, data):
        """Handle general commands"""
        action = data.get('action')
        
        if action == 'open_display':
            monitor_index = data.get('monitor_index', 0)
            background_folder = data.get('background_folder', '')
            self.open_display(monitor_index, background_folder)
            
        elif action == 'close_display':
            self.close_display()
            
        elif action == 'toggle_fullscreen':
            self.toggle_fullscreen()
            
        elif action == 'switch_monitor':
            monitor_index = data.get('monitor_index', 0)
            self.switch_monitor(monitor_index)
            
    def handle_ranking_command(self, data):
        """Handle ranking update commands"""
        if not self.display_window:
            self.mqtt_handler.send_status("error", "Display window not open")
            return
            
        # Apply ranking data
        success = self.display_window.show_background("01", data)
        if success:
            self.current_mode = "01"
            self.mqtt_handler.send_status("success", "Ranking updated")
        else:
            self.mqtt_handler.send_status("error", "Failed to update ranking")
            
    def handle_final_command(self, data):
        """Handle final results commands"""
        if not self.display_window:
            self.mqtt_handler.send_status("error", "Display window not open")
            return
            
        # Apply final results data
        success = self.display_window.show_background("02", data)
        if success:
            self.current_mode = "02"
            self.mqtt_handler.send_status("success", "Final results updated")
        else:
            self.mqtt_handler.send_status("error", "Failed to update final results")
            
    def handle_display_command(self, data):
        """Handle display control commands"""
        action = data.get('action')
        
        if action == 'show_background':
            bg_id = data.get('background_id')
            if bg_id and self.display_window:
                success = self.display_window.show_background(bg_id)
                if success:
                    self.current_mode = bg_id
                    self.mqtt_handler.send_status("success", f"Background {bg_id} displayed")
                else:
                    self.mqtt_handler.send_status("error", f"Failed to show background {bg_id}")
                    
    def handle_background_command(self, data):
        """Handle background folder commands"""
        folder_path = data.get('folder_path')
        if folder_path and os.path.exists(folder_path):
            self.background_folder = folder_path
            self.mqtt_handler.send_status("success", f"Background folder set to: {folder_path}")
        else:
            self.mqtt_handler.send_status("error", "Invalid background folder path")
            
    def open_display(self, monitor_index=0, background_folder=""):
        """Open display window"""
        if background_folder:
            self.background_folder = background_folder
            
        if not self.background_folder:
            self.mqtt_handler.send_status("error", "No background folder specified")
            return
            
        # Close existing display
        if self.display_window:
            self.display_window.close()
            
        # Create new display
        self.display_window = TournamentDisplayWindow(monitor_index)
        
        if self.display_window.load_background_folder(self.background_folder):
            self.display_window.show()
            self.mqtt_handler.send_status("success", f"Display opened on monitor {monitor_index + 1}")
        else:
            self.mqtt_handler.send_status("error", "Failed to load background folder")
            
    def close_display(self):
        """Close display window"""
        if self.display_window:
            self.display_window.close()
            self.display_window = None
            self.current_mode = None
            self.mqtt_handler.send_status("success", "Display closed")
        else:
            self.mqtt_handler.send_status("info", "No display window open")
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.display_window:
            self.display_window.toggle_fullscreen()
            state = "fullscreen" if self.display_window.is_fullscreen else "windowed"
            self.mqtt_handler.send_status("success", f"Display switched to {state} mode")
        else:
            self.mqtt_handler.send_status("error", "No display window open")
            
    def switch_monitor(self, monitor_index):
        """Switch to different monitor"""
        if self.display_window:
            background_folder = self.background_folder
            self.close_display()
            self.open_display(monitor_index, background_folder)
        else:
            self.mqtt_handler.send_status("error", "No display window open")
            
    def show_display(self):
        """Show display window (for manual control)"""
        if self.display_window:
            self.display_window.show()
            self.display_window.raise_()
            self.display_window.activateWindow()
        else:
            self.mqtt_handler.send_status("info", "No display window to show")
            
    def hide_display(self):
        """Hide display window"""
        if self.display_window:
            self.display_window.hide()
            
    def send_heartbeat(self):
        """Send heartbeat to remote"""
        if self.mqtt_handler:
            self.mqtt_handler.send_heartbeat()
            
    def reconnect_mqtt(self):
        """Reconnect to MQTT broker"""
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
            time.sleep(1)
            self.mqtt_handler.connect()
            
    def quit_application(self):
        """Quit the application"""
        if self.mqtt_handler:
            self.mqtt_handler.send_status("offline", "Client shutting down")
            self.mqtt_handler.disconnect()
            
        if self.display_window:
            self.display_window.close()
            
        QApplication.quit()
        
    def closeEvent(self, event):
        """Handle close event"""
        event.ignore()  # Don't close, just hide
        self.hide()

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
    
    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "ScoShow Client", 
                           "System tray is not available on this system.")
        sys.exit(1)
    
    try:
        client = ScoShowClient()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
