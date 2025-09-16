from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from datetime import datetime, timezone
from typing import Optional

from db.database import Base

class CiscoVPNEvent(Base):
    __tablename__ = "cisco_vpn_event"

    id: Mapped[int] = mapped_column(primary_key=True, default=0)
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True
    )
    host: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    event: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)