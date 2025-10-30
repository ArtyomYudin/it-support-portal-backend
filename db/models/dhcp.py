from decimal import Decimal

from sqlalchemy import String, DateTime, Integer, UniqueConstraint, ForeignKey, Numeric, Index
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional

from db.database import Base


class DhcpScope(Base):
    __tablename__ = "dhcp_scope"

    id: Mapped[int] = mapped_column(primary_key=True)
    server_address: Mapped[str] = mapped_column(String(45))  # IP или hostname сервера
    scope_id: Mapped[str] = mapped_column(String(39))  # IPv4/IPv6, например "192.168.1.0"
    name: Mapped[Optional[str]] = mapped_column(String(255))
    subnet_mask: Mapped[str] = mapped_column(String(15))
    start_range: Mapped[str] = mapped_column(String(15))
    end_range: Mapped[str] = mapped_column(String(15))
    state: Mapped[str] = mapped_column(String(20))  # Active, Inactive и т.д.

    # Отношения
    statistics: Mapped[list["DhcpScopeStatistics"]] = relationship(back_populates="scope", cascade="all, delete-orphan")
    leases: Mapped[list["DhcpLease"]] = relationship(back_populates="scope", cascade="all, delete-orphan")

    __table_args__ = (Index("uq_dhcp_scope_server_scope", "server_address", "scope_id", unique=True),)

    def __repr__(self) -> str:
        return f"<DhcpScope id={self.id} server={self.server_address} scope={self.scope_id}>"


class DhcpLease(Base):
    __tablename__ = "dhcp_lease"

    id: Mapped[int] = mapped_column(primary_key=True)
    dhcp_scope_id: Mapped[int] = mapped_column(ForeignKey("dhcp_scope.id", ondelete="CASCADE"))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    ip_address: Mapped[str] = mapped_column(String(39))  # IPv4/IPv6
    client_id: Mapped[Optional[str]] = mapped_column(String(255)) # MAC
    host_name: Mapped[Optional[str]] = mapped_column(String(255))
    lease_expiration_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    address_state: Mapped[str] = mapped_column(String(20))  # Active, Offered, etc.
    mac_address: Mapped[Optional[str]] = mapped_column(String(17)) # MAC

    # Отношение
    scope: Mapped["DhcpScope"] = relationship(back_populates="leases")

    # __table_args__ = (UniqueConstraint("scope_id", "ip_address", "collected_at", name="uq_lease_scope_ip_time"),)
    __table_args__ = (
        Index("ix_dhcp_lease_scope_collected", "dhcp_scope_id", "collected_at"),
        Index("ix_dhcp_lease_ip", "ip_address"),
    )


class DhcpScopeStatistics(Base):
    __tablename__ = "dhcp_scope_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    dhcp_scope_id: Mapped[int] = mapped_column(ForeignKey("dhcp_scope.id", ondelete="CASCADE"))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    total_addresses: Mapped[int] = mapped_column(Integer)
    in_use: Mapped[int] = mapped_column(Integer)
    available: Mapped[int] = mapped_column(Integer)
    pending_offers: Mapped[int] = mapped_column(Integer)
    percentage_in_use: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    # Отношение
    scope: Mapped["DhcpScope"] = relationship(back_populates="statistics")

    __table_args__ = (
        Index("ix_dhcp_scope_statistics_collected", "dhcp_scope_id", "collected_at"),
    )