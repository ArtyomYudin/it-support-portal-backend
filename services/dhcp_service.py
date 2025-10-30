import asyncio
from datetime import datetime, timedelta, date, timezone
import dateutil.parser

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from typing import Optional, List
from core.logging_config import logger
from db.models.dhcp import DhcpScope, DhcpScopeStatistics, DhcpLease
from db.database import AsyncSessionLocal

async def add_dhcp_scope(db: AsyncSession, scopes: list[dict], server: str):
    table = DhcpScope.__table__

    for scope_data in scopes:
        stmt = insert(table).values(
            server_address=server,
            scope_id=scope_data["ScopeId"],
            name=scope_data.get("Name"),
            subnet_mask=scope_data.get("SubnetMask"),
            start_range=scope_data.get("StartRange"),
            end_range=scope_data.get("EndRange"),
            state=scope_data.get("State"),
        ).on_conflict_do_update(
            index_elements=["server_address", "scope_id"],
            set_={
                "name": table.c.name,
                "subnet_mask": table.c.subnet_mask,
                "start_range": table.c.start_range,
                "end_range": table.c.end_range,
                "state": table.c.state,
            },
        )

        await db.execute(stmt)
        logger.info(f"[{server}] Updated DHCP scope {scope_data['ScopeId']} ({scope_data.get('Name', '')})")

    await db.commit()

async def add_dhcp_scope_statistics(db, stats: list[dict], server: str, collected_at: datetime):
    table = DhcpScopeStatistics.__table__

    for item in stats:
        # Находим соответствующий scope
        q = select(DhcpScope.id).where(
            DhcpScope.server_address == server,
            DhcpScope.scope_id == item["ScopeId"]
        )
        result = await db.execute(q)
        scope_id = result.scalar_one_or_none()

        if not scope_id:
            logger.warning(f"[{server}] Scope {item['ScopeId']} not found — skipping stat entry")
            continue

        stmt = insert(table).values(
            dhcp_scope_id=scope_id,
            collected_at=collected_at,
            total_addresses=item.get("TotalAddresses", 0),
            in_use=item.get("AddressesInUse", 0),
            available=item.get("AddressesFree", 0),
            pending_offers=item.get("PendingOffers", 0),
            percentage_in_use=item.get("PercentageInUse", 0.0),
        )

        await db.execute(stmt)

    await db.commit()

async def add_dhcp_scope_lease(db: AsyncSession, leases: list[dict], server: str, collected_at):
    table = DhcpLease.__table__

    for lease in leases:
        # Найдём scope_id по server + ScopeId
        q = select(DhcpScope.id).where(
            DhcpScope.server_address == server,
            DhcpScope.scope_id == lease["ScopeId"]
        )
        result = await db.execute(q)
        scope_id = result.scalar_one_or_none()

        if not scope_id:
            logger.warning(f"[{server}] Lease for unknown scope {lease['ScopeId']} — skipping")
            continue

        # Парсим дату, если есть
        expiry = None
        if lease.get("LeaseExpiryTime"):
            try:
                # Поддержка ISO-8601 с Z (UTC)
                expiry = dateutil.parser.isoparse(lease["LeaseExpiryTime"])
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.warning(f"Failed to parse lease expiry '{lease['LeaseExpiryTime']}': {e}")
                expiry = None

        stmt = insert(table).values(
            dhcp_scope_id=scope_id,
            collected_at=collected_at,
            ip_address=lease["IPAddress"],
            client_id=lease.get("ClientId"),
            host_name=lease.get("HostName"),
            lease_expiration_time=expiry,
            address_state=lease["AddressState"],
            mac_address=lease.get("ClientHardwareAddress"),
        )

        await db.execute(stmt)

    await db.commit()

async def get_dhcp_scope_statistic(db: AsyncSession):
    # Найти последнюю collected_at
    subq = select(func.max(DhcpScopeStatistics.collected_at)).scalar_subquery()

    # Выбрать статистику + связанный scope
    stmt = (
        select(DhcpScopeStatistics, DhcpScope.scope_id)
        .join(DhcpScope, DhcpScope.id == DhcpScopeStatistics.dhcp_scope_id)
        .where(DhcpScopeStatistics.collected_at == subq)
    )

    result = await db.execute(stmt)

    rows = result.all()  # возвращает кортежи (DhcpScopeStatistic, scope_id)

    # Формируем список словарей или объектов для сериализации
    return [
        {
            "scopeId": scope_id,
            "totalAddresses": stat.total_addresses,
            "inUse": stat.in_use,
            "available": stat.available,
            "pendingOffers": stat.pending_offers,
            "percentageInUse": float(stat.percentage_in_use),
            # Можно добавить и другие поля из DhcpScope, например name, server_address и т.д.
        }
        for stat, scope_id in rows
    ]


async def get_dhcp_scope_lease(db: AsyncSession):
    # Найти последнюю collected_at
    subq = select(func.max(DhcpLease.collected_at)).scalar_subquery()

    # Выбрать все записи с этой датой
    stmt = select(DhcpLease).where(DhcpLease.collected_at == subq)

    result = await db.execute(stmt)

    rows = result.scalars().all()  # scalars() даёт объекты DhcpLease

    return [
        {
            "ipAddress": row.ip_address,
            "macAddress": row.client_id,
            "hostName": row.host_name,
            "addressState": row.address_state,
            "leaseExpiryTime": row.lease_expiration_time.isoformat() if row.lease_expiration_time else None
        }
        for row in rows
    ]


async def test_rule():
    async with AsyncSessionLocal() as db:
        data = await get_dhcp_scope_statistic(db)
        logger.info("!!!!!!!!!!!!!!!!!!!!")
        logger.info(data)
        logger.info("!!!!!!!!!!!!!!!!!!!!")

if __name__ == "__main__":
    asyncio.run(test_rule())