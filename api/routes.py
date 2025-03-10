from flask import Blueprint, jsonify, request
from flask_login import login_required
import time
import json
from mqtt.client import (
    devices,
    client,
    request_device_settings,
    request_device_config,
    update_device_settings,
    update_device_config,
    send_reboot_command,
    get_device_state,
    update_monobank_api_key
)

api = Blueprint("api", __name__)

@api.route("/devices", methods=["GET"])
@login_required
def get_devices():
    """Получение списка найденных устройств"""
    return jsonify({"devices": list(devices.keys())})

@api.route("/devices/<device_id>/settings", methods=["GET"])
@login_required
def get_device_settings(device_id):
    """Получение текущих настроек устройства"""
    if device_id in devices and "settings" in devices[device_id]:
        settings = devices[device_id]["settings"]
        
        # Проверяем, есть ли метка времени и насколько недавно получены настройки
        current_time = time.time()
        received_at = settings.get("received_at", 0)
        
        # Если настройки получены в течение последних 60 секунд после запроса
        if received_at > 0 and (current_time - received_at) < 60:
            return jsonify(settings)
            
        # Настройки устарели или не были получены после запроса
        return jsonify({"error": "Settings are outdated or not received yet"}), 404
            
    return jsonify({"error": "Settings not available"}), 404

@api.route("/devices/<device_id>/settings/request", methods=["GET"])
@login_required
def request_settings(device_id):
    """Запрос настроек у устройства"""
    if device_id in devices:
        # Сбрасываем временную метку, если настройки уже были получены ранее
        if "settings" in devices[device_id]:
            if "received_at" in devices[device_id]["settings"]:
                devices[device_id]["settings"]["received_at"] = 0
            
        request_device_settings(device_id)
        return jsonify({"message": f"Settings request sent to {device_id}"})
    return jsonify({"error": "Device not found"}), 404

@api.route("/devices/<device_id>/settings/ack", methods=["GET"])
@login_required
def get_settings_ack(device_id):
    """Получение подтверждения отправки настроек"""
    if device_id in devices and "setting_ack" in devices[device_id]:
        return jsonify(devices[device_id]["setting_ack"])
    return jsonify({"error": "Settings ACK not available"}), 404

@api.route("/devices/<device_id>/settings", methods=["PUT"])
@login_required
def update_settings(device_id):
    """Обновление настроек устройства"""
    if device_id not in devices or "settings" not in devices[device_id]:
        return jsonify({"error": "Device not found or settings unavailable"}), 404

    new_settings = request.json
    # Очистка ACK перед отправкой новых настроек
    if "setting_ack" in devices[device_id]:
        devices[device_id]["setting_ack"] = None
        
    update_device_settings(device_id, new_settings)
    return jsonify({"message": f"Settings updated and sent to {device_id}"})

@api.route("/devices/<device_id>/config", methods=["GET"])
@login_required
def get_device_config(device_id):
    """Получение конфигурации устройства"""
    if device_id in devices and "config" in devices[device_id]:
        config = devices[device_id]["config"]
        
        # Проверяем, есть ли метка времени и насколько недавно получена конфигурация
        current_time = time.time()
        received_at = config.get("received_at", 0)
        
        # Если конфигурация получена в течение последних 60 секунд после запроса
        if received_at > 0 and (current_time - received_at) < 60:
            return jsonify(config)
            
        # Конфигурация устарела или не была получена после запроса
        return jsonify({"error": "Configuration is outdated or not received yet"}), 404
            
    return jsonify({"error": "Config not available"}), 404

@api.route("/devices/<device_id>/config/request", methods=["GET"])
@login_required
def request_config(device_id):
    """Запрос конфигурации у устройства"""
    if device_id in devices:
        # Сбрасываем временную метку, если конфигурация уже была получена ранее
        if "config" in devices[device_id]:
            if "received_at" in devices[device_id]["config"]:
                devices[device_id]["config"]["received_at"] = 0
            
        request_device_config(device_id)
        return jsonify({"message": f"Config request sent to {device_id}"})
    return jsonify({"error": "Device not found"}), 404

@api.route("/devices/<device_id>/config/ack", methods=["GET"])
@login_required
def get_config_ack(device_id):
    """Получение подтверждения отправки конфигурации"""
    if device_id in devices and "config_ack" in devices[device_id]:
        return jsonify(devices[device_id]["config_ack"])
    return jsonify({"error": "Config ACK not available"}), 404

@api.route("/devices/<device_id>/reboot/ack", methods=["GET"])
@login_required
def get_reboot_ack(device_id):
    """Получение подтверждения перезагрузки"""
    if device_id in devices and "reboot_ack" in devices[device_id]:
        return jsonify(devices[device_id]["reboot_ack"])
    return jsonify({"error": "Reboot ACK not available"}), 404

@api.route("/devices/<device_id>/config", methods=["PUT"])
@login_required
def update_config(device_id):
    """Отправка новой конфигурации в устройство"""
    if device_id not in devices or "config" not in devices[device_id]:
        return jsonify({"error": "Device not found or config unavailable"}), 404

    new_config = request.json
    # Очистка ACK перед отправкой новой конфигурации
    if "config_ack" in devices[device_id]:
        devices[device_id]["config_ack"] = None
        
    update_device_config(device_id, new_config)
    return jsonify({"message": f"Config updated and sent to {device_id}"})

@api.route("/devices/<device_id>/reboot", methods=["POST"])
@login_required
def reboot_device(device_id):
    """Отправка команды на перезагрузку"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

    delay = request.json.get("delay", 400)  # Значение по умолчанию 400
    # Очистка ACK перед отправкой команды перезагрузки
    if "reboot_ack" in devices[device_id]:
        devices[device_id]["reboot_ack"] = None
        
    send_reboot_command(device_id, delay)
    return jsonify({"message": f"Reboot command sent to {device_id} with delay {delay}"})

@api.route("/devices/<device_id>/state/info", methods=["GET"])
@login_required
def get_device_state_api(device_id):
    """Получение текущего состояния устройства"""
    if device_id in devices and devices[device_id].get("state"):
        return jsonify(devices[device_id]["state"])
    return jsonify({"error": "State not available"}), 404

@api.route("/devices/<device_id>/denomination", methods=["GET"])
@login_required
def get_device_denomination(device_id):
    """Получение истории приема денег устройством"""
    if device_id in devices and "denomination" in devices[device_id]:
        return jsonify({"denomination": devices[device_id]["denomination"]})
    return jsonify({"denomination": []})

@api.route("/devices/<device_id>/display", methods=["GET"])
@login_required
def get_display_info(device_id):
    """Получение информации с дисплея"""
    if device_id in devices and "display" in devices[device_id]:
        return jsonify(devices[device_id]["display"])
    return jsonify({"error": "Display info not available"}), 404

@api.route("/devices/<device_id>/display/request", methods=["GET"])
@login_required
def request_display_info(device_id):
    """Запрос информации с дисплея устройства"""
    if device_id in devices:
        topic = f"wsm/{device_id}/client/display/get"
        payload = json.dumps({"request_id": 234, "fields": ["line_1", "line_2"]})
        client.publish(topic, payload)
        return jsonify({"message": f"Display info request sent to {device_id}"})
    return jsonify({"error": "Device not found"}), 404

@api.route("/devices/<device_id>/payment/qrcode", methods=["POST"])
@login_required
def send_qrcode_payment(device_id):
    """Отправка оплаты QRcode"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
        
    # Очистка ACK перед отправкой
    if "payment_ack" in devices[device_id]:
        devices[device_id]["payment_ack"] = None
        
    data = request.json
    order_id = data.get("order_id", f"order_{int(time.time())}")
    amount = data.get("amount", 0)
    
    topic = f"wsm/{device_id}/client/payment/set"
    payload = json.dumps({
        "request_id": 234,
        "addQRcode": {
            "order_id": order_id,
            "amount": amount
        }
    })
    
    client.publish(topic, payload)
    return jsonify({"message": f"QR code payment sent to {device_id}", "order_id": order_id})

@api.route("/devices/<device_id>/payment/free", methods=["POST"])
@login_required
def send_free_payment(device_id):
    """Отправка свободного начисления"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
        
    # Очистка ACK перед отправкой
    if "payment_ack" in devices[device_id]:
        devices[device_id]["payment_ack"] = None
        
    amount = request.json.get("amount", 0)
    
    topic = f"wsm/{device_id}/client/payment/set"
    payload = json.dumps({
        "request_id": 234,
        "addFree": {
            "amount": amount
        }
    })
    
    client.publish(topic, payload)
    return jsonify({"message": f"Free payment sent to {device_id}"})

@api.route("/devices/<device_id>/payment/clear", methods=["POST"])
@login_required
def clear_payment(device_id):
    """Обнуление оплаты"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
        
    # Очистка ACK перед отправкой
    if "payment_ack" in devices[device_id]:
        devices[device_id]["payment_ack"] = None
    
    clear_options = request.json or {}
    
    payload = {
        "request_id": 234,
        "CoinClear": clear_options.get("CoinClear", True),
        "BillClear": clear_options.get("BillClear", True),
        "PrevClear": clear_options.get("PrevClear", True),
        "FreeClear": clear_options.get("FreeClear", True),
        "QRcodeClear": clear_options.get("QRcodeClear", True),
        "PayPassClear": clear_options.get("PayPassClear", True)
    }
    
    topic = f"wsm/{device_id}/client/payment/set"
    client.publish(topic, json.dumps(payload))
    return jsonify({"message": f"Payment cleared for {device_id}"})

@api.route("/devices/<device_id>/action", methods=["POST"])
@login_required
def send_action(device_id):
    """Отправка команды управления (пролив/блокировка)"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
        
    # Очистка ACK перед отправкой
    if "action_ack" in devices[device_id]:
        devices[device_id]["action_ack"] = None
    
    data = request.json
    pour = data.get("pour")
    blocking = data.get("blocking")
    
    payload = {"request_id": 234}
    
    if pour in ["Start_1", "Start_2", "Stop"]:
        payload["Pour"] = pour
        
    if blocking is not None:
        payload["Blocking"] = blocking
    
    topic = f"wsm/{device_id}/client/action/set"
    client.publish(topic, json.dumps(payload))
    return jsonify({"message": f"Action command sent to {device_id}"})

@api.route("/devices/<device_id>/payment/ack", methods=["GET"])
@login_required
def get_payment_ack(device_id):
    """Получение подтверждения платежа"""
    if device_id in devices and "payment_ack" in devices[device_id]:
        return jsonify(devices[device_id]["payment_ack"])
    return jsonify({"error": "Payment ACK not available"}), 404

@api.route("/devices/<device_id>/action/ack", methods=["GET"])
@login_required
def get_action_ack(device_id):
    """Получение подтверждения действия"""
    if device_id in devices and "action_ack" in devices[device_id]:
        return jsonify(devices[device_id]["action_ack"])
    return jsonify({"error": "Action ACK not available"}), 404

@api.route("/devices/<device_id>/monobank/api-key", methods=["PUT"])
@login_required
def update_device_monobank_api_key(device_id):
    """Обновление API-ключа Monobank для устройства"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    data = request.json
    api_key = data.get("api_key", "")
    
    update_monobank_api_key(device_id, api_key)
    return jsonify({"message": f"Monobank API key updated for {device_id}"})

@api.route("/webhook/monobank/<device_id>/<order_id>/<amount>", methods=["POST"])
def monobank_webhook(device_id, order_id, amount):
    """Обработчик вебхука от Monobank"""
    print(f"🔍 Webhook received: device={device_id}, order={order_id}, amount={amount}")
    
    try:
        # Получаем данные от Monobank
        data = request.json
        print(f"📌 Webhook data: {json.dumps(data)}")
        
        # Проверяем статус платежа
        if data.get("status") == "success":
            # Платеж успешен, начисляем деньги на устройство
            amount_kopeek = int(amount)
            
            # Формируем сообщение для MQTT в точном соответствии с требуемым форматом
            topic = f"wsm/{device_id}/client/payment/set"
            payload = {
                "request_id": 234,
                "addQRcode": {
                    "order_id": order_id,
                    "amount": amount_kopeek
                }
            }
            
            # Преобразуем в JSON строку для отправки
            mqtt_payload = json.dumps(payload)
            
            print(f"🚀 Sending MQTT message to topic: {topic}")
            print(f"📦 Payload: {mqtt_payload}")
            
            # Публикуем в MQTT
            result = client.publish(topic, mqtt_payload)
            print(f"📢 MQTT publish result: {result}")
            
            # Логируем успешную оплату
            print(f"💰 Monobank payment success: device={device_id}, order={order_id}, amount={amount_kopeek/100} UAH")
            
            # Сохраняем информацию о платеже
            if device_id in devices:
                if "monobank_payments" not in devices[device_id]:
                    devices[device_id]["monobank_payments"] = []
                    
                payment_info = {
                    "order_id": order_id,
                    "amount": amount_kopeek,
                    "status": "success",
                    "timestamp": time.time(),
                    "invoice_id": data.get("invoiceId", "")
                }
                
                devices[device_id]["monobank_payments"].append(payment_info)
            else:
                print(f"⚠️ Device {device_id} not found in devices dictionary")
            
            return jsonify({"status": "ok"}), 200
        else:
            # Платеж не успешен
            print(f"❌ Monobank payment failed: device={device_id}, order={order_id}, status={data.get('status')}")
            return jsonify({"status": "failed"}), 200
            
    except Exception as e:
        import traceback
        print(f"❌ Error processing Monobank webhook: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@api.route("/devices/<device_id>/monobank/payments", methods=["GET"])
@login_required
def get_monobank_payments(device_id):
    """Получение истории платежей через Monobank"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404
    
    payments = devices.get(device_id, {}).get("monobank_payments", [])
    return jsonify({"payments": payments})