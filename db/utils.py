import json
import traceback
from datetime import datetime

from flask import current_app
from sqlalchemy.exc import IntegrityError

from .models import (
    AckMessage,
    Collection,
    Device,
    DeviceConfig,
    DeviceSetting,
    DeviceState,
    DisplayInfo,
    Payment,
    Sale,
    db,
)


def safe_db_operation(operation):
    """
    Декоратор для безопасного выполнения операций с базой данных
    с логированием ошибок и откатом транзакции
    """

    def wrapper(*args, **kwargs):
        try:
            result = operation(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error in {operation.__name__}: {e}")
            current_app.logger.error(traceback.format_exc())
            return None

    return wrapper


@safe_db_operation
def get_device(device_id):
    """Получение устройства из БД. Если устройства нет, возвращает None."""
    return Device.query.filter_by(id=device_id).first()


@safe_db_operation
def get_or_create_device(device_id):
    """Получить или создать устройство в БД"""
    device = Device.query.filter_by(id=device_id).first()

    if not device:
        try:
            device = Device(
                id=device_id, last_seen=datetime.utcnow(), monobank_api_key=None
            )
            db.session.add(device)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            device = Device.query.filter_by(
                id=device_id
            ).first()  # Повторный запрос после rollback

    return device


@safe_db_operation
def update_device_last_seen(device_id):
    """Обновление времени последнего обнаружения устройства."""
    device = get_or_create_device(device_id)
    if device:
        device.last_seen = datetime.utcnow()
    return device


def get_all_devices():
    """Получение списка всех устройств."""
    try:
        return Device.query.order_by(Device.id).all()
    except Exception as e:
        current_app.logger.error(f"Error getting all devices: {e}")
        current_app.logger.error(traceback.format_exc())
        return []


@safe_db_operation
def save_device_state(device_id, state_data):
    """Сохранение состояния устройства в БД."""
    device = get_or_create_device(device_id)
    if not device:
        current_app.logger.error(
            f"Cannot save state for non-existent device {device_id}"
        )
        return None

    # Создаем новое состояние устройства
    state = DeviceState(
        device_id=device_id,
        created=datetime.utcnow(),
        operating_mode=state_data.get("operatingMode"),
        summa_in_box=state_data.get("summaInBox"),
        liters_in_tank=state_data.get("litersInTank"),
        tank_low_level_sensor=state_data.get("tankLowLevelSensor"),
        tank_high_level_sensor=state_data.get("tankHighLevelSensor"),
        deposit_box_sensor=state_data.get("depositBoxSensor"),
        door_sensor=state_data.get("doorSensor"),
        coin_state=state_data.get("coinState"),
        bill_state=state_data.get("billState"),
    )

    # Если есть ошибки, сохраняем их
    if "errors" in state_data:
        state.errors = json.dumps(state_data["errors"])

    db.session.add(state)
    return state


def get_latest_device_state(device_id):
    """Получение последнего состояния устройства."""
    try:
        return (
            DeviceState.query.filter_by(device_id=device_id)
            .order_by(DeviceState.created.desc())
            .first()
        )
    except Exception as e:
        current_app.logger.error(f"Error getting latest device state: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def save_device_settings(device_id, settings_data):
    """Сохранение настроек устройства в БД."""
    device = get_or_create_device(device_id)
    if not device:
        current_app.logger.error(
            f"Cannot save settings for non-existent device {device_id}"
        )
        return None

    settings = DeviceSetting(
        device_id=device_id,
        created=datetime.utcnow(),
        request_id=settings_data.get("request_id"),
        max_payment=settings_data.get("maxPayment"),
        min_pay_pass=settings_data.get("minPayPass"),
        max_pay_pass=settings_data.get("maxPayPass"),
        delta_pay_pass=settings_data.get("deltaPayPass"),
        tariff_per_liter_1=settings_data.get("tariffPerLiter_1"),
        tariff_per_liter_2=settings_data.get("tariffPerLiter_2"),
        pulses_per_liter_1=settings_data.get("pulsesPerLiter_1"),
        pulses_per_liter_2=settings_data.get("pulsesPerLiter_2"),
        pulses_per_liter_3=settings_data.get("pulsesPerLiter_3"),
        time_one_pay=settings_data.get("timeOnePay"),
        liters_in_full_tank=settings_data.get("litersInFullTank"),
        time_servis_mode=settings_data.get("timeServisMode"),
        spill_timer=settings_data.get("spillTimer"),
        spill_amount=settings_data.get("spillAmount"),
    )

    db.session.add(settings)
    return settings


def get_latest_device_settings(device_id):
    """Получение последних настроек устройства."""
    try:
        return (
            DeviceSetting.query.filter_by(device_id=device_id)
            .order_by(DeviceSetting.created.desc())
            .first()
        )
    except Exception as e:
        current_app.logger.error(f"Error getting latest device settings: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def save_device_config(device_id, config_data):
    """Сохранение конфигурации устройства в БД."""
    device = get_or_create_device(device_id)
    if not device:
        current_app.logger.error(
            f"Cannot save config for non-existent device {device_id}"
        )
        return None

    config = DeviceConfig(
        device_id=device_id,
        created=datetime.utcnow(),
        request_id=config_data.get("request_id"),
        wifi_sta_ssid=config_data.get("wifi_STA_ssid"),
        wifi_sta_pass=config_data.get("wifi_STA_pass"),
        ntp_server=config_data.get("ntp_server"),
        time_zone=config_data.get("timeZone"),
        broker_uri=config_data.get("broker_uri"),
        broker_port=config_data.get("broker_port"),
        broker_user=config_data.get("broker_user"),
        broker_pass=config_data.get("broker_pass"),
        ota_server=config_data.get("OTA_server"),
        ota_port=config_data.get("OTA_port"),
        coin_validator_type=config_data.get("coinValidatorType"),
        coin_pulse_price=config_data.get("coinPulsePrice"),
    )

    # Сохраняем таблицы номиналов
    if "bill_table" in config_data:
        config.bill_table = json.dumps(config_data["bill_table"])

    if "coin_table" in config_data:
        config.coin_table = json.dumps(config_data["coin_table"])

    db.session.add(config)
    return config


def get_latest_device_config(device_id):
    """Получение последней конфигурации устройства."""
    try:
        return (
            DeviceConfig.query.filter_by(device_id=device_id)
            .order_by(DeviceConfig.created.desc())
            .first()
        )
    except Exception as e:
        current_app.logger.error(f"Error getting latest device config: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def save_ack_message(device_id, message_type, ack_data):
    """Сохранение ACK-сообщения в БД."""
    device = get_or_create_device(device_id)

    ack = AckMessage(
        device_id=device_id,
        created=datetime.utcnow(),
        message_type=message_type,
        code=ack_data.get("code"),
        message=json.dumps(ack_data),
    )

    db.session.add(ack)
    return ack


def get_latest_ack_message(device_id, message_type):
    """Получение последнего ACK-сообщения для устройства."""
    try:
        return (
            AckMessage.query.filter_by(device_id=device_id, message_type=message_type)
            .order_by(AckMessage.created.desc())
            .first()
        )
    except Exception as e:
        current_app.logger.error(f"Error getting latest ACK message: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def save_payment(
    device_id,
    payment_type,
    amount,
    order_id=None,
    status="pending",
    monobank_invoice_id=None,
    confirmed_at=None,
):
    """Сохранение платежа в БД."""
    device = get_or_create_device(device_id)

    payment = Payment(
        device_id=device_id,
        created=datetime.utcnow(),
        amount=amount,
        payment_type=payment_type,
        order_id=order_id,
        status=status,
        monobank_invoice_id=monobank_invoice_id,
        confirmed_at=confirmed_at,
    )

    db.session.add(payment)
    return payment


@safe_db_operation
def update_payment_status(payment_id, status, confirmed_at=None):
    """Обновление статуса платежа."""
    payment = Payment.query.get(payment_id)
    if payment:
        payment.status = status
        if confirmed_at:
            payment.confirmed_at = confirmed_at
    return payment


def get_device_payments(device_id, payment_type=None, limit=100):
    """Получение платежей устройства."""
    try:
        query = Payment.query.filter_by(device_id=device_id)

        if payment_type:
            query = query.filter_by(payment_type=payment_type)

        return query.order_by(Payment.created.desc()).limit(limit).all()
    except Exception as e:
        current_app.logger.error(f"Error getting device payments: {e}")
        current_app.logger.error(traceback.format_exc())
        return []


@safe_db_operation
def save_display_info(device_id, display_data):
    """Сохранение информации с дисплея в БД."""
    device = get_or_create_device(device_id)

    display = DisplayInfo(
        device_id=device_id,
        created=datetime.utcnow(),
        line_1=display_data.get("line_1"),
        line_2=display_data.get("line_2"),
    )

    db.session.add(display)
    return display


def get_latest_display_info(device_id):
    """Получение последней информации с дисплея устройства."""
    try:
        return (
            DisplayInfo.query.filter_by(device_id=device_id)
            .order_by(DisplayInfo.created.desc())
            .first()
        )
    except Exception as e:
        current_app.logger.error(f"Error getting latest display info: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def update_monobank_api_key(device_id, api_key):
    """Обновление API-ключа Monobank для устройства."""
    device = get_or_create_device(device_id)
    device.monobank_api_key = api_key
    return device


def get_monobank_api_key(device_id):
    """Получение API-ключа Monobank для устройства."""
    try:
        device = get_device(device_id)
        return device.monobank_api_key if device else None
    except Exception as e:
        current_app.logger.error(f"Error getting Monobank API key: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def save_sale(device_id, sale_data):
    """Сохранение продажи с правильным определением метода оплаты"""
    device = get_or_create_device(device_id)

    # Определяем способ оплаты
    payment_sources = []
    if sale_data.get("addCoin", 0) > 0:
        payment_sources.append("cash_coin")
    if sale_data.get("addBill", 0) > 0:
        payment_sources.append("cash_bill")
    if sale_data.get("add_QR", 0) > 0:
        payment_sources.append("qr_code")
    if sale_data.get("add_PP", 0) > 0:
        payment_sources.append("paypass")
    if sale_data.get("addFree", 0) > 0:
        payment_sources.append("free_credit")

    payment_source = ", ".join(payment_sources) if payment_sources else "unknown"

    sale = Sale(
        device_id=device_id,
        external_id=sale_data.get("id"),
        created=datetime.strptime(sale_data.get("created", ""), "%Y-%m-%dT%H:%M:%S")
        if "created" in sale_data
        else datetime.utcnow(),
        add_coin=sale_data.get("addCoin", 0),
        add_bill=sale_data.get("addBill", 0),
        add_prev=sale_data.get("addPrev", 0),
        add_free=sale_data.get("addFree", 0),
        add_qr=sale_data.get("add_QR", 0),
        add_pp=sale_data.get("add_PP", 0),
        out_liters_1=sale_data.get("OutLiters_1", 0),
        out_liters_2=sale_data.get("OutLiters_2", 0),
        sale_type=sale_data.get("saleType"),
        payment_source=payment_source,  # Теперь источник корректный!
    )

    db.session.add(sale)
    return sale


def get_sale(device_id, external_id):
    """Получение продажи по device_id и external_id"""
    try:
        return Sale.query.filter_by(
            device_id=device_id, external_id=external_id
        ).first()
    except Exception as e:
        current_app.logger.error(f"Error getting sale: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def mark_sale_ack_sent(sale_id):
    """Отметка о том, что отправлено подтверждение продажи"""
    sale = Sale.query.get(sale_id)
    if sale:
        sale.ack_sent = True
    return sale


def get_device_sales(device_id, limit=100):
    """Получение продаж устройства"""
    try:
        return (
            Sale.query.filter_by(device_id=device_id)
            .order_by(Sale.created.desc())
            .limit(limit)
            .all()
        )
    except Exception as e:
        current_app.logger.error(f"Error getting device sales: {e}")
        current_app.logger.error(traceback.format_exc())
        return []


@safe_db_operation
def save_collection(device_id, collection_data):
    """Сохранение инкассации в БД"""
    device = get_or_create_device(device_id)

    # Создаем объект инкассации
    collection = Collection(
        device_id=device_id,
        external_id=collection_data.get("id"),
        created=datetime.strptime(
            collection_data.get("created", ""), "%Y-%m-%dT%H:%M:%S"
        )
        if "created" in collection_data
        else datetime.utcnow(),
        coin_1=collection_data.get("coin_1", 0),
        coin_2=collection_data.get("coin_2", 0),
        coin_3=collection_data.get("coin_3", 0),
        coin_4=collection_data.get("coin_4", 0),
        coin_5=collection_data.get("coin_5", 0),
        coin_6=collection_data.get("coin_6", 0),
        bill_1=collection_data.get("bill_1", 0),
        bill_2=collection_data.get("bill_2", 0),
        bill_3=collection_data.get("bill_3", 0),
        bill_4=collection_data.get("bill_4", 0),
        bill_5=collection_data.get("bill_5", 0),
        bill_6=collection_data.get("bill_6", 0),
        bill_7=collection_data.get("bill_7", 0),
        bill_8=collection_data.get("bill_8", 0),
        amount=collection_data.get("amount", 0),
    )

    db.session.add(collection)
    return collection


def get_collection(device_id, external_id):
    """Получение инкассации по device_id и external_id"""
    try:
        return Collection.query.filter_by(
            device_id=device_id, external_id=external_id
        ).first()
    except Exception as e:
        current_app.logger.error(f"Error getting collection: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


@safe_db_operation
def mark_collection_ack_sent(collection_id):
    """Отметка о том, что отправлено подтверждение инкассации"""
    collection = Collection.query.get(collection_id)
    if collection:
        collection.ack_sent = True
    return collection


def get_device_collections(device_id, limit=100):
    """Получение инкассаций устройства"""
    try:
        return (
            Collection.query.filter_by(device_id=device_id)
            .order_by(Collection.created.desc())
            .limit(limit)
            .all()
        )
    except Exception as e:
        current_app.logger.error(f"Error getting device collections: {e}")
        current_app.logger.error(traceback.format_exc())
        return []


# Справочные функции для работы с данными устройств


def get_device_summary(device_id):
    """
    Получение краткой сводки по устройству:
    - последнее состояние
    - последние настройки
    - последняя конфигурация
    """
    try:
        return {
            "device": get_device(device_id),
            "latest_state": get_latest_device_state(device_id),
            "latest_settings": get_latest_device_settings(device_id),
            "latest_config": get_latest_device_config(device_id),
            "recent_sales": get_device_sales(device_id, limit=10),
            "recent_collections": get_device_collections(device_id, limit=10),
        }
    except Exception as e:
        current_app.logger.error(f"Error getting device summary: {e}")
        current_app.logger.error(traceback.format_exc())
        return None


def get_all_devices_summary():
    """
    Получение сводки по всем устройствам
    """
    try:
        devices = get_all_devices()
        return [
            {
                "device_id": device.id,
                "last_seen": device.last_seen,
                "latest_state": get_latest_device_state(device.id),
                "monobank_api_key": device.monobank_api_key,
            }
            for device in devices
        ]
    except Exception as e:
        current_app.logger.error(f"Error getting all devices summary: {e}")
        current_app.logger.error(traceback.format_exc())
        return []
