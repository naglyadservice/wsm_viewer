import paho.mqtt.client as mqtt
import json
import time
from config import Config

# Словарь для хранения данных об устройствах
devices = {}

def on_connect(client, userdata, flags, rc):
    """При подключении подписываемся на все устройства."""
    if rc == 0:
        print("✅ Connected to MQTT broker, subscribing to wsm/#")
        client.subscribe("wsm/#")
    else:
        print(f"❌ Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Обработка входящих MQTT-сообщений."""
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"⚠️ JSON Decode Error: {msg.payload}")
        return

    print(f"📥 Received message: {topic} → {payload}")

    if topic.startswith("wsm/"):
        parts = topic.split("/")
        if len(parts) < 3:
            return

        device_id = parts[1]

        if device_id not in devices:
            devices[device_id] = {
                "settings": {}, 
                "config": {}, 
                "state": {}, 
                "reboot_ack": None,
                "setting_ack": None,
                "config_ack": None,
                "payment_ack": None,
                "action_ack": None,
                "display": None,
                "denomination": []
            }

        request_id = payload.get("request_id", 234)

        # Обработка состояния оборудования
        if topic.endswith("/server/state/info"):
            devices[device_id]["state"] = payload
            print(f"🆕 State updated for {device_id}")

        # Обработка настроек устройства
        elif topic.endswith("/server/setting"):
            payload["request_id"] = request_id
            payload["received_at"] = time.time()  # Добавляем временную метку
            devices[device_id]["settings"] = payload
            print(f"⚙️ Settings received for {device_id}")

        # Обработка конфигурации устройства
        elif topic.endswith("/server/config"):
            payload["request_id"] = request_id
            payload["received_at"] = time.time()  # Добавляем временную метку
            devices[device_id]["config"] = payload
            print(f"🔧 Config received for {device_id}")

        # Обработка подтверждения настроек
        elif topic.endswith("/server/setting/ack"):
            devices[device_id]["setting_ack"] = payload
            print(f"⚙️ Settings ACK received for {device_id}: {payload}")

        # Обработка подтверждения конфигурации
        elif topic.endswith("/server/config/ack"):
            devices[device_id]["config_ack"] = payload
            print(f"🔧 Config ACK received for {device_id}: {payload}")

        # Обработка подтверждения перезагрузки
        elif topic.endswith("/server/reboot/ack"):
            devices[device_id]["reboot_ack"] = payload
            print(f"🔄 Reboot ACK received for {device_id}")
            request_device_settings(device_id)
            request_device_config(device_id)
            
        # Обработка приема денег
        elif topic.endswith("/server/denomination/info"):
            if "denomination" not in devices[device_id]:
                devices[device_id]["denomination"] = []
            devices[device_id]["denomination"].append(payload)
            print(f"💰 Denomination received for {device_id}: {payload}")
            
        # Обработка информации с дисплея
        elif topic.endswith("/server/display"):
            devices[device_id]["display"] = payload
            print(f"📺 Display info received for {device_id}: {payload}")

        # Обработка подтверждения платежа
        elif topic.endswith("/server/payment/ack"):
            devices[device_id]["payment_ack"] = payload
            print(f"💰 Payment ACK received for {device_id}: {payload}")

        # Обработка подтверждения действия
        elif topic.endswith("/server/action/ack"):
            devices[device_id]["action_ack"] = payload
            print(f"🔄 Action ACK received for {device_id}: {payload}")

def request_device_settings(device_id):
    """Запрос настроек у устройства."""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/setting/get"
        payload = json.dumps({"request_id": 234, "fields": []})
        print(f"📤 Requesting settings for {device_id}...")
        client.publish(topic, payload)

def request_device_config(device_id):
    """Запрос конфигурации у устройства."""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/config/get"
        payload = json.dumps({"request_id": 234, "fields": []})
        print(f"📤 Requesting config for {device_id}...")
        client.publish(topic, payload)

def update_device_settings(device_id, new_settings):
    """Отправка обновленных настроек в устройство."""
    if device_id in devices and "settings" in devices[device_id]:
        topic = f"wsm/{device_id}/client/setting/set"
        
        # Замена None на числовые значения для всех полей
        for key in new_settings:
            if new_settings[key] is None:
                new_settings[key] = 0
                
        new_settings["request_id"] = devices[device_id]["settings"].get("request_id", 234)
        payload = json.dumps(new_settings)
        print(f"📤 Sending updated settings to {device_id}: {new_settings}")
        client.publish(topic, payload)

def update_device_config(device_id, new_config):
    """Отправка обновленной конфигурации в устройство."""
    if device_id in devices and "config" in devices[device_id]:
        topic = f"wsm/{device_id}/client/config/set"
        
        # Преобразование строк в массивы для таблиц номиналов если нужно
        for key in ['bill_table', 'coin_table']:
            if key in new_config and isinstance(new_config[key], str):
                try:
                    new_config[key] = [int(x.strip()) for x in new_config[key].split(',') if x.strip()]
                except ValueError:
                    print(f"⚠️ Error converting {key} to array, using empty array")
                    new_config[key] = []
                    
        # Замена None на значения по умолчанию
        for key in new_config:
            if new_config[key] is None:
                if key in ['broker_port', 'OTA_port', 'timeZone', 'coinPulsePrice']:
                    new_config[key] = 0
                elif key in ['broker_uri', 'OTA_server', 'wifi_STA_ssid', 'wifi_STA_pass', 'ntp_server', 'broker_user', 'broker_pass']:
                    new_config[key] = ""
        
        new_config["request_id"] = devices[device_id]["config"].get("request_id", 234)
        payload = json.dumps(new_config)
        print(f"📤 Sending updated config to {device_id}: {new_config}")
        client.publish(topic, payload)

def send_reboot_command(device_id, delay):
    """Отправка команды на перезагрузку устройства."""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/reboot/set"
        payload = json.dumps({"request_id": 234, "delay": delay})
        print(f"📤 Sending reboot command to {device_id} with delay {delay}")
        client.publish(topic, payload)

def get_device_state(device_id):
    """Получение последнего состояния устройства."""
    return devices.get(device_id, {}).get("state", {})

def request_display_info(device_id):
    """Запрос информации с дисплея устройства."""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/display/get"
        payload = json.dumps({"request_id": 234, "fields": ["line_1", "line_2"]})
        print(f"📤 Requesting display info for {device_id}...")
        client.publish(topic, payload)

def send_qrcode_payment(device_id, order_id, amount):
    """Отправка оплаты QR-кодом в устройство."""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/payment/set"
        payload = json.dumps({
            "request_id": 234,
            "addQRcode": {
                "order_id": order_id,
                "amount": amount
            }
        })
        print(f"📤 Sending QR code payment to {device_id}: {amount} kopecks, order_id: {order_id}")
        client.publish(topic, payload)

def send_free_payment(device_id, amount):
    """Отправка свободного начисления в устройство."""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/payment/set"
        payload = json.dumps({
            "request_id": 234,
            "addFree": {
                "amount": amount
            }
        })
        print(f"📤 Sending free payment to {device_id}: {amount} kopecks")
        client.publish(topic, payload)

def clear_payment(device_id, clear_options=None):
    """Отправка команды обнуления оплаты."""
    if device_id in devices:
        if clear_options is None:
            clear_options = {
                "CoinClear": True,
                "BillClear": True,
                "PrevClear": True,
                "FreeClear": True,
                "QRcodeClear": True,
                "PayPassClear": True
            }
        
        topic = f"wsm/{device_id}/client/payment/set"
        payload = json.dumps({
            "request_id": 234,
            **clear_options
        })
        print(f"📤 Clearing payment for {device_id}")
        client.publish(topic, payload)

def send_action_command(device_id, pour=None, blocking=None):
    """Отправка команды действия (пролив воды/блокировка)."""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/action/set"
        payload = {"request_id": 234}
        
        if pour in ["Start", "Stop"]:
            payload["Pour"] = pour
            
        if blocking is not None:
            payload["Blocking"] = blocking
            
        print(f"📤 Sending action command to {device_id}: {payload}")
        client.publish(topic, json.dumps(payload))

# Инициализация MQTT-клиента
client = mqtt.Client()
client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Подключение к брокеру
try:
    client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
    client.loop_start()
    print(f"🔌 Connecting to MQTT broker {Config.MQTT_BROKER}:{Config.MQTT_PORT}")
except Exception as e:
    print(f"❌ Failed to connect to MQTT broker: {e}")