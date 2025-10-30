from pydantic_settings import BaseSettings
from typing import Optional, List

import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DEBUG_MODE: bool = bool(os.getenv("DEBUG_MODE", "False").lower())

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

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "redis")

    # Zabbix
    ZABBIX_HOST: str = os.getenv("ZABBIX_HOST", "localhost")
    ZABBIX_AUTH_TOKEN: str = os.getenv("ZABBIX_AUTH_TOKEN", "zabbix_token")

    # VPN
    DEFAULT_VPN_DOMAIN: str = os.getenv("DEFAULT_VPN_DOMAIN", "center-inform.ru")
    MAX_SESSION_HOURS: int = os.getenv("MAX_SESSION_HOURS", 24)

    #IMAP
    IMAP_HOST: str = os.getenv("IMAP_HOST", "outlook.center-inform.ru")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
    IMAP_TLS : bool = bool(os.getenv("IMAP_TLS", "False").lower())
    IMAP_USER: str = os.getenv("IMAP_USER", "itsupport@center-inform.ru")
    IMAP_PASSWORD : str = os.getenv("IMAP_PASSWORD", "CixR55bjF341")

    # DHCP
    DHCP_SERVERS: List[str] = [
        s.strip() for s in os.getenv("DHCP_SERVERS", "janet.center-inform.ru").split(",")
    ]
    DHCP_USER: str = os.getenv("DHCP_USER", "center-inform\\itsupport")  # обязательно экранирование
    DHCP_PASSWORD : str = os.getenv("DHCP_PASSWORD", "CixR55bjF341")

    # Windows AD kerberos
    KERBEROS_USER:str = os.getenv("KERBEROS_USER", "itsupport@CENTER-INFORM.RU")
    KERBEROS_PASSWORD: str = os.getenv("KERBEROS_PASSWORD", "CixR55bjF341")


    # App
    HOST: str = "0.0.0.0"
    PORT: int = 8888

    class Config:
        env_file = ".env"

settings = Settings()
