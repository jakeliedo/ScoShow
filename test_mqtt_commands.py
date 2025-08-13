#!/usr/bin/env python3
"""
Test script để kiểm tra ScoShow client-remote MQTT communication
"""

import paho.mqtt.client as mqtt
import json
import time

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
SESSION_ID = "clubvtournamentranking2025"

# MQTT Topics
MQTT_TOPICS = {
    'commands': f"scoshow_{SESSION_ID}/commands",
    'commands_targeted': f"scoshow_{SESSION_ID}/commands/{__import__('platform').node() or 'client'}",
    'ranking': f"scoshow_{SESSION_ID}/ranking",
    'ranking_targeted': f"scoshow_{SESSION_ID}/ranking/{__import__('platform').node() or 'client'}",
    'final': f"scoshow_{SESSION_ID}/final",
    'final_targeted': f"scoshow_{SESSION_ID}/final/{__import__('platform').node() or 'client'}",
    'display': f"scoshow_{SESSION_ID}/display",
    'display_targeted': f"scoshow_{SESSION_ID}/display/{__import__('platform').node() or 'client'}",
    'background': f"scoshow_{SESSION_ID}/background",
    'background_targeted': f"scoshow_{SESSION_ID}/background/{__import__('platform').node() or 'client'}",
    'status': f"scoshow_{SESSION_ID}/status",
    'heartbeat': f"scoshow_{SESSION_ID}/heartbeat"
}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to MQTT broker")
        # Subscribe to status to see responses
        client.subscribe(MQTT_TOPICS['status'])
        print(f"📬 Subscribed to status updates")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print(f"📨 Status: {data}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_open_display():
    """Test opening display"""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"🔌 Connecting to {MQTT_BROKER}:{MQTT_PORT}")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    time.sleep(2)  # Wait for connection
    
    # Test 1: Open Display
    print(f"\n🧪 Test 1: Open Display")
    open_command = {
        "action": "open_display",
        "monitor_index": 0,
        "background_folder": "D:/Python/Projects/ScoShow/background",
        "target": __import__('platform').node() or 'client'
    }
    
    # Prefer targeted command to avoid other clients reacting
    result = client.publish(MQTT_TOPICS.get('commands_targeted', MQTT_TOPICS['commands']), json.dumps(open_command))
    print(f"📤 Sent open display command: {result.rc}")
    time.sleep(3)
    
    # Test 2: Show Background
    print(f"\n🧪 Test 2: Show Background")
    bg_command = {
        "action": "show_background",
        "background_id": "01",
        "target": __import__('platform').node() or 'client'
    }
    
    result = client.publish(MQTT_TOPICS.get('display_targeted', MQTT_TOPICS['display']), json.dumps(bg_command))
    print(f"📤 Sent show background command: {result.rc}")
    time.sleep(2)
    
    # Test 3: Ranking Data
    print(f"\n🧪 Test 3: Ranking Data")
    ranking_data = {
        "round": "Round 1",
        "1st": "Player A",
        "2nd": "Player B", 
        "3rd": "Player C",
        "positions": {
            "round": "960,100",
            "1st": "960,200",
            "2nd": "960,300", 
            "3rd": "960,400"
        },
        "font_settings": {
            "font_name": "arial.ttf",
            "rank_font_size": 60,
            "round_font_size": 60,
            "color": "white"
        },
        "target": __import__('platform').node() or 'client'
    }
    
    result = client.publish(MQTT_TOPICS.get('ranking_targeted', MQTT_TOPICS['ranking']), json.dumps(ranking_data))
    print(f"📤 Sent ranking data: {result.rc}")
    time.sleep(2)
    
    print(f"\n✅ Test completed!")
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    test_open_display()
