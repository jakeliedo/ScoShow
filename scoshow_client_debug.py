"""
ScoShow MQTT Client - Display Application (Debug Version)
This runs on the client computer connected to the displays
Features enhanced console logging for debugging MQTT connection
"""

import sys
import os
import json
import threading
import time
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QSystemTrayIcon, QMenu, QAction, QMessageBox, QFileDialog, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtGui import QIcon
import paho.mqtt.client as mqtt
from main import TournamentDisplayWindow
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

# Try to allocate console for debug output when running as executable
def allocate_console():
    """Allocate console for debug output when running as executable"""
    try:
        if sys.platform == "win32" and hasattr(sys, '_MEIPASS'):
            import ctypes
            from ctypes import wintypes
            
            # Check if already have console
            if not hasattr(allocate_console, '_console_allocated'):
                # Allocate console
                ctypes.windll.kernel32.AllocConsole()
                
                # Redirect stdout and stderr to console
                import io
                sys.stdout = io.TextIOWrapper(
                    io.FileIO(ctypes.windll.kernel32.GetStdHandle(-11), 'w', closefd=False),
                    encoding='utf-8'
                )
                sys.stderr = io.TextIOWrapper(
                    io.FileIO(ctypes.windll.kernel32.GetStdHandle(-12), 'w', closefd=False),
                    encoding='utf-8'
                )
                
                allocate_console._console_allocated = True
                print("🖥️  Debug Console Allocated")
                return True
    except Exception as e:
        pass
    return False

def debug_print(message):
    """Enhanced debug print with timestamp and console allocation"""
    # Try to allocate console if we don't have one
    if hasattr(sys, '_MEIPASS') and not hasattr(debug_print, '_tried_console'):
        allocate_console()
        debug_print._tried_console = True
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    
    try:
        print(formatted_msg)
        if sys.stdout:
            sys.stdout.flush()
    except:
        pass
    
    logger.info(message)

# --- Single instance guard helpers ---
def ensure_single_instance(instance_key: str):
    """Ensure only one instance of this app runs.
    Returns a QLocalServer if this is the primary instance, otherwise None.
    """
    # Try to connect to an existing server
    socket = QLocalSocket()
    socket.connectToServer(instance_key)
    if socket.waitForConnected(150):
        # Another instance is running
        socket.close()
        return None

    # No instance is running (or stale server). Create a new server.
    server = QLocalServer()
    # Handle potential stale server names
    try:
        QLocalServer.removeServer(instance_key)
    except Exception:
        pass
    if not server.listen(instance_key):
        # As a last resort, try removing and listening again
        try:
            QLocalServer.removeServer(instance_key)
        except Exception:
            pass
        if not server.listen(instance_key):
            return None
    return server

class MQTTHandler(QObject):
    """Handle MQTT communication"""
    
    # Signals for UI updates
    command_received = pyqtSignal(str, dict)
    connection_changed = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        debug_print("🔧 Initializing MQTT Handler...")
        
        self.client = mqtt.Client()
        self.connected = False
        self.reconnect_attempts = 0
        
        # Setup MQTT client
        self.setup_mqtt()
        debug_print("✅ MQTT Handler initialized")
        
    def setup_mqtt(self):
        """Setup MQTT client"""
        debug_print("🔧 Setting up MQTT callbacks...")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        # Set authentication if provided
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            debug_print("🔐 MQTT authentication configured")
        else:
            debug_print("🔓 No MQTT authentication (using public broker)")
            
    def connect(self):
        """Connect to MQTT broker"""
        try:
            debug_print("🔄 Attempting to connect to MQTT broker...")
            debug_print(f"📡 Broker: {MQTT_BROKER}:{MQTT_PORT}")
            debug_print(f"🆔 Session ID: {UNIQUE_ID}")
            debug_print(f"🔐 Authentication: {'Yes' if MQTT_USERNAME else 'No'}")
            
            self.client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
            self.client.loop_start()
            debug_print("🚀 MQTT connection initiated...")
            return True
        except Exception as e:
            debug_print(f"❌ Failed to connect to MQTT broker: {e}")
            debug_print(f"💡 Check internet connection and firewall settings")
            return False
            
    def disconnect(self):
        """Disconnect from MQTT broker"""
        debug_print("🔌 Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            debug_print("✅ Successfully connected to MQTT broker!")
            debug_print(f"🔗 Connection details - Flags: {flags}, RC: {rc}")
            self.connected = True
            self.reconnect_attempts = 0
            self.connection_changed.emit(True)
            
            # Subscribe to all relevant topics
            debug_print("📥 Subscribing to MQTT topics...")
            # Subscribe base topics and their targeted/broadcast variants
            for key, base in MQTT_TOPICS.items():
                if key == 'status':
                    continue
                client.subscribe(base, MQTT_QOS)
                debug_print(f"   ✓ Subscribed to {base}")
            for base_key in ('commands', 'ranking', 'final', 'display', 'background'):
                t_key = f"{base_key}_targeted"
                b_key = f"{base_key}_broadcast"
                if t_key in MQTT_TOPICS:
                    client.subscribe(MQTT_TOPICS[t_key], MQTT_QOS)
                    debug_print(f"   ✓ Subscribed to {MQTT_TOPICS[t_key]}")
                if b_key in MQTT_TOPICS:
                    client.subscribe(MQTT_TOPICS[b_key], MQTT_QOS)
                    debug_print(f"   ✓ Subscribed to {MQTT_TOPICS[b_key]}")
                    
            # Send initial status
            debug_print("📤 Sending initial status...")
            self.send_status("online", "Client connected and ready")
            
        else:
            debug_print(f"❌ Failed to connect to MQTT broker!")
            debug_print(f"   Return code: {rc}")
            if rc == 1:
                debug_print("   Error: Connection refused - incorrect protocol version")
            elif rc == 2:
                debug_print("   Error: Connection refused - invalid client identifier")
            elif rc == 3:
                debug_print("   Error: Connection refused - server unavailable")
            elif rc == 4:
                debug_print("   Error: Connection refused - bad username or password")
            elif rc == 5:
                debug_print("   Error: Connection refused - not authorised")
            else:
                debug_print(f"   Error: Unknown error code {rc}")
            self.connected = False
            self.connection_changed.emit(False)
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        debug_print("🔌 Disconnected from MQTT broker")
        debug_print(f"   Disconnect reason code: {rc}")
        self.connected = False
        self.connection_changed.emit(False)
        
        # Auto-reconnect
        if self.reconnect_attempts < MQTT_MAX_RECONNECT_ATTEMPTS:
            self.reconnect_attempts += 1
            debug_print(f"🔄 Attempting to reconnect ({self.reconnect_attempts}/{MQTT_MAX_RECONNECT_ATTEMPTS})...")
            time.sleep(MQTT_RECONNECT_DELAY)
            self.connect()
        else:
            debug_print("❌ Max reconnection attempts reached. Giving up.")
            
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # If a target is specified, ensure it matches this client (or is broadcast)
            target = payload.get('target') if isinstance(payload, dict) else None
            if target and target not in (CLIENT_ID, 'all'):
                debug_print(f"🎯 Ignoring message for target '{target}' (this client: '{CLIENT_ID}')")
                return
            
            # Generate message ID for deduplication
            import hashlib
            message_content = str(payload) + str(topic)
            message_id = hashlib.md5(message_content.encode()).hexdigest()
            
            # Check if we've already processed this message recently
            current_time = time.time()
            topic_key = topic.split('/')[-1]  # Get the last part of topic
            
            if not hasattr(self, '_last_message_id'):
                self._last_message_id = {}
            
            if topic_key in self._last_message_id:
                last_id, last_time = self._last_message_id[topic_key]
                # If same message within 1 second, skip it
                if last_id == message_id and (current_time - last_time) < 1:
                    debug_print(f"⚠️ Skipping duplicate message for {topic_key}")
                    return
            
            # Update last message tracking
            self._last_message_id[topic_key] = (message_id, current_time)
            
            debug_print(f"📨 Received message on {topic}: {payload}")
            
            # Emit signal with command type and data
            # Normalize command topics (support base, targeted, and broadcast)
            base_commands = MQTT_TOPICS['commands']
            targeted = MQTT_TOPICS.get('commands_targeted')
            broadcast = MQTT_TOPICS.get('commands_broadcast')
            if topic in (base_commands, targeted, broadcast):
                self.command_received.emit('command', payload)
            elif topic in (MQTT_TOPICS['ranking'], MQTT_TOPICS.get('ranking_targeted'), MQTT_TOPICS.get('ranking_broadcast')):
                self.command_received.emit('ranking', payload)
            elif topic in (MQTT_TOPICS['final'], MQTT_TOPICS.get('final_targeted'), MQTT_TOPICS.get('final_broadcast')):
                self.command_received.emit('final', payload)
            elif topic in (MQTT_TOPICS['display'], MQTT_TOPICS.get('display_targeted'), MQTT_TOPICS.get('display_broadcast')):
                self.command_received.emit('display', payload)
            elif topic in (MQTT_TOPICS['background'], MQTT_TOPICS.get('background_targeted'), MQTT_TOPICS.get('background_broadcast')):
                self.command_received.emit('background', payload)
                
        except Exception as e:
            debug_print(f"❌ Error processing message: {e}")
            debug_print(f"   Raw message: {msg.payload}")
            debug_print(f"   Topic: {msg.topic}")
            
    def send_status(self, status, message=""):
        """Send status update"""
        if self.connected:
            data = {
                'status': status,
                'message': message,
                'timestamp': time.time(),
                'client_id': CLIENT_ID
            }
            self.client.publish(MQTT_TOPICS['status'], json.dumps(data), MQTT_QOS)
            debug_print(f"📤 Status sent: {status} - {message}")
        else:
            debug_print(f"⚠️  Cannot send status (not connected): {status} - {message}")
            
    def get_monitor_info(self):
        """Get monitor information for this client"""
        try:
            from screeninfo import get_monitors
            monitors = get_monitors()
            monitor_list = []
            for i, monitor in enumerate(monitors):
                monitor_info = f"Monitor {i+1} ({monitor.width}x{monitor.height})"
                if hasattr(monitor, 'name') and monitor.name:
                    monitor_info += f" - {monitor.name}"
                monitor_list.append(monitor_info)
            debug_print(f"🖥️ Detected {len(monitor_list)} monitors:")
            for i, info in enumerate(monitor_list):
                debug_print(f"   {i}: {info}")
            return monitor_list
        except Exception as e:
            debug_print(f"❌ Error detecting monitors: {e}")
            return ["Monitor 1 (Primary)"]
            
    def send_heartbeat(self):
        """Send heartbeat with additional info"""
        if self.connected:
            data = {
                'timestamp': time.time(),
                'client_id': 'scoshow_client',
                'monitor_info': self.get_monitor_info(),
                'display_status': 'closed' if not hasattr(self, 'display_window') or not self.display_window else 'open',
                'current_background': getattr(self, 'current_background', 'unknown'),
                'client_version': '1.0.0',
                'uptime': time.time() - getattr(self, 'start_time', time.time())
            }
            self.client.publish(MQTT_TOPICS['heartbeat'], json.dumps(data), MQTT_QOS)
            debug_print("💓 Enhanced heartbeat sent with monitor info")
        else:
            debug_print("⚠️  Cannot send heartbeat (not connected)")

class ScoShowClient(QMainWindow):
    """ScoShow Client Application - Display only"""
    
    def __init__(self):
        super().__init__()
        
        debug_print("🎯 ScoShow Client starting...")
        debug_print("=" * 50)
        
        # Initialize variables
        self.display_window = None
        
        # Auto-detect background folder
        debug_print("📂 Auto-detecting background folder...")
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller executable
            exe_dir = os.path.dirname(sys.executable)
            debug_print(f"🔧 Running as executable from: {exe_dir}")
        else:
            # Running as Python script
            exe_dir = os.path.dirname(os.path.abspath(__file__))
            debug_print(f"🔧 Running as script from: {exe_dir}")
        
        default_bg_folder = os.path.join(exe_dir, "background")
        debug_print(f"📁 Looking for background folder at: {default_bg_folder}")
        
        if os.path.exists(default_bg_folder):
            # Check if it has required files
            required_files = ["00", "01", "02"]
            valid_extensions = [".jpg", ".png", ".jpeg"]
            found_files = []
            
            for req_file in required_files:
                for ext in valid_extensions:
                    full_path = os.path.join(default_bg_folder, req_file + ext)
                    if os.path.exists(full_path):
                        found_files.append(req_file + ext)
                        break
            
            debug_print(f"📋 Found background files: {found_files}")
            
            if len(found_files) >= 3:
                self.background_folder = default_bg_folder
                debug_print(f"✅ Background folder auto-detected: {self.background_folder}")
            else:
                self.background_folder = ""
                debug_print(f"❌ Background folder incomplete (need 00, 01, 02 files)")
        else:
            self.background_folder = ""
            debug_print(f"❌ Background folder not found at: {default_bg_folder}")
        
        if not self.background_folder:
            debug_print("💡 You can manually select background folder later")
        
        self.current_mode = None
        self.current_background = "unknown"
        self.mqtt_handler = None
        self.start_time = time.time()  # Track start time for uptime
        self._opening_display = False  # Prevent multiple display openings
        self._last_message_id = {}  # Track last processed message for each topic
        
        # Setup UI
        self.setup_ui()

        # Setup system tray
        debug_print("🔧 Setting up system tray...")
        self.setup_tray()
        
        # Setup MQTT
        debug_print("🔧 Setting up MQTT connection...")
        self.setup_mqtt()
        
        # Setup heartbeat
        debug_print("💓 Setting up heartbeat timer...")
        self.setup_heartbeat()
        
        debug_print("✅ ScoShow Client initialization complete!")
        debug_print("=" * 50)
        
    def setup_ui(self):
        """Setup the main UI components"""
        self.setWindowTitle("ScoShow Client Debug")
        self.setGeometry(100, 100, 400, 200)

        # Create a central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Add a button to select background folder
        select_folder_button = QPushButton("Select Background Folder")
        select_folder_button.clicked.connect(self.select_background_folder)
        layout.addWidget(select_folder_button)

        # Set the layout to the central widget
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def setup_tray(self):
        """Setup system tray icon and menu"""
        debug_print("🔧 Creating system tray icon...")
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Status action (read-only)
        self.status_action = QAction("Status: Disconnected", self)
        self.status_action.setEnabled(False)
        tray_menu.addAction(self.status_action)
        
        tray_menu.addSeparator()
        
        # Add action to select background folder
        select_folder_action = QAction("Select Background Folder", self)
        select_folder_action.triggered.connect(self.select_background_folder)
        tray_menu.addAction(select_folder_action)
        
        # Show display action
        show_action = QAction("Show Display", self)
        show_action.triggered.connect(self.show_display)
        tray_menu.addAction(show_action)
        
        # Hide display action
        hide_action = QAction("Hide Display", self)
        hide_action.triggered.connect(self.hide_display)
        tray_menu.addAction(hide_action)
        
        # Toggle fullscreen action
        fullscreen_action = QAction("Toggle Fullscreen", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        tray_menu.addAction(fullscreen_action)
        
        tray_menu.addSeparator()
        
        # Reconnect action
        reconnect_action = QAction("Reconnect MQTT", self)
        reconnect_action.triggered.connect(self.reconnect_mqtt)
        tray_menu.addAction(reconnect_action)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        # Set menu and show tray icon
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("ScoShow Client")
        
        # Try to set icon, fallback to default if not available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        except:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        self.tray_icon.show()
        debug_print("✅ System tray icon created and shown")
        
    def setup_mqtt(self):
        """Setup MQTT handler"""
        self.mqtt_handler = MQTTHandler()
        self.mqtt_handler.command_received.connect(self.handle_mqtt_command)
        self.mqtt_handler.connection_changed.connect(self.handle_connection_change)
        
        # Connect to MQTT broker
        debug_print("🔄 Initiating MQTT connection...")
        success = self.mqtt_handler.connect()
        if success:
            debug_print("✅ MQTT connection setup complete")
        else:
            debug_print("❌ MQTT connection setup failed")
        
    def setup_heartbeat(self):
        """Setup heartbeat timer"""
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.send_heartbeat)
        self.heartbeat_timer.start(30000)  # Send heartbeat every 30 seconds
        debug_print("✅ Heartbeat timer started (30s interval)")
        
    def handle_connection_change(self, connected):
        """Handle MQTT connection status change"""
        if connected:
            debug_print("🔗 MQTT connection status: CONNECTED")
            self.status_action.setText("Status: Connected")
            self.tray_icon.setToolTip("ScoShow Client - Connected")
        else:
            debug_print("🔗 MQTT connection status: DISCONNECTED")
            self.status_action.setText("Status: Disconnected")
            self.tray_icon.setToolTip("ScoShow Client - Disconnected")
            
    def handle_mqtt_command(self, command_type, data):
        """Handle received MQTT commands"""
        try:
            debug_print(f"🎮 Processing command: {command_type}")
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
            debug_print(f"❌ Error handling command: {e}")
            if self.mqtt_handler:
                self.mqtt_handler.send_status("error", f"Command error: {e}")
            
    def handle_general_command(self, data):
        """Handle general commands"""
        action = data.get('action')
        debug_print(f"🎮 General command action: {action}")
        
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
            
        elif action == 'debug_info':
            self.handle_debug_request(data)
            
        elif action == 'ping':
            self.handle_ping_request(data)
            
    def handle_debug_request(self, data):
        """Handle debug information requests"""
        request_type = data.get('request_type', 'unknown')
        debug_print(f"🐛 Debug request: {request_type}")
        
        if request_type == 'client_info':
            self.send_client_info()
        elif request_type == 'monitor_info':
            self.send_monitor_info()
        else:
            debug_print(f"❓ Unknown debug request: {request_type}")
            
    def handle_ping_request(self, data):
        """Handle ping request"""
        debug_print("🏓 Ping request received")
        response_data = {
            'status': 'pong',
            'message': 'Connection test successful',
            'timestamp': time.time(),
            'request_timestamp': data.get('timestamp', 0),
            'response_time': time.time() - data.get('timestamp', 0)
        }
        
        if self.mqtt_handler:
            self.mqtt_handler.send_status("pong", "Connection test response")
            debug_print("🏓 Pong response sent")
            
    def send_client_info(self):
        """Send detailed client information"""
        debug_print("📋 Sending client info...")
        import platform
        import sys
        
        client_info = {
            'client_version': '1.0.0-debug',
            'python_version': sys.version,
            'platform': platform.platform(),
            'hostname': platform.node(),
            'processor': platform.processor(),
            'uptime': time.time() - self.start_time,
            'display_status': 'open' if self.display_window else 'closed',
            'current_background': self.current_background,
            'background_folder': self.background_folder,
            'timestamp': time.time()
        }
        
        if self.mqtt_handler:
            self.mqtt_handler.send_status("client_info", f"Client info: {client_info}")
            debug_print("📋 Client info sent")
            
    def send_monitor_info(self):
        """Send monitor information"""
        debug_print("🖥️ Sending monitor info...")
        monitor_info = self.mqtt_handler.get_monitor_info() if self.mqtt_handler else ["Monitor 1 (Primary)"]
        
        if self.mqtt_handler:
            self.mqtt_handler.send_status("monitor_info", f"Monitors: {monitor_info}")
            debug_print(f"🖥️ Monitor info sent: {monitor_info}")
            
    def handle_ranking_command(self, data):
        """Handle ranking update commands"""
        debug_print(f"📊 Ranking command received: {data}")
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
        debug_print(f"🏆 Final results command received: {data}")
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
        debug_print(f"🖥️  Display command action: {action}")
        
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
        debug_print(f"📁 Background folder command: {folder_path}")
        if folder_path and os.path.exists(folder_path):
            self.background_folder = folder_path
            self.mqtt_handler.send_status("success", f"Background folder set to: {folder_path}")
        else:
            self.mqtt_handler.send_status("error", "Invalid background folder path")
            
    def open_display(self, monitor_index=0, background_folder=""):
        """Open display window"""
        debug_print(f"🖥️  Opening display on monitor {monitor_index + 1}")
        # Debounce rapid duplicate open requests
        now = time.time()
        if not hasattr(self, '_last_open_time'):
            self._last_open_time = 0
        if now - getattr(self, '_last_open_time', 0) < 0.8:
            debug_print("⚠️ Ignoring rapid duplicate open_display request")
            return
        self._last_open_time = now

        # Prevent opening multiple displays at the same time
        if hasattr(self, '_opening_display') and self._opening_display:
            debug_print("⚠️ Display window is already being opened")
            return
            
        self._opening_display = True
        
        try:
            if background_folder:
                self.background_folder = background_folder
                
            if not self.background_folder:
                self.mqtt_handler.send_status("error", "No background folder specified")
                return
                
            # If there's an existing window already open on the same monitor, reuse it
            if self.display_window and self.display_window.isVisible() and getattr(self, 'current_monitor_index', None) == monitor_index:
                debug_print("🔁 Reusing existing display window on the same monitor")
                # Reload background folder if changed
                if self.display_window.load_background_folder(self.background_folder):
                    self.mqtt_handler.send_status("success", f"Display already open on monitor {monitor_index + 1}")
                else:
                    self.mqtt_handler.send_status("error", "Failed to load background folder")
                return
            
            # Close existing display if different monitor or invisible
            if self.display_window:
                debug_print("🔄 Closing existing display window")
                try:
                    self.display_window.close()
                except Exception:
                    pass
                self.display_window = None
                
            # Create new display
            debug_print(f"🆕 Creating new display window on monitor {monitor_index}")
            self.display_window = TournamentDisplayWindow(monitor_index)
            self.current_monitor_index = monitor_index
            
            if self.display_window.load_background_folder(self.background_folder):
                self.display_window.show()
                self.mqtt_handler.send_status("success", f"Display opened on monitor {monitor_index + 1}")
                debug_print(f"✅ Display window opened successfully")
            else:
                self.mqtt_handler.send_status("error", "Failed to load background folder")
                debug_print(f"❌ Failed to load background folder")
                
        finally:
            self._opening_display = False
            
    def close_display(self):
        """Close display window"""
        debug_print("🖥️  Closing display window")
        if self.display_window:
            self.display_window.close()
            self.display_window = None
            self.current_mode = None
            self.mqtt_handler.send_status("success", "Display closed")
            debug_print("✅ Display window closed")
        else:
            self.mqtt_handler.send_status("info", "No display window open")
            debug_print("ℹ️  No display window to close")
            
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        debug_print("🖥️  Toggling fullscreen mode")
        if self.display_window:
            self.display_window.toggle_fullscreen()
            state = "fullscreen" if self.display_window.is_fullscreen else "windowed"
            self.mqtt_handler.send_status("success", f"Display switched to {state} mode")
            debug_print(f"✅ Display switched to {state} mode")
        else:
            self.mqtt_handler.send_status("error", "No display window open")
            debug_print("❌ No display window to toggle")
            
    def switch_monitor(self, monitor_index):
        """Switch to different monitor"""
        debug_print(f"🖥️  Switching to monitor {monitor_index + 1}")
        if self.display_window:
            background_folder = self.background_folder
            self.close_display()
            self.open_display(monitor_index, background_folder)
        else:
            self.mqtt_handler.send_status("error", "No display window open")
            debug_print("❌ No display window to switch")
            
    def show_display(self):
        """Show display window (for manual control)"""
        debug_print("👁️  Showing display window")
        if self.display_window:
            self.display_window.show()
            self.display_window.raise_()
            self.display_window.activateWindow()
            debug_print("✅ Display window shown")
        else:
            self.mqtt_handler.send_status("info", "No display window to show")
            debug_print("ℹ️  No display window to show")
            
    def hide_display(self):
        """Hide display window"""
        debug_print("🙈 Hiding display window")
        if self.display_window:
            self.display_window.hide()
            debug_print("✅ Display window hidden")
        else:
            debug_print("ℹ️  No display window to hide")
            
    def send_heartbeat(self):
        """Send heartbeat to remote"""
        if self.mqtt_handler:
            self.mqtt_handler.send_heartbeat()
            
    def reconnect_mqtt(self):
        """Reconnect to MQTT broker"""
        debug_print("🔄 Manual MQTT reconnection requested")
        if self.mqtt_handler:
            self.mqtt_handler.disconnect()
            time.sleep(1)
            success = self.mqtt_handler.connect()
            if success:
                debug_print("✅ Manual reconnection initiated")
            else:
                debug_print("❌ Manual reconnection failed")
            
    def quit_application(self):
        """Quit the application"""
        debug_print("🚪 Shutting down ScoShow Client...")
        if self.mqtt_handler:
            self.mqtt_handler.send_status("offline", "Client shutting down")
            self.mqtt_handler.disconnect()
            
        if self.display_window:
            self.display_window.close()
            
        debug_print("👋 Goodbye!")
        QApplication.quit()
        
    def closeEvent(self, event):
        """Handle close event"""
        event.ignore()  # Don't close, just hide
        self.hide()

    def select_background_folder(self):
        """Open dialog to select background folder"""
        while True:
            folder = QFileDialog.getExistingDirectory(self, "Select Background Folder")
            if folder:
                # Check if the folder contains at least 3 valid image files with specific names
                required_files = ["00", "01", "02"]
                valid_extensions = [".jpg", ".png", ".jpeg"]
                valid_files = [f for f in required_files if any(os.path.exists(os.path.join(folder, f + ext)) for ext in valid_extensions)]

                if len(valid_files) == 3:
                    self.background_folder = folder
                    debug_print(f"📂 Background folder selected: {self.background_folder}")
                    QMessageBox.information(self, "Success", "Library Set!")
                    self.resize(200, 100)  # Shrink the window size
                    break
                else:
                    QMessageBox.warning(self, "Invalid Folder", "The selected folder must contain at least 3 image files named 00, 01, and 02 with valid extensions (.jpg, .png, .jpeg). Please select again.")
            else:
                break

def main():
    """Main function"""
    print("🚀 Starting ScoShow Client (Debug Version)")
    print("Console logging is enabled for debugging")
    print("=" * 50)
    
    debug_print(f"🚀 Starting ScoShow Client Debug with Session ID: {UNIQUE_ID}")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # Single instance guard (process-level)
    instance_key = f"ScoShowClient_{UNIQUE_ID}"
    server = ensure_single_instance(instance_key)
    if server is None:
        debug_print("⚠️ Another ScoShow Client instance is already running. Exiting.")
        # Optional notice to the user
        QMessageBox.information(None, "ScoShow Client", "Another ScoShow Client instance is already running.")
        return 0
    
    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        debug_print("❌ System tray is not available on this system.")
        QMessageBox.critical(None, "ScoShow Client", 
                           "System tray is not available on this system.")
        sys.exit(1)
    
    try:
        client = ScoShowClient()
        client.show()  # Ensure the main window is displayed
        debug_print("🎯 Starting main application loop...")
        exit_code = app.exec_()
        # Keep server alive for the duration; then close on exit
        server.close()
        sys.exit(exit_code)
    except Exception as e:
        debug_print(f"💥 Application error: {e}")
        QMessageBox.critical(None, "Error", f"Application error: {e}")

if __name__ == "__main__":
    main()
