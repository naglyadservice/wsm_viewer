import paho.mqtt.client as mqtt
import json
import time
import traceback
from flask import current_app
from config import load_config
from datetime import datetime

# Словарь для хранения данных об устройствах в оперативной памяти
# (для обратной совместимости с текущим кодом)
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
    from app import app  # Импортируем внутри функции для избежания циклических импортов
    from db.utils import (
        get_or_create_device, update_device_last_seen, save_device_state,
        save_device_settings, save_device_config, save_ack_message, 
        save_display_info, save_payment, save_sale, save_collection,
        get_monobank_api_key
    )

    # Создаем контекст приложения для каждого сообщения
    with app.app_context():
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            current_app.logger.warning(f"⚠️ JSON Decode Error: {msg.payload}")
            return

        print(f"📥 Received message: {topic} → {payload}")

        if topic.startswith("wsm/"):
            parts = topic.split("/")
            if len(parts) < 3:
                return

            device_id = parts[1]

            try:
                # Обновляем время последнего обнаружения устройства
                update_device_last_seen(device_id)

                # Для обратной совместимости обновляем также кэш в памяти
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
                        "denomination": [], 
                        "monobank_api_key": load_config().monobank.api_key, 
                        "monobank_payments": []
                    }

                request_id = payload.get("request_id", 234)

                # Обработка состояния оборудования
                if topic.endswith("/server/state/info"):
                    # Сохраняем в БД
                    save_device_state(device_id, payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["state"] = payload
                    print(f"🆕 State updated for {device_id}")

                # Обработка настроек устройства
                elif topic.endswith("/server/setting"):
                    payload["request_id"] = request_id
                    payload["received_at"] = time.time()  # Добавляем временную метку
                    
                    # Сохраняем в БД
                    save_device_settings(device_id, payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["settings"] = payload
                    print(f"⚙️ Settings received for {device_id}")

                # Обработка конфигурации устройства
                elif topic.endswith("/server/config"):
                    payload["request_id"] = request_id
                    payload["received_at"] = time.time()  # Добавляем временную метку
                    
                    # Добавляем API-ключ Monobank, если он есть в БД
                    api_key = get_monobank_api_key(device_id)
                    if api_key:
                        payload["monobank_api_key"] = api_key
                    
                    # Сохраняем в БД
                    save_device_config(device_id, payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["config"] = payload
                    print(f"🔧 Config received for {device_id}")

                # Обработка подтверждения настроек
                elif topic.endswith("/server/setting/ack"):
                    # Сохраняем в БД
                    save_ack_message(device_id, "setting", payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["setting_ack"] = payload
                    print(f"⚙️ Settings ACK received for {device_id}: {payload}")

                # Обработка подтверждения конфигурации
                elif topic.endswith("/server/config/ack"):
                    # Сохраняем в БД
                    save_ack_message(device_id, "config", payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["config_ack"] = payload
                    print(f"🔧 Config ACK received for {device_id}: {payload}")

                # Обработка подтверждения перезагрузки
                elif topic.endswith("/server/reboot/ack"):
                    # Сохраняем в БД
                    save_ack_message(device_id, "reboot", payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["reboot_ack"] = payload
                    print(f"🔄 Reboot ACK received for {device_id}")
                    request_device_settings(device_id)
                    request_device_config(device_id)
                    
                # Обработка приема денег
                elif topic.endswith("/server/denomination/info"):
                    # Сохраняем в БД как платеж
                    payment_type = None
                    if payload.get("billValue"):
                        payment_type = "bill"
                        amount = payload.get("billValue")
                    elif payload.get("coinValue"):
                        payment_type = "coin"
                        amount = payload.get("coinValue")
                        
                    if payment_type:
                        save_payment(device_id, payment_type, amount, status='confirmed', confirmed_at=datetime.utcnow())
                    
                    # Обновляем кэш в памяти
                    if "denomination" not in devices[device_id]:
                        devices[device_id]["denomination"] = []
                    devices[device_id]["denomination"].append(payload)
                    print(f"💰 Denomination received for {device_id}: {payload}")
                    
                # Обработка информации с дисплея
                elif topic.endswith("/server/display"):
                    # Сохраняем в БД
                    save_display_info(device_id, payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["display"] = payload
                    print(f"📺 Display info received for {device_id}: {payload}")

                # Обработка подтверждения платежа
                elif topic.endswith("/server/payment/ack"):
                    # Сохраняем в БД
                    save_ack_message(device_id, "payment", payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["payment_ack"] = payload
                    print(f"💰 Payment ACK received for {device_id}: {payload}")
                    
                    # Если это подтверждение платежа через Monobank
                    if payload.get("code") == 0:
                        # Находим и обновляем статус платежа
                        # В реальной реализации нужно связать этот ACK с конкретным платежом
                        # через order_id или другой идентификатор
                        
                        # Для обратной совместимости поддерживаем также кэш в памяти
                        if "monobank_payments" in devices[device_id]:
                            pending_payments = [p for p in devices[device_id]["monobank_payments"] 
                                                if p.get("status") == "pending"]
                            if pending_payments:
                                # Обновляем статус первого ожидающего платежа
                                pending_payments[0]["status"] = "confirmed"
                                pending_payments[0]["confirmed_at"] = time.time()
                                print(f"💰 Monobank payment confirmed for {device_id}: {pending_payments[0]}")

                # Обработка подтверждения действия
                elif topic.endswith("/server/action/ack"):
                    # Сохраняем в БД
                    save_ack_message(device_id, "action", payload)
                    
                    # Обновляем кэш в памяти
                    devices[device_id]["action_ack"] = payload
                    print(f"🔄 Action ACK received for {device_id}: {payload}")
                    
                # Обработка информации о продаже
                elif topic.endswith("/server/sale/set"):
                    # Сохраняем продажу в БД
                    sale = save_sale(device_id, payload)
                    print(f"💵 Sale received for {device_id}: {payload}")
                    
                    # Отправляем подтверждение получения продажи
                    send_sale_ack(device_id, sale.external_id)
                    
                # Обработка информации об инкассации
                elif topic.endswith("/server/incass/set"):
                    # Сохраняем инкассацию в БД
                    collection = save_collection(device_id, payload)
                    print(f"💰 Collection received for {device_id}: {payload}")
                    
                    # Отправляем подтверждение получения инкассации
                    send_collection_ack(device_id, collection.external_id)

            except Exception as e:
                current_app.logger.error(f"Error processing MQTT message: {e}")
                current_app.logger.error(traceback.format_exc())

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
    from db.utils import update_monobank_api_key

    if device_id in devices and "config" in devices[device_id]:
        topic = f"wsm/{device_id}/client/config/set"
        
        # Сохраняем API-ключ Monobank перед отправкой, если он есть в новой конфигурации
        if "monobank_api_key" in new_config:
            update_monobank_api_key(device_id, new_config["monobank_api_key"])
            # Удаляем API-ключ из конфигурации перед отправкой в устройство
            del new_config["monobank_api_key"]
        
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

import json
from db.utils import get_sale, mark_sale_ack_sent
from flask import current_app

def send_sale_ack(device_id, sale_id):
    """Отправка подтверждения получения продажи"""
    if device_id not in devices:
        current_app.logger.error(f"❌ Устройство {device_id} не найдено в памяти")
        return False

    topic = f"wsm/{device_id}/client/sale/ack"
    payload = json.dumps({
        "id": sale_id,
        "code": 0  # 0 - успешно
    })

    print(f"📤 Sending sale ACK to {device_id} for sale ID {sale_id}")

    try:
        # Отправка сообщения в MQTT
        result = client.publish(topic, payload)

        # Проверка успешности публикации
        if result.rc != 0:
            current_app.logger.error(f"❌ Ошибка публикации ACK для продажи {sale_id} (код {result.rc})")
            return False

        # Проверяем, существует ли продажа в БД
        sale = get_sale(device_id, sale_id)
        if not sale:
            current_app.logger.error(f"⚠️ Продажа {sale_id} для устройства {device_id} не найдена в БД")
            return False

        # Отмечаем продажу как подтвержденную в БД
        mark_sale_ack_sent(sale.id)
        print(f"✅ Sale ACK sent successfully for {sale_id}")

        return True

    except Exception as e:
        current_app.logger.error(f"❌ Ошибка при отправке подтверждения продажи {sale_id}: {e}")
        return False

def send_collection_ack(device_id, collection_id):
    """Отправка подтверждения получения инкассации"""
    from db.utils import get_collection, mark_collection_ack_sent

    if device_id in devices:
        topic = f"wsm/{device_id}/client/incass/ack"
        payload = json.dumps({
            "id": collection_id,
            "code": 0  # 0 - успешно
        })
        print(f"📤 Sending collection ACK to {device_id} for collection ID {collection_id}")
        result = client.publish(topic, payload)
        
        if result.rc == 0:
            # Обновляем статус в БД
            collection = get_collection(device_id, collection_id)
            if collection:
                mark_collection_ack_sent(collection.id)
            print(f"✅ Collection ACK sent successfully")
            return True
        else:
            print(f"❌ Collection ACK publish failed with code {result.rc}")
            return False

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
        payload = {
            "request_id": 234,
            "addQRcode": {
                "order_id": order_id,
                "amount": amount
            }
        }
        
        mqtt_payload = json.dumps(payload)
        print(f"📤 Sending QR code payment to {device_id}: {amount} kopecks, order_id: {order_id}")
        print(f"📦 Full payload: {mqtt_payload}")
        
        result = client.publish(topic, mqtt_payload)
        if result.rc == 0:
            print(f"✅ MQTT message sent successfully")
            return True
        else:
            print(f"❌ MQTT publish failed with code {result.rc}")
            return False

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

def get_monobank_payments_history(device_id):
    """Получение истории платежей Monobank."""
    if device_id in devices:
        return devices[device_id].get("monobank_payments", [])
    return []

config = load_config()

# Инициализация MQTT-клиента
client = mqtt.Client()
client.username_pw_set(config.mqtt.username, config.mqtt.password)
client.on_connect = on_connect
client.on_message = on_message

# Подключение к брокеру
try:
    client.connect(config.mqtt.broker, config.mqtt.port, 60)
    client.loop_start()
    print(f"🔌 Connecting to MQTT broker {config.mqtt.broker}:{config.mqtt.port}")
except Exception as e:
    print(f"❌ Failed to connect to MQTT broker: {e}")