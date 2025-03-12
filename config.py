from dataclasses import dataclass
from sqlalchemy.engine.url import URL
from environs import Env
import secrets

@dataclass
class MQTTConfig:
    broker: str
    port: int
    username: str
    password: str

    @staticmethod
    def from_env(env: Env):
        broker = env.str("MQTT_BROKER", "mqtt.example.com")
        port = env.int("MQTT_PORT", 1883)
        username = env.str("MQTT_USERNAME", "user")
        password = env.str("MQTT_PASSWORD", "pass")
        return MQTTConfig(
            broker=broker, port=port, username=username, password=password
        )


@dataclass
class FlaskConfig:
    port: int
    secret_key: str

    @staticmethod
    def from_env(env: Env):
        port = env.int("FLASK_PORT", 5000)
        secret_key = env.str("SECRET_KEY", None)
        
        if not secret_key:
            secret_key = secrets.token_hex(16)
        return FlaskConfig(port=port, secret_key=secret_key)
    

@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: int = 5432

    def construct_sqlalchemy_url(self, driver="psycopg2", host=None, port=None) -> str:
        if not host:
            host = self.host
        if not port:
            port = self.port
        uri = URL.create(
            drivername=f"postgresql+{driver}",
            username=self.user,
            password=self.password,
            host=host,
            port=port,
            database=self.database,
        )
        return uri.render_as_string(hide_password=False)

    @staticmethod
    def from_env(env: Env):
        host = env.str("DB_HOST")
        password = env.str("POSTGRES_PASSWORD")
        user = env.str("POSTGRES_USER")
        database = env.str("POSTGRES_DB")
        port = env.int("DB_PORT", 5432)
        return DbConfig(
            host=host, password=password, user=user, database=database, port=port
        )


@dataclass
class Miscellaneous:
    monobank_api_key: str = ""

    @staticmethod
    def from_env(env: Env):
        monobank_api_key = env.str("MONOBANK_API_KEY", "")
        return Miscellaneous(monobank_api_key=monobank_api_key)


@dataclass
class Config:
    mqtt: MQTTConfig
    flask: FlaskConfig
    db: DbConfig
    misc: Miscellaneous


def load_config(path: str = None) -> Config:
    env = Env()
    env.read_env(path)

    return Config(
        mqtt=MQTTConfig.from_env(env),
        flask=FlaskConfig.from_env(env),
        db=DbConfig.from_env(env),
        misc=Miscellaneous.from_env(env)
    )