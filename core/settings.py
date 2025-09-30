from pydantic_settings import BaseSettings
from typing import Optional

import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DEBUG_MODE: bool = bool(os.getenv("DEBUG_MODE", False).lower())

    # Database
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "postgres")
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "postgres")
    DATABASE_HOST: str = os.getenv("DATABASE_USER", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", 5432))
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "IOH7aLvm5j4EbKvsSjmx3v3PaY1yKss")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 10))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # RabbitMQ
    RMQ_HOST: str = os.getenv("RMQ_HOST", "rabbitmq")
    RMQ_PORT: int = int(os.getenv("RMQ_PORT", 5672))
    RMQ_VIRTUAL_HOST: str = os.getenv("RMQ_VIRTUAL_HOST", "/")
    RMQ_BACKEND_USER: str = os.getenv("RMQ_BACKEND_USER", "rabbitmq")
    RMQ_BACKEND_PASSWORD: str = os.getenv("RMQ_BACKEND_PASSWORD", "rabbitmq")
    RMQ_CELERY_USER: str = os.getenv("RMQ_CELERY_USER", "rabbitmq")
    RMQ_CELERY_PASSWORD: str = os.getenv("RMQ_CELERY_PASSWORD", "rabbitmq")
    RMQ_PACS_EXCHANGE_NAME: str = os.getenv("RMQ_PACS_EXCHANGE_NAME", "quest")
    RMQ_CELERY_BEAT_EXCHANGE_NAME: str = os.getenv("RMQ_CELERY_BEAT_EXCHANGE_NAME", "celery_beat")

    # Zabbix
    ZABBIX_HOST: str = os.getenv("ZABBIX_HOST", "localhost")
    ZABBIX_AUTH_TOKEN: str = os.getenv("ZABBIX_AUTH_TOKEN", "zabbix_token")

    # VPN
    DEFAULT_VPN_DOMAIN: str = os.getenv("DEFAULT_VPN_DOMAIN", "center-inform.ru")

    # App
    HOST: str = "0.0.0.0"
    PORT: int = 8888

    class Config:
        env_file = ".env"

settings = Settings()
