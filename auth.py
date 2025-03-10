from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from flask import request, Response
from db.models import User as DbUser

# Пользовательский класс для Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Словарь для хранения пользователей в памяти (используется до перехода полностью на БД)
users = {
    'admin': User(1, 'admin', generate_password_hash('alex414alex'))  # Используйте более надежный пароль!
}

# Функция для инициализации авторизации
def init_auth(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        # Сначала пытаемся найти пользователя в БД
        try:
            db_user = DbUser.query.get(int(user_id))
            if db_user:
                return User(db_user.id, db_user.username, db_user.password_hash)
        except:
            pass
        
        # Если не нашли в БД или произошла ошибка, используем словарь в памяти
        for user in users.values():
            if str(user.id) == user_id:
                return user
        return None

# Функция для HTTP Basic Auth
def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def check_auth(username, password):
    # Проверяем сначала в БД
    try:
        db_user = DbUser.query.filter_by(username=username).first()
        if db_user and check_password_hash(db_user.password_hash, password):
            user = User(db_user.id, db_user.username, db_user.password_hash)
            login_user(user)
            return True
    except:
        pass
    
    # Если не нашли в БД или произошла ошибка, используем словарь в памяти
    user = users.get(username)
    if user and user.check_password(password):
        login_user(user)
        return True
    return False

def authenticate():
    return Response(
        'Требуется авторизация', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )