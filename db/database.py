from flask_sqlalchemy import SQLAlchemy
from .models import db, User
from werkzeug.security import generate_password_hash
import sqlite3

def init_db(app):
    """Инициализация базы данных приложения."""
    db.init_app(app)
    
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        
        # Проверяем наличие хотя бы одного пользователя
        if User.query.count() == 0:
            # Создаем пользователя admin
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('alex414alex')
            )
            db.session.add(admin_user)
            db.session.commit()

def create_connection():
    """Создание соединения с базой данных для выполнения прямых SQL-запросов."""
    try:
        connection = sqlite3.connect('wsm_viewer.db')
        connection.row_factory = sqlite3.Row  # Чтобы получать результаты как словари
        return connection
    except Exception as e:
        print(f"Ошибка при соединении с SQLite: {e}")
        return None