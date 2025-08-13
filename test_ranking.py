#!/usr/bin/env python3
"""
Test script to send ranking data via MQTT and verify the fixed parsing
"""

import json
import paho.mqtt.client as mqtt
import time

# MQTT Configuration  
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
SESSION_ID = "clubvtournamentranking2025"

def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to MQTT broker with result code {rc}")

def test_ranking_data():
    """Test sending ranking data to verify the fix"""
    
    client = mqtt.Client()
    client.on_connect = on_connect
    
    print("🔌 Connecting to MQTT broker...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    time.sleep(2)  # Wait for connection
    
    # Test data with string positions (this caused the "too many values to unpack" error)
    test_data = {
        'round': '1',
        '1st': 'Player A',
        '2nd': 'Player B', 
        '3rd': 'Player C',
        '4th': 'Player D',
        '5th': 'Player E',
        'positions': {
            'round': '1286,935',
            '1st': '2980,125',
            '2nd': '2980,220', 
            '3rd': '2980,318',
            '4th': '2980,402',
            '5th': '2980,495',
            '6th': '2980,578',
            '7th': '2980,672',
            '8th': '2980,762',
            '9th': '2980,850',
            '10th': '2980,939'
        },
        'font_settings': {
            'font_name': 'arial.ttf',
            'rank_font_size': 80,
            'round_font_size': 80,
            'color': 'white'
        }
    }
    
    topic = f"scoshow_{SESSION_ID}/ranking"
    
    print("📤 Sending test ranking data...")
    print(f"Topic: {topic}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    client.publish(topic, json.dumps(test_data))
    
    print("✅ Test data sent! Check client for results.")
    
    time.sleep(2)
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    test_ranking_data()
