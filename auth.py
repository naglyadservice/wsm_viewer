from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from flask import request, Response

# Простой пользовательский класс
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Словарь для хранения пользователей (в реальном приложении это была бы база данных)
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
