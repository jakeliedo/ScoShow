import logging

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Add debug logs in MQTTRemoteHandler methods
class MQTTRemoteHandler(QObject):
    def setup_mqtt(self):
        logging.debug("Setting up MQTT client")
        # ...existing code...

    def connect(self):
        logging.debug(f"Attempting to connect to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        # ...existing code...

    def on_connect(self, client, userdata, flags, rc):
        logging.debug(f"MQTT on_connect called with return code: {rc}")
        # ...existing code...

    def on_disconnect(self, client, userdata, rc):
        logging.debug("MQTT on_disconnect called")
        # ...existing code...

    def on_message(self, client, userdata, msg):
        logging.debug(f"MQTT message received on topic: {msg.topic} with payload: {msg.payload}")
        # ...existing code...

    def send_command(self, command_type, data):
        logging.debug(f"Sending command: {command_type} with data: {data}")
        # ...existing code...

# Add debug logs in ScoShowRemoteControl methods
class ScoShowRemoteControl(QMainWindow):
    def setup_mqtt(self):
        logging.debug("Setting up MQTT handler")
        # ...existing code...

    def handle_connection_changed(self, connected):
        logging.debug(f"MQTT connection status changed: {'Connected' if connected else 'Disconnected'}")
        # ...existing code...

    def handle_status_received(self, data):
        logging.debug(f"Status received: {data}")
        # ...existing code...

    def handle_heartbeat_received(self, data):
        logging.debug(f"Heartbeat received: {data}")
        # ...existing code...

    def check_client_status(self):
        logging.debug("Checking client status based on last heartbeat")
        # ...existing code...

    def browse_background_folder(self):
        logging.debug("Browsing for background folder")
        # ...existing code...

    def open_display(self):
        logging.debug("Sending open display command")
        # ...existing code...

    def close_display(self):
        logging.debug("Sending close display command")
        # ...existing code...

    def toggle_fullscreen(self):
        logging.debug("Sending toggle fullscreen command")
        # ...existing code...

    def switch_monitor(self):
        logging.debug("Sending switch monitor command")
        # ...existing code...

    def show_background(self, bg_id):
        logging.debug(f"Sending show background command for background ID: {bg_id}")
        # ...existing code...

    def apply_ranking(self):
        logging.debug("Applying ranking updates")
        # ...existing code...

    def apply_final_results(self):
        logging.debug("Applying final results updates")
        # ...existing code...

    def reconnect_mqtt(self):
        logging.debug("Reconnecting to MQTT broker")
        # ...existing code...