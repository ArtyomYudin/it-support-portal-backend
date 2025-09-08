from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Event, CardOwner, AccessPoint

async def get_pacs_events_data(db: AsyncSession) -> list[dict]:
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    result = await db.execute(
        select(
            Event.created,
            CardOwner.firstname,
            CardOwner.secondname,
            CardOwner.lastname,
            AccessPoint.name,
        )
        .select_from(Event)
        .outerjoin(CardOwner, Event.owner_id == CardOwner.system_id)
        .outerjoin(AccessPoint, Event.ap_id == AccessPoint.system_id)
        .where(Event.created >= today, Event.created < tomorrow, Event.code ==1)
        .order_by(Event.created.desc())
        # .limit(50)
    )
    rows = result.all()

    return [
        {
            "eventDate": r.created.isoformat(),
            "displayName": f"{r.lastname or ''} {r.firstname or ''} {r.secondname or ''}".strip(),
            "accessPoint": r.name or "Неизвестно"
        }
        for r in rows
    ]

async def get_pacs_events_by_id(db: AsyncSession, event_id: int) -> list[dict]:
    result = await db.execute(
        select(
            Event.created,
            CardOwner.firstname,
            CardOwner.secondname,
            CardOwner.lastname,
            AccessPoint.name,
        )
        .select_from(Event)
        .outerjoin(CardOwner, Event.owner_id == CardOwner.system_id)
        .outerjoin(AccessPoint, Event.ap_id == AccessPoint.system_id)
        .where(Event.id == event_id, Event.code ==1)
    )
    rows = result.all()

    return [
        {
            "eventDate": r.created.isoformat(),
            "displayName": f"{r.lastname or ''} {r.firstname or ''} {r.secondname or ''}".strip(),
            "accessPoint": r.name or "Неизвестно"
        }
        for r in rows
    ]
