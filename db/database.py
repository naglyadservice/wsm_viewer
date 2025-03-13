from .models import db
import psycopg2
from psycopg2.extras import DictCursor
from config import load_config
from flask_migrate import Migrate, upgrade

def init_db(app):
    """Инициализация базы данных приложения."""
    db.init_app(app)
    
    # Настройка миграций
    Migrate(app, db)
    
    # Автоматическое выполнение миграций при запуске
    with app.app_context():
        upgrade()
        
def create_connection():
    try:
        config = load_config()
        
        connection = psycopg2.connect(
            dbname=config.db.database,
            user=config.db.user,
            password=config.db.password,
            host=config.db.host,
            port=config.db.port,
            cursor_factory=DictCursor
        )
        return connection
    except Exception as e:
        print(f"Ошибка при соединении с PostgreSQL: {e}")
        return None