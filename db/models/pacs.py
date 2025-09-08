from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional, List
from datetime import datetime

from db.database import Base

class AccessPoint(Base):
    __tablename__ = "pacs_access_point"

    system_id: Mapped[int] = mapped_column(primary_key=True, default=0)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    # связь с событиями
    events: Mapped[List["Event"]] = relationship(back_populates="ap")

    def __str__(self) -> str:
        return f"AccessPoint({self.system_id}: {self.name})"

    def __repr__(self) -> str:
        return f"<AccessPoint(system_id={self.system_id}, name='{self.name}')>"


class CardOwner(Base):
    __tablename__ = "pacs_card_owner"

    system_id: Mapped[int] = mapped_column(primary_key=True, default=0)
    firstname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    secondname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lastname: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)

    events: Mapped[List["Event"]] = relationship(back_populates="owner")

    def __str__(self) -> str:
        return f"{self.lastname or ''} {self.firstname or ''} {self.secondname or ''}".strip()

    def __repr__(self) -> str:
        return (
            f"<CardOwner(system_id={self.system_id}, "
            f"firstname='{self.firstname}', "
            f"secondname='{self.secondname}', "
            f"lastname='{self.lastname}')>"
        )

class Event(Base):
    __tablename__ = "pacs_event"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    ap_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pacs_access_point.system_id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pacs_card_owner.system_id"), index=True)

    card: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[int] = mapped_column(Integer, nullable=False)

    ap: Mapped[Optional[AccessPoint]] = relationship(back_populates="events")
    owner: Mapped[Optional[CardOwner]] = relationship(back_populates="events")

    def __str__(self) -> str:
        return f"Event({self.created}, card={self.card}, code={self.code})"

    def __repr__(self) -> str:
        return (
            f"<Event(id={self.id}, created={self.created}, "
            f"ap_id={self.ap_id}, owner_id={self.owner_id}, "
            f"card={self.card}, code={self.code})>"
        )
    