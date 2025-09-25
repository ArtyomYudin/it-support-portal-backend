from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime, timezone

from db.database import Base

class AvayaCDR(Base):
    __tablename__ = "avaya_cdr"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    duration: Mapped[int] = mapped_column()
    calling_number: Mapped[str] =  mapped_column(String(25))
    called_number: Mapped[str] =  mapped_column(String(25))
    call_code: Mapped[str] = mapped_column(String(2))
