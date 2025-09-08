import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import getpass
import re
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from sqlalchemy import select

from db.models import CoreUser
from db.database import Base  # Опционально для создания таблиц
from core.settings import settings

# Настройка хеширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# URL БД (можно переопределить через .env)
DATABASE_URL = (
    "postgresql+asyncpg://"
    f"{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}"
    f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}"
    f"/{settings.DATABASE_NAME}"
)

engine = create_async_engine(DATABASE_URL, echo=False)  # echo=True для отладки
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Валидация email
def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


# Валидация пароля (минимум 8 символов)
def validate_password(password: str) -> bool:
    return len(password) >= 8


# Интерактивный ввод данных
def collect_user_data():
    print("\n" + "="*50)
    print("    Создание суперпользователя")
    print("="*50)

    while True:
        email = input("Email: ").strip()
        if validate_email(email):
            break
        print("Неверный формат email. Попробуйте снова.")

    while True:
        username = input("Username: ").strip()
        if username and len(username) >= 3:
            break
        print("Username должен быть не короче 3 символов.")

    while True:
        first_name = input("Имя: ").strip()
        if first_name:
            break
        print("Имя обязательно.")

    while True:
        last_name = input("Фамилия: ").strip()
        if last_name:
            break
        print("Фамилия обязательна.")

    while True:
        password = getpass.getpass("Пароль (не будет отображаться): ")
        if validate_password(password):
            password2 = getpass.getpass("Повторите пароль: ")
            if password == password2:
                break
            else:
                print("Пароли не совпадают.")
        else:
            print("Пароль должен быть не менее 8 символов.")

    return {
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
    }


async def create_superuser():
    user_data = collect_user_data()

    async with AsyncSessionLocal() as session:
        # Проверяем дубликаты
        existing = await session.execute(
            select(CoreUser).where(
                (CoreUser.email == user_data["email"]) |
                (CoreUser.username == user_data["username"])
            )
        )
        if existing.scalar_one_or_none():
            print(f"\nПользователь с email '{user_data['email']}' или username '{user_data['username']}' уже существует.")
            return

        # Хешируем пароль
        hashed_password = pwd_context.hash(user_data["password"])

        # Создаём пользователя
        superuser = CoreUser(
            id=uuid4(),
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_active=True,
            is_superuser=True,
            created=datetime.now(timezone.utc),  # Лучше использовать UTC
            password_hash=hashed_password,
        )

        session.add(superuser)
        await session.commit()
        await session.refresh(superuser)

        print(f"\nСуперпользователь успешно создан!")
        print(f"   Email: {superuser.email}")
        print(f"   Username: {superuser.username}")
        print(f"   ID: {superuser.id}")


# Опционально: Создать таблицы, если их нет
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    # Раскомментируйте, если нужно создать таблицы автоматически
    # print("Создание таблиц (если не существуют)...")
    # asyncio.run(init_models())

    print("👤 Запуск создания суперпользователя...")
    asyncio.run(create_superuser())