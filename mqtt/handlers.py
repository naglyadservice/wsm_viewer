import json

def discover_device(topic, payload, devices):
    device_id = topic.split("/")[1]
    if device_id not in devices:
        devices[device_id] = {"settings": {}}
    print(f"Device discovered: {device_id}")

def handle_device_settings(topic, payload):
    device_id = topic.split("/")[1]
    settings = json.loads(payload)
    print(f"Received settings from {device_id}: {settings}")
