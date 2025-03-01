from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, login_required, current_user
from config import Config
from api.routes import api
from mqtt.client import devices, client  # Запускаем MQTT при старте
from auth import init_auth, User, users, check_auth

# Инициализация Flask-приложения
app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.FLASK_PORT, debug=True)