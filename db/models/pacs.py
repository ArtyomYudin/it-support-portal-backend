from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from db.database import Base

if TYPE_CHECKING:
    from .employee import Employee, EmployeeCard


class AccessPoint(Base):
    __tablename__ = "pacs_access_point"

    system_id: Mapped[int] = mapped_column(primary_key=True, default=0)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    # связь с событиями
    events: Mapped[List["Event"]] = relationship(back_populates="ap")


class CardOwner(Base):
    __tablename__ = "pacs_card_owner"

    system_id: Mapped[int] = mapped_column(primary_key=True, default=0)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    firstname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    secondname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lastname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    events: Mapped[List["Event"]] = relationship(back_populates="owner")
    # связь через таблицу employee_card
    card_employees: Mapped[List["EmployeeCard"]] = relationship(back_populates="card")
    employees: Mapped[List["Employee"]] = relationship(
        secondary="employee_card", back_populates="cards"
    )


class Event(Base):
    __tablename__ = "pacs_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    ap_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pacs_access_point.system_id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pacs_card_owner.system_id"), index=True)

    card_number: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[int] = mapped_column(Integer, nullable=False)

    ap: Mapped[Optional[AccessPoint]] = relationship(back_populates="events")
    owner: Mapped[Optional[CardOwner]] = relationship(back_populates="events")