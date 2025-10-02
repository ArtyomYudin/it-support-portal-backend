from sqlalchemy import String, Integer, ForeignKey, LargeBinary, DateTime, Text, Date, Sequence
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

from db.database import Base

# Последовательность для регистрационного номера
request_reg_number_seq = Sequence("request_reg_number_seq", start=1, increment=1)

class UserRequest(Base):
    __tablename__ = "user_request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    change_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Регистрационный номер — берётся из последовательности
    reg_number: Mapped[int] = mapped_column(
        Integer,
        request_reg_number_seq,
        server_default=request_reg_number_seq.next_value(),
        unique=True,
        nullable=False,
    )
    creator_upn: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    initiator_upn: Mapped[str] = mapped_column(String(40))
    executor_upn: Mapped[str] = mapped_column(String(40))
    service_id: Mapped[int] = mapped_column(Integer)
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status_id: Mapped[int] = mapped_column(Integer)
    priority_id: Mapped[int] = mapped_column(Integer)
    deadline: Mapped[Date] = mapped_column(Date)

    # Свойство для отображения с ведущими нулями
    @property
    def formatted_reg_number(self) -> str:
        return f"{self.reg_number:06d}"  # 6 цифр, например: 000305

class UserRequestStatus(Base):
    __tablename__ = "user_request_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40))
    icon: Mapped[Optional[String]] = mapped_column(String(32), nullable=True)


class UserRequestPriority(Base):
    __tablename__ = "user_request_priority"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40))
    color: Mapped[Optional[String]] = mapped_column(String(32), nullable=True)


class UserRequestService(Base):
    __tablename__ = "user_request_service"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40))


class UserRequestLifeCycle(Base):
    __tablename__ = "user_request_life_cycle"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reg_number: Mapped[int] = mapped_column(Integer)
    user_principal_name: Mapped[str] = mapped_column(String(40))
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_type: Mapped[str] = mapped_column(String(40))
    event_value: Mapped[str] = mapped_column(Text)


class UserRequestAttachment(Base):
    __tablename__ = "user_request_attachment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(String(10))
    file_name: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer)
    file_type: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(255))

