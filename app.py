from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, current_user
from config import Config
from api.routes import api
from mqtt.client import devices, client  # Запускаем MQTT при старте
from auth import init_auth, User, users, check_auth
import requests
import uuid
import json
from datetime import datetime, timedelta

# Инициализация Flask-приложения
app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
app.config['JSON_AS_ASCII'] = False  # Для корректной работы с кириллицей

# Секретный ключ для сессий
app.secret_key = Config.SECRET_KEY

# Инициализация базы данных (пока не используется, но может пригодиться)
# db = SQLAlchemy(app)

# Инициализация авторизации
init_auth(app)

# Регистрация API-маршрутов
app.register_blueprint(api, url_prefix="/api")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = users.get(username)
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next', url_for('index'))
            return redirect(next_page)
        else:
            error = "Неверное имя пользователя или пароль"
    
    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    """Главная страница: список устройств"""
    return render_template("index.html")

@app.route("/device/<device_id>")
@login_required
def device_page(device_id):
    """Страница конкретного устройства с настройками"""
    if device_id not in devices:
        return "Device not found", 404
    return render_template("device.html", device_id=device_id)

@app.route("/monopay/<device_id>", methods=["GET", "POST"])
def monopay_page(device_id):
    """Публичная страница оплаты через Monobank"""
    # Проверяем, существует ли устройство
    if device_id not in devices:
        return "Устройство не найдено", 404
    
    error = None
    success = None
    
    if request.method == "POST":
        try:
            # Получаем сумму оплаты из формы (в гривнах)
            amount = float(request.form.get("amount", 0))
            
            # Проверяем валидность суммы
            if amount <= 0:
                error = "Пожалуйста, введите корректную сумму"
            else:
                # Конвертируем в копейки для API
                amount_kopeek = int(amount * 100)
                
                # Получаем API ключ устройства
                api_key = devices.get(device_id, {}).get("monobank_api_key", "")
                
                if not api_key:
                    error = "API ключ Monobank не настроен для данного устройства"
                else:
                    # Создаем уникальный ID заказа
                    order_id = f"wsm_{device_id}_{uuid.uuid4().hex[:8]}"
                    
                    # Подготавливаем данные для запроса к Monobank API
                    payload = {
                        "amount": amount_kopeek,
                        "ccy": 980,  # Код валюты для UAH
                        "merchantPaymInfo": {
                            "reference": order_id,
                            "destination": f"Пополнение водомата {device_id}",
                            "basketOrder": [
                                {
                                    "name": "Вода",
                                    "qty": 1,
                                    "sum": amount_kopeek,
                                    "code": "water"
                                }
                            ]
                        },
                        "redirectUrl": request.url_root + f"monopay/success/{device_id}",
                        "webHookUrl": request.url_root + f"api/webhook/monobank/{device_id}/{order_id}/{amount_kopeek}",
                        "validity": 3600,  # Срок действия в секундах (1 час)
                        "paymentType": "debit"  # Тип платежа
                    }
                    
                    # Отправляем запрос к Monobank API
                    response = requests.post(
                        "https://api.monobank.ua/api/merchant/invoice/create",
                        json=payload,
                        headers={
                            "X-Token": api_key,
                            "Content-Type": "application/json"
                        }
                    )
                    
                    # Проверяем ответ
                    if response.status_code == 200:
                        result = response.json()
                        payment_url = result.get("pageUrl")
                        if payment_url:
                            # Перенаправляем на страницу оплаты Monobank
                            return redirect(payment_url)
                        else:
                            error = "Ошибка при создании счета: отсутствует URL страницы оплаты"
                    else:
                        # В случае ошибки от API
                        try:
                            error_data = response.json()
                            error = f"Ошибка API Monobank: {error_data.get('errText', 'Неизвестная ошибка')}"
                        except:
                            error = f"Ошибка API Monobank: {response.status_code}"
        
        except ValueError:
            error = "Пожалуйста, введите корректную сумму"
        except Exception as e:
            error = f"Произошла ошибка: {str(e)}"
    
    return render_template("monopay.html", device_id=device_id, error=error, success=success)

@app.route("/monopay/success/<device_id>", methods=["GET"])
def monopay_success(device_id):
    """Страница успешной оплаты"""
    return render_template("monopay_success.html", device_id=device_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.FLASK_PORT, debug=True)