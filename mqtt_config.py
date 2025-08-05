"""
MQTT Configuration for ScoShow Remote Control
"""

# MQTT Broker Settings
# Option 1: Public MQTT Broker (recommended for testing)
MQTT_BROKER = "test.mosquitto.org"  # Public MQTT broker
MQTT_PORT = 1883
MQTT_USERNAME = ""  # No authentication needed for public broker
MQTT_PASSWORD = ""  # No authentication needed for public broker

# Option 2: Local broker (uncomment these lines if using local setup)
# MQTT_BROKER = "localhost"
# MQTT_PORT = 1883
# MQTT_USERNAME = ""
# MQTT_PASSWORD = ""

# MQTT Topics (with unique prefix to avoid conflicts on public broker)
import random
import string
import os
import json

def get_or_create_session_id():
    """Get existing session ID or create new one"""
    session_file = 'mqtt_session.json'
    
    # Try to load existing session ID
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
                return data.get('session_id', None)
        except:
            pass
    
    # Create new session ID if not exists
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    # Save to file
    try:
        with open(session_file, 'w') as f:
            json.dump({'session_id': session_id}, f)
    except:
        pass
    
    return session_id

# Get shared session ID
UNIQUE_ID = get_or_create_session_id()

MQTT_TOPICS = {
    'commands': f'scoshow_{UNIQUE_ID}/commands',
    'ranking': f'scoshow_{UNIQUE_ID}/ranking',
    'final': f'scoshow_{UNIQUE_ID}/final',
    'display': f'scoshow_{UNIQUE_ID}/display',
    'background': f'scoshow_{UNIQUE_ID}/background',
    'status': f'scoshow_{UNIQUE_ID}/status',
    'heartbeat': f'scoshow_{UNIQUE_ID}/heartbeat'
}

# QoS Level (0, 1, or 2)
MQTT_QOS = 1

# Keep Alive (seconds)
MQTT_KEEPALIVE = 60

# Reconnect settings
MQTT_RECONNECT_DELAY = 5
MQTT_MAX_RECONNECT_ATTEMPTS = 10
