from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_migrate import Migrate
from flask import current_app

db = SQLAlchemy()
migrate = Migrate()  # Отложенная инициализация миграций

class Device(db.Model):
    """Модель для хранения информации об устройствах"""
    __tablename__ = 'devices'
    
    id = db.Column(db.String(50), primary_key=True)  # device_id как основной ключ
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    monobank_api_key = db.Column(db.String(255), nullable=True)
    
    # Отношения с другими таблицами
    states = db.relationship('DeviceState', backref='device', lazy=True, cascade="all, delete-orphan")
    settings = db.relationship('DeviceSetting', backref='device', lazy=True, cascade="all, delete-orphan")
    configs = db.relationship('DeviceConfig', backref='device', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='device', lazy=True, cascade="all, delete-orphan")
    sales = db.relationship('Sale', backref='device', lazy=True, cascade="all, delete-orphan")
    collections = db.relationship('Collection', backref='device', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Device {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'monobank_api_key': self.monobank_api_key
        }


class DeviceState(db.Model):
    """Модель для хранения состояний устройств"""
    __tablename__ = 'device_states'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    operating_mode = db.Column(db.String(50), nullable=True)
    summa_in_box = db.Column(db.Integer, nullable=True)  # в копейках
    liters_in_tank = db.Column(db.Integer, nullable=True)  # в сантилитрах
    tank_low_level_sensor = db.Column(db.Boolean, nullable=True)
    tank_high_level_sensor = db.Column(db.Boolean, nullable=True)
    deposit_box_sensor = db.Column(db.Boolean, nullable=True)
    door_sensor = db.Column(db.Boolean, nullable=True)
    coin_state = db.Column(db.String(50), nullable=True)
    bill_state = db.Column(db.String(50), nullable=True)
    errors_json = db.Column(db.Text, nullable=True)  # JSON представление ошибок
    
    def __repr__(self):
        return f'<DeviceState {self.device_id} at {self.created}>'
    
    @property
    def errors(self):
        """Получение ошибок из JSON"""
        if self.errors_json:
            return json.loads(self.errors_json)
        return {}
    
    @errors.setter
    def errors(self, value):
        """Сохранение ошибок в JSON"""
        if value:
            self.errors_json = json.dumps(value)
        else:
            self.errors_json = None
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'created': self.created.isoformat() if self.created else None,
            'operatingMode': self.operating_mode,
            'summaInBox': self.summa_in_box,
            'litersInTank': self.liters_in_tank,
            'tankLowLevelSensor': self.tank_low_level_sensor,
            'tankHighLevelSensor': self.tank_high_level_sensor,
            'depositBoxSensor': self.deposit_box_sensor,
            'doorSensor': self.door_sensor,
            'coinState': self.coin_state,
            'billState': self.bill_state,
            'errors': self.errors
        }


class DeviceSetting(db.Model):
    """Модель для хранения настроек устройств"""
    __tablename__ = 'device_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    request_id = db.Column(db.Integer, nullable=True)
    max_payment = db.Column(db.Integer, nullable=True)
    min_pay_pass = db.Column(db.Integer, nullable=True)
    max_pay_pass = db.Column(db.Integer, nullable=True)
    delta_pay_pass = db.Column(db.Integer, nullable=True)
    tariff_per_liter_1 = db.Column(db.Integer, nullable=True)
    tariff_per_liter_2 = db.Column(db.Integer, nullable=True)
    pulses_per_liter_1 = db.Column(db.Integer, nullable=True)
    pulses_per_liter_2 = db.Column(db.Integer, nullable=True)
    pulses_per_liter_3 = db.Column(db.Integer, nullable=True)
    time_one_pay = db.Column(db.Integer, nullable=True)
    liters_in_full_tank = db.Column(db.Integer, nullable=True)
    time_servis_mode = db.Column(db.Integer, nullable=True)
    spill_timer = db.Column(db.Integer, nullable=True)
    spill_amount = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<DeviceSetting {self.device_id} at {self.created}>'
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'created': self.created.isoformat() if self.created else None,
            'request_id': self.request_id,
            'maxPayment': self.max_payment,
            'minPayPass': self.min_pay_pass,
            'maxPayPass': self.max_pay_pass,
            'deltaPayPass': self.delta_pay_pass,
            'tariffPerLiter_1': self.tariff_per_liter_1,
            'tariffPerLiter_2': self.tariff_per_liter_2,
            'pulsesPerLiter_1': self.pulses_per_liter_1,
            'pulsesPerLiter_2': self.pulses_per_liter_2,
            'pulsesPerLiter_3': self.pulses_per_liter_3,
            'timeOnePay': self.time_one_pay,
            'litersInFullTank': self.liters_in_full_tank,
            'timeServisMode': self.time_servis_mode,
            'spillTimer': self.spill_timer,
            'spillAmount': self.spill_amount
        }


class DeviceConfig(db.Model):
    """Модель для хранения конфигурации устройств"""
    __tablename__ = 'device_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    request_id = db.Column(db.Integer, nullable=True)
    wifi_sta_ssid = db.Column(db.String(100), nullable=True)
    wifi_sta_pass = db.Column(db.String(100), nullable=True)
    ntp_server = db.Column(db.String(100), nullable=True)
    time_zone = db.Column(db.Integer, nullable=True)
    broker_uri = db.Column(db.String(100), nullable=True)
    broker_port = db.Column(db.Integer, nullable=True)
    broker_user = db.Column(db.String(100), nullable=True)
    broker_pass = db.Column(db.String(100), nullable=True)
    ota_server = db.Column(db.String(100), nullable=True)
    ota_port = db.Column(db.Integer, nullable=True)
    bill_table_json = db.Column(db.Text, nullable=True)  # JSON массив
    coin_table_json = db.Column(db.Text, nullable=True)  # JSON массив
    coin_validator_type = db.Column(db.String(20), nullable=True)
    coin_pulse_price = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<DeviceConfig {self.device_id} at {self.created}>'
    
    @property
    def bill_table(self):
        """Получение таблицы номиналов купюр из JSON"""
        if self.bill_table_json:
            return json.loads(self.bill_table_json)
        return []
    
    @bill_table.setter
    def bill_table(self, value):
        """Сохранение таблицы номиналов купюр в JSON"""
        if value:
            self.bill_table_json = json.dumps(value)
        else:
            self.bill_table_json = None
    
    @property
    def coin_table(self):
        """Получение таблицы номиналов монет из JSON"""
        if self.coin_table_json:
            return json.loads(self.coin_table_json)
        return []
    
    @coin_table.setter
    def coin_table(self, value):
        """Сохранение таблицы номиналов монет в JSON"""
        if value:
            self.coin_table_json = json.dumps(value)
        else:
            self.coin_table_json = None
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'created': self.created.isoformat() if self.created else None,
            'request_id': self.request_id,
            'wifi_STA_ssid': self.wifi_sta_ssid,
            'wifi_STA_pass': self.wifi_sta_pass,
            'ntp_server': self.ntp_server,
            'timeZone': self.time_zone,
            'broker_uri': self.broker_uri,
            'broker_port': self.broker_port,
            'broker_user': self.broker_user,
            'broker_pass': self.broker_pass,
            'OTA_server': self.ota_server,
            'OTA_port': self.ota_port,
            'bill_table': self.bill_table,
            'coin_table': self.coin_table,
            'coinValidatorType': self.coin_validator_type,
            'coinPulsePrice': self.coin_pulse_price
        }


class Payment(db.Model):
    """Модель для хранения платежей"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Integer, nullable=False)  # в копейках
    payment_type = db.Column(db.String(20), nullable=False)  # 'qrcode', 'free', 'monobank', 'coin', 'bill'
    order_id = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=True)  # 'pending', 'confirmed', 'failed'
    confirmed_at = db.Column(db.DateTime, nullable=True)
    monobank_invoice_id = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<Payment {self.payment_type} {self.amount} for {self.device_id}>'
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'created': self.created.isoformat() if self.created else None,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'order_id': self.order_id,
            'status': self.status,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'monobank_invoice_id': self.monobank_invoice_id
        }


class Sale(db.Model):
    """Модель для хранения продаж"""
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    external_id = db.Column(db.Integer, nullable=True)  # ID продажи из устройства
    created = db.Column(db.DateTime, default=datetime.utcnow)
    add_coin = db.Column(db.Integer, default=0)  # Внесено монет (коп)
    add_bill = db.Column(db.Integer, default=0)  # Внесено купюр (коп)
    add_prev = db.Column(db.Integer, default=0)  # Перенесено из предыдущей продажи (коп)
    add_free = db.Column(db.Integer, default=0)  # Внесено через RemoteXY (коп)
    add_qr = db.Column(db.Integer, default=0)  # Внесено через интернет (коп)
    add_pp = db.Column(db.Integer, default=0)  # Внесено через PayPass (коп)
    out_liters_1 = db.Column(db.Integer, default=0)  # Проданные литры тип 1 (0.01 л)
    out_liters_2 = db.Column(db.Integer, default=0)  # Проданные литры тип 2 (0.01 л)
    sale_type = db.Column(db.String(20), nullable=True)  # Тип продажи
    card_code = db.Column(db.String(20), nullable=True)  # Код карты
    card_balance_in = db.Column(db.Integer, nullable=True)  # Входной баланс на карте (коп)
    card_balance_out = db.Column(db.Integer, nullable=True)  # Оставшийся баланс на карте (коп)
    ack_sent = db.Column(db.Boolean, default=False)  # Отправлено ли подтверждение
    payment_source = db.Column(db.String(100), nullable=True) 
    
    def __repr__(self):
        return f'<Sale {self.id} for {self.device_id}>'
    
    @property
    def total_amount(self):
        """Общая сумма продажи"""
        return self.add_coin + self.add_bill + self.add_prev + self.add_free + self.add_qr + self.add_pp
    
    @property
    def total_liters(self):
        """Общее количество проданной воды"""
        return self.out_liters_1 + self.out_liters_2
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'external_id': self.external_id,
            'created': self.created.isoformat() if self.created else None,
            'addCoin': self.add_coin,
            'addBill': self.add_bill,
            'addPrev': self.add_prev,
            'addFree': self.add_free,
            'add_QR': self.add_qr,
            'add_PP': self.add_pp,
            'OutLiters_1': self.out_liters_1,
            'OutLiters_2': self.out_liters_2,
            'saleType': self.sale_type,
            'cardCode': self.card_code,
            'cardBalanceIn': self.card_balance_in,
            'cardBalanceOut': self.card_balance_out,
            'totalAmount': self.total_amount,
            'totalLiters': self.total_liters
        }


class Collection(db.Model):
    """Модель для хранения инкассаций"""
    __tablename__ = 'collections'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    external_id = db.Column(db.Integer, nullable=True)  # ID инкассации из устройства
    created = db.Column(db.DateTime, default=datetime.utcnow)
    coin_1 = db.Column(db.Integer, default=0)  # Количество монет типа 1
    coin_2 = db.Column(db.Integer, default=0)  # Количество монет типа 2
    coin_3 = db.Column(db.Integer, default=0)  # Количество монет типа 3
    coin_4 = db.Column(db.Integer, default=0)  # Количество монет типа 4
    coin_5 = db.Column(db.Integer, default=0)  # Количество монет типа 5
    coin_6 = db.Column(db.Integer, default=0)  # Количество монет типа 6
    bill_1 = db.Column(db.Integer, default=0)  # Количество купюр типа 1
    bill_2 = db.Column(db.Integer, default=0)  # Количество купюр типа 2
    bill_3 = db.Column(db.Integer, default=0)  # Количество купюр типа 3
    bill_4 = db.Column(db.Integer, default=0)  # Количество купюр типа 4
    bill_5 = db.Column(db.Integer, default=0)  # Количество купюр типа 5
    bill_6 = db.Column(db.Integer, default=0)  # Количество купюр типа 6
    bill_7 = db.Column(db.Integer, default=0)  # Количество купюр типа 7
    bill_8 = db.Column(db.Integer, default=0)  # Количество купюр типа 8
    amount = db.Column(db.Integer, default=0)  # Общая сумма инкассации (коп)
    ack_sent = db.Column(db.Boolean, default=False)  # Отправлено ли подтверждение
    
    def __repr__(self):
        return f'<Collection {self.id} for {self.device_id}>'
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'external_id': self.external_id,
            'created': self.created.isoformat() if self.created else None,
            'coin_1': self.coin_1,
            'coin_2': self.coin_2,
            'coin_3': self.coin_3,
            'coin_4': self.coin_4,
            'coin_5': self.coin_5,
            'coin_6': self.coin_6,
            'bill_1': self.bill_1,
            'bill_2': self.bill_2,
            'bill_3': self.bill_3,
            'bill_4': self.bill_4,
            'bill_5': self.bill_5,
            'bill_6': self.bill_6,
            'bill_7': self.bill_7,
            'bill_8': self.bill_8,
            'amount': self.amount
        }


class AckMessage(db.Model):
    """Модель для хранения подтверждений (ACK)"""
    __tablename__ = 'ack_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    message_type = db.Column(db.String(20), nullable=False)  # 'setting', 'config', 'reboot', 'payment', 'action'
    code = db.Column(db.Integer, nullable=True)
    message = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<AckMessage {self.message_type} for {self.device_id}>'
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'created': self.created.isoformat() if self.created else None,
            'message_type': self.message_type,
            'code': self.code,
            'message': self.message
        }


class DisplayInfo(db.Model):
    """Модель для хранения информации с дисплея"""
    __tablename__ = 'display_info'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), db.ForeignKey('devices.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    line_1 = db.Column(db.String(255), nullable=True)
    line_2 = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<DisplayInfo for {self.device_id} at {self.created}>'
    
    def to_dict(self):
        """Преобразование в словарь для API"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'created': self.created.isoformat() if self.created else None,
            'line_1': self.line_1,
            'line_2': self.line_2
        }


class User(db.Model):
    """Модель для хранения пользователей"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Преобразование в словарь для API (без пароля)"""
        return {
            'id': self.id,
            'username': self.username,
            'created': self.created.isoformat() if self.created else None,
            'is_active': self.is_active
        }