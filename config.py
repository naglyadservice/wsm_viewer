import os
from dotenv import load_dotenv
import secrets

load_dotenv()

class Config:
    MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt.example.com")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "user")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "pass")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    
    # Secret key для сессий и токенов
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(16))

    # Добавляем параметр БД
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///wsm_viewer.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Отключаем предупреждения