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
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "1234567890")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 10))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # RabbitMQ
    RMQ_HOST: str = os.getenv("RMQ_HOST", "rabbitmq")
    RMQ_PORT: int = int(os.getenv("RMQ_PORT", 5672))
    RMQ_VIRTUAL_HOST: str = os.getenv("RMQ_VIRTUAL_HOST", "/")
    RMQ_USER: str = os.getenv("RMQ_USER", "rabbitmq")
    RMQ_PASSWORD: str = os.getenv("RMQ_PASSWORD", "rabbitmq")

    # App
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
