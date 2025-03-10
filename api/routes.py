from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from config import Config
import time  
import uuid  #импорт для генерации уникальных идентификаторов
import json 
from db.models import Sale


# Импорты для работы с устройствами и MQTT
from mqtt.client import (
    devices,
    client,
    send_qrcode_payment,
    send_free_payment,
    clear_payment,
    send_action_command,
    get_monobank_payments_history,
    request_device_settings,
    request_device_config,
    update_device_settings,
    update_device_config,
    send_reboot_command,
    request_display_info
)

# Импорты для работы с базой данных и утилитами
from db.utils import (
    get_device,
    get_all_devices,
    get_latest_device_state,
    get_latest_device_settings,
    get_latest_device_config,
    get_device_payments,
    get_device_sales,
    get_device_collections,
    update_monobank_api_key,
    get_monobank_api_key,
    get_latest_display_info,
    get_latest_ack_message
)

api = Blueprint("api", __name__)

@api.route("/devices", methods=["GET"])
@login_required
def get_devices():
    """Получение списка найденных устройств"""
    # Получаем устройства из БД
    db_devices = get_all_devices()
    device_ids = [device.id for device in db_devices]
    
    # Дополняем списком из памяти для обратной совместимости
    for device_id in devices.keys():
        if device_id not in device_ids:
            device_ids.append(device_id)
            
    return jsonify({"devices": device_ids})

@api.route("/devices/<device_id>/settings", methods=["GET"])
@login_required
def get_device_settings(device_id):
    """Получение текущих настроек устройства"""
    # Пытаемся получить настройки из БД
    db_settings = get_latest_device_settings(device_id)
    if db_settings:
        return jsonify(db_settings.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
    if device_id in devices and "settings" in devices[device_id]:
        settings = devices[device_id]["settings"]
        
        # Проверяем, есть ли метка времени и насколько недавно получены настройки
        current_time = time.time()
        received_at = settings.get("received_at", 0)
        
        # Если настройки получены в течение последних 60 секунд после запроса
        if received_at > 0 and (current_time - received_at) < 60:
            return jsonify(settings)
            
    # Настройки не найдены или устарели
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
    # Пытаемся получить ACK из БД
    ack = get_latest_ack_message(device_id, "setting")
    if ack:
        return jsonify(ack.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
    if device_id in devices and "setting_ack" in devices[device_id]:
        return jsonify(devices[device_id]["setting_ack"])
        
    return jsonify({"error": "Settings ACK not available"}), 404

@api.route("/devices/<device_id>/settings", methods=["PUT"])
@login_required
def update_settings(device_id):
    """Обновление настроек устройства"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

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
    # Пытаемся получить конфигурацию из БД
    db_config = get_latest_device_config(device_id)
    if db_config:
        return jsonify(db_config.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
    if device_id in devices and "config" in devices[device_id]:
        config = devices[device_id]["config"]
        
        # Проверяем, есть ли метка времени и насколько недавно получена конфигурация
        current_time = time.time()
        received_at = config.get("received_at", 0)
        
        # Если конфигурация получена в течение последних 60 секунд после запроса
        if received_at > 0 and (current_time - received_at) < 60:
            return jsonify(config)
            
    # Конфигурация не найдена или устарела
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
    # Пытаемся получить ACK из БД
    ack = get_latest_ack_message(device_id, "config")
    if ack:
        return jsonify(ack.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
    if device_id in devices and "config_ack" in devices[device_id]:
        return jsonify(devices[device_id]["config_ack"])
        
    return jsonify({"error": "Config ACK not available"}), 404

@api.route("/devices/<device_id>/reboot/ack", methods=["GET"])
@login_required
def get_reboot_ack(device_id):
    """Получение подтверждения перезагрузки"""
    # Пытаемся получить ACK из БД
    ack = get_latest_ack_message(device_id, "reboot")
    if ack:
        return jsonify(ack.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
    if device_id in devices and "reboot_ack" in devices[device_id]:
        return jsonify(devices[device_id]["reboot_ack"])
        
    return jsonify({"error": "Reboot ACK not available"}), 404

@api.route("/devices/<device_id>/config", methods=["PUT"])
@login_required
def update_config(device_id):
    """Отправка новой конфигурации в устройство"""
    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

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
    # Пытаемся получить состояние из БД
    db_state = get_latest_device_state(device_id)
    if db_state:
        return jsonify(db_state.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
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
    # Пытаемся получить информацию с дисплея из БД
    db_display = get_latest_display_info(device_id)
    if db_display:
        return jsonify(db_display.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
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
    # Пытаемся получить ACK из БД
    ack = get_latest_ack_message(device_id, "payment")
    if ack:
        return jsonify(ack.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
    if device_id in devices and "payment_ack" in devices[device_id]:
        return jsonify(devices[device_id]["payment_ack"])
        
    return jsonify({"error": "Payment ACK not available"}), 404

@api.route("/devices/<device_id>/action/ack", methods=["GET"])
@login_required
def get_action_ack(device_id):
    """Получение подтверждения действия"""
    # Пытаемся получить ACK из БД
    ack = get_latest_ack_message(device_id, "action")
    if ack:
        return jsonify(ack.to_dict())
    
    # Если в БД нет, пробуем из памяти (обратная совместимость)
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

# Новые API-эндпоинты для продаж и инкассаций

@api.route("/devices/<device_id>/sales", methods=["GET"])
@login_required
def get_sales(device_id):
    sales = Sale.query.filter_by(device_id=device_id).distinct().all()
    sales_data = []

    for sale in sales:
        sales_data.append({
            "id": sale.id,
            "created": sale.created.strftime('%d.%m.%Y %H:%M:%S'),
            "sum": sale.add_coin + sale.add_bill + sale.add_qr + sale.add_pp + sale.add_free,
            "liters": sale.out_liters_1 + sale.out_liters_2,
            "payment_type": sale.payment_source,
        })

    return jsonify(sales_data)

@api.route("/devices/<device_id>/sales/<int:sale_id>/ack", methods=["POST"])
@login_required
def resend_sale_ack(device_id, sale_id):
    """Повторная отправка подтверждения получения продажи"""
    success = send_sale_ack(device_id, sale_id)
    if success:
        return jsonify({"message": f"Sale ACK resent to {device_id} for sale ID {sale_id}"})
    else:
        return jsonify({"error": "Failed to send sale ACK"}), 500

@api.route("/devices/<device_id>/collections", methods=["GET"])
@login_required
def get_collections(device_id):
    """Получение списка инкассаций устройства"""
    collections = get_device_collections(device_id)
    return jsonify({
        "collections": [collection.to_dict() for collection in collections],
        "total": len(collections)
    })

@api.route("/devices/<device_id>/collections/<int:collection_id>/ack", methods=["POST"])
@login_required
def resend_collection_ack(device_id, collection_id):
    """Повторная отправка подтверждения получения инкассации"""
    success = send_collection_ack(device_id, collection_id)
    if success:
        return jsonify({"message": f"Collection ACK resent to {device_id} for collection ID {collection_id}"})
    else:
        return jsonify({"error": "Failed to send collection ACK"}), 500

@api.route("/devices/<device_id>/payments", methods=["GET"])
@login_required
def get_payments(device_id):
    """Получение списка всех платежей устройства"""
    payment_type = request.args.get("type")
    payments = get_device_payments(device_id, payment_type)
    return jsonify({
        "payments": [payment.to_dict() for payment in payments],
        "total": len(payments)
    })

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