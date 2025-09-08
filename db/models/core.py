from uuid import uuid4, UUID
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime, timezone

from db.database import Base


class CoreUser(Base):
    __tablename__ = "core_user"

    # Основной идентификатор — UUID, используется как внутренний и внешний ID
    id: Mapped[UUID] = mapped_column(
        default=uuid4,
        primary_key=True,
        index=True,  # для быстрых запросов по ID в API
        nullable=False
    )

    # Уникальные поля с индексами
    username: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    # Персональные данные
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Статусы
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Даты
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    # updated: Mapped[datetime] = mapped_column(
    #     DateTime,
    #     default=datetime.now(),
    #     onupdate=datetime.now(),
    #     nullable=False
    # )
    # last_login: Mapped[datetime] = mapped_column(
    #     DateTime,
    #     default=datetime.now(),
    #     # onlogin=datetime.now(),
    #     nullable=False
    # )

    # Хэш пароля
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)

    def __str__(self) -> str:
        return self.email

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r}, username={self.username!r})>"