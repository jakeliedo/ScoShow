"""
ScoShow MQTT Client - Tích hợp điều khiển từ xa qua MQTT
Hỗ trợ điều khiển từ màn hình DMG80480C050_03WTC thông qua ESP32-C3
"""

import sys
import os
import json
import time
from threading import Thread
import paho.mqtt.client as mqtt
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox

# Import ScoShow modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import TournamentControlPanel, TournamentDisplayWindow

class MQTTScoShowController(QObject):
    """
    Controller kết hợp MQTT với ScoShow
    Nhận lệnh từ màn hình cảm ứng qua MQTT và điều khiển ScoShow
    """
    
    # Signals for UI updates
    status_changed = pyqtSignal(str)
    connection_changed = pyqtSignal(bool)
    command_received = pyqtSignal(str, dict)
    
    def __init__(self, scoshow_panel):
        super().__init__()
        self.scoshow_panel = scoshow_panel
        self.mqtt_client = None
        self.is_connected = False
        
        # MQTT Configuration
        self.mqtt_config = {
            'broker': 'localhost',
            'port': 1883,
            'username': '',
            'password': '',
            'client_id': 'scoshow_main',
            'topics': {
                'commands': 'scoshow/commands',
                'status': 'scoshow/status',
                'display': 'scoshow/display',
                'ranking': 'scoshow/ranking',
                'final': 'scoshow/final'
            }
        }
        
        # Load MQTT config
        self.load_mqtt_config()
        
        # Initialize MQTT
        self.setup_mqtt()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.publish_status)
        self.status_timer.start(5000)  # Every 5 seconds
        
    def load_mqtt_config(self):
        """Load MQTT configuration"""
        config_file = "mqtt_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.mqtt_config.update(config)
            except Exception as e:
                print(f"Error loading MQTT config: {e}")
                
    def save_mqtt_config(self):
        """Save MQTT configuration"""
        try:
            with open("mqtt_config.json", 'w', encoding='utf-8') as f:
                json.dump(self.mqtt_config, f, indent=2)
        except Exception as e:
            print(f"Error saving MQTT config: {e}")
            
    def setup_mqtt(self):
        """Setup MQTT client"""
        try:
            self.mqtt_client = mqtt.Client(self.mqtt_config['client_id'])
            
            # Set credentials if provided
            if self.mqtt_config['username']:
                self.mqtt_client.username_pw_set(
                    self.mqtt_config['username'], 
                    self.mqtt_config['password']
                )
            
            # Set callbacks
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            self.mqtt_client.on_message = self.on_mqtt_message
            
            # Connect
            self.connect_mqtt()
            
        except Exception as e:
            self.status_changed.emit(f"MQTT Setup Error: {e}")
            
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client.connect(
                self.mqtt_config['broker'], 
                self.mqtt_config['port'], 
                60
            )
            self.mqtt_client.loop_start()
        except Exception as e:
            self.status_changed.emit(f"MQTT Connection Error: {e}")
            
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            self.connection_changed.emit(True)
            self.status_changed.emit("MQTT Connected")
            
            # Subscribe to command topics
            for topic_name, topic in self.mqtt_config['topics'].items():
                if topic_name != 'status':  # Don't subscribe to status topic
                    client.subscribe(topic)
                    print(f"Subscribed to: {topic}")
                    
        else:
            self.is_connected = False
            self.connection_changed.emit(False)
            self.status_changed.emit(f"MQTT Connection Failed: {rc}")
            
    def on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        self.connection_changed.emit(False)
        self.status_changed.emit("MQTT Disconnected")
        
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            print(f"Received: {topic} -> {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except:
                data = {'raw': payload}
                
            # Process commands based on topic
            if topic == self.mqtt_config['topics']['commands']:
                self.handle_command(data)
            elif topic == self.mqtt_config['topics']['display']:
                self.handle_display_command(data)
            elif topic == self.mqtt_config['topics']['ranking']:
                self.handle_ranking_command(data)
            elif topic == self.mqtt_config['topics']['final']:
                self.handle_final_command(data)
                
            self.command_received.emit(topic, data)
            
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
            
    def handle_command(self, data):
        """Handle general commands"""
        command = data.get('command', '')
        
        if command == 'open_display':
            monitor = data.get('monitor', 0)
            if hasattr(self.scoshow_panel, 'monitor_combo'):
                self.scoshow_panel.monitor_combo.setCurrentIndex(monitor)
            self.scoshow_panel.open_display()
            
        elif command == 'close_display':
            self.scoshow_panel.close_display()
            
        elif command == 'switch_monitor':
            self.scoshow_panel.switch_monitor()
            
        elif command == 'toggle_fullscreen':
            self.scoshow_panel.toggle_display_fullscreen()
            
        elif command == 'select_background':
            folder = data.get('folder', '')
            if folder and os.path.exists(folder):
                self.scoshow_panel.background_folder = folder
                # Update UI status
                
    def handle_display_command(self, data):
        """Handle display commands"""
        bg_id = data.get('background', '00')
        self.scoshow_panel.show_background(bg_id)
        
    def handle_ranking_command(self, data):
        """Handle ranking update commands"""
        # Update ranking fields
        if hasattr(self.scoshow_panel, 'round_edit'):
            round_val = data.get('round', '')
            if round_val:
                self.scoshow_panel.round_edit.setText(str(round_val))
                
        # Update rank values
        for rank in ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']:
            if rank in data and hasattr(self.scoshow_panel, 'rank_edits'):
                if rank in self.scoshow_panel.rank_edits:
                    self.scoshow_panel.rank_edits[rank].setText(data[rank])
                    
        # Apply ranking
        if data.get('apply', False):
            self.scoshow_panel.apply_ranking(show_popup=False)
            
    def handle_final_command(self, data):
        """Handle final results commands"""
        # Update final results fields
        for key in ['winner', 'second', 'third', 'fourth', 'fifth']:
            if key in data and hasattr(self.scoshow_panel, 'final_edits'):
                if key in self.scoshow_panel.final_edits:
                    self.scoshow_panel.final_edits[key].setText(data[key])
                    
        # Apply final results
        if data.get('apply', False):
            self.scoshow_panel.apply_final_results(show_popup=False)
            
    def publish_status(self):
        """Publish current status to MQTT"""
        if not self.is_connected:
            return
            
        try:
            status = {
                'timestamp': time.time(),
                'display_open': self.scoshow_panel.display_window is not None,
                'current_mode': self.scoshow_panel.current_mode,
                'background_folder': self.scoshow_panel.background_folder,
                'selected_monitor': self.scoshow_panel.monitor_combo.currentIndex() if hasattr(self.scoshow_panel, 'monitor_combo') else 0
            }
            
            # Add display status if window exists
            if self.scoshow_panel.display_window:
                status['fullscreen'] = self.scoshow_panel.display_window.is_fullscreen
                
            self.mqtt_client.publish(
                self.mqtt_config['topics']['status'],
                json.dumps(status),
                retain=True
            )
            
        except Exception as e:
            print(f"Error publishing status: {e}")
            
    def publish_command_response(self, command, success, message=""):
        """Publish command response"""
        if not self.is_connected:
            return
            
        try:
            response = {
                'timestamp': time.time(),
                'command': command,
                'success': success,
                'message': message
            }
            
            self.mqtt_client.publish(
                f"{self.mqtt_config['topics']['commands']}/response",
                json.dumps(response)
            )
            
        except Exception as e:
            print(f"Error publishing command response: {e}")
            
    def disconnect(self):
        """Disconnect MQTT"""
        if self.mqtt_client and self.is_connected:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()


class MQTTScoShowPanel(TournamentControlPanel):
    """
    Extended ScoShow Panel with MQTT support
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize MQTT controller
        self.mqtt_controller = MQTTScoShowController(self)
        
        # Connect signals
        self.mqtt_controller.status_changed.connect(self.update_mqtt_status)
        self.mqtt_controller.connection_changed.connect(self.update_mqtt_connection)
        
        # Add MQTT status to UI
        self.setup_mqtt_ui()
        
    def setup_mqtt_ui(self):
        """Add MQTT status to existing UI"""
        # Update status label to show MQTT status
        if hasattr(self, 'status_label'):
            self.status_label.setText("Starting MQTT...")
            
    def update_mqtt_status(self, status):
        """Update MQTT status in UI"""
        if hasattr(self, 'status_label'):
            current_text = self.status_label.text()
            if "MQTT" not in current_text:
                self.status_label.setText(f"{current_text} | MQTT: {status}")
            else:
                # Replace MQTT part
                parts = current_text.split(" | ")
                non_mqtt_parts = [p for p in parts if not p.startswith("MQTT")]
                new_text = " | ".join(non_mqtt_parts + [f"MQTT: {status}"])
                self.status_label.setText(new_text)
                
    def update_mqtt_connection(self, connected):
        """Update connection status"""
        color = "#27AE60" if connected else "#E74C3C"
        if hasattr(self, 'status_label'):
            self.status_label.setStyleSheet(f"color: {color};")
            
    def closeEvent(self, event):
        """Handle application close"""
        # Disconnect MQTT
        if hasattr(self, 'mqtt_controller'):
            self.mqtt_controller.disconnect()
            
        # Call parent close event
        super().closeEvent(event)


def main():
    """Main function with MQTT support"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setApplicationName("ScoShow MQTT")
    app.setOrganizationName("Tournament Display")
    
    try:
        window = MQTTScoShowPanel()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
