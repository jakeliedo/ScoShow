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
import platform

def get_or_create_session_id():
    """Get fixed session ID for tournament ranking system"""
    session_file = 'mqtt_session.json'
    
    # Fixed session ID for club tournament ranking 2025
    session_id = "clubvtournamentranking2025"
    
    # Always save the fixed session ID to file
    try:
        with open(session_file, 'w') as f:
            json.dump({'session_id': session_id}, f)
    except:
        pass
    
    return session_id

# A simple client identifier to support targeted commands (defaults to hostname)
def get_client_id():
    try:
        host = platform.node() or os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME')
        # Sanitize to safe characters
        safe = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '-' for ch in host)
        return safe or 'client'
    except Exception:
        return 'client'

# Get shared session ID
UNIQUE_ID = get_or_create_session_id()
CLIENT_ID = get_client_id()

MQTT_TOPICS = {
    'commands': f'scoshow_{UNIQUE_ID}/commands',
    'ranking': f'scoshow_{UNIQUE_ID}/ranking',
    'final': f'scoshow_{UNIQUE_ID}/final',
    'display': f'scoshow_{UNIQUE_ID}/display',
    'background': f'scoshow_{UNIQUE_ID}/background',
    'status': f'scoshow_{UNIQUE_ID}/status',
    'heartbeat': f'scoshow_{UNIQUE_ID}/heartbeat'
}

# Derived topics for targeted/broadcast commands (backward compatible with 'commands')
MQTT_TOPICS['commands_targeted'] = f"{MQTT_TOPICS['commands']}/{CLIENT_ID}"
MQTT_TOPICS['commands_broadcast'] = f"{MQTT_TOPICS['commands']}/all"

# Targeted variants for other channels
for key in ('ranking', 'final', 'display', 'background'):
    MQTT_TOPICS[f'{key}_targeted'] = f"{MQTT_TOPICS[key]}/{CLIENT_ID}"
    MQTT_TOPICS[f'{key}_broadcast'] = f"{MQTT_TOPICS[key]}/all"

# QoS Level (0, 1, or 2)
MQTT_QOS = 1

# Keep Alive (seconds)
MQTT_KEEPALIVE = 60

# Reconnect settings
MQTT_RECONNECT_DELAY = 5
MQTT_MAX_RECONNECT_ATTEMPTS = 10
