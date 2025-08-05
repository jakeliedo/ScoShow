"""
MQTT Configuration for ScoShow Remote Control
"""

# MQTT Broker Settings
MQTT_BROKER = "localhost"  # Change to your MQTT broker IP/hostname
MQTT_PORT = 1883
MQTT_USERNAME = ""  # Optional: Set if your broker requires authentication
MQTT_PASSWORD = ""  # Optional: Set if your broker requires authentication

# MQTT Topics
MQTT_TOPICS = {
    'commands': 'scoshow/commands',
    'ranking': 'scoshow/ranking',
    'final': 'scoshow/final',
    'display': 'scoshow/display',
    'background': 'scoshow/background',
    'status': 'scoshow/status',
    'heartbeat': 'scoshow/heartbeat'
}

# QoS Level (0, 1, or 2)
MQTT_QOS = 1

# Keep Alive (seconds)
MQTT_KEEPALIVE = 60

# Reconnect settings
MQTT_RECONNECT_DELAY = 5
MQTT_MAX_RECONNECT_ATTEMPTS = 10
