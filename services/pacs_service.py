from datetime import datetime, timedelta, date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from typing import Optional, List

from db.models.employee import Employee, EmployeeCard
from db.models.pacs import Event, CardOwner, AccessPoint

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
            "displayName": f"{r.lastname or 'Неизвестно'} {r.firstname or ''} {r.secondname or ''}".strip(),
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

async def get_last_events_by_dep(db: AsyncSession, department_id: int) -> list[dict]:
    # Подзапрос: берём последнюю дату события по каждому сотруднику
    subq = (
        select(
            Employee.user_principal_name.label("upn"),
            func.max(Event.created).label("last_created")
        )
        .join(EmployeeCard, Employee.user_principal_name == EmployeeCard.employee_upn)
        .join(CardOwner, EmployeeCard.card_id == CardOwner.system_id)
        .join(Event, CardOwner.system_id == Event.owner_id)
        .where(Employee.department_id == department_id)
        .group_by(Employee.user_principal_name)
        .subquery()
    )

    # Алиасы для join с последним событием
    e = aliased(Employee)
    ev = aliased(Event)

    query = (
        select(
            ev.created,
            e.display_name,
            AccessPoint.name.label("access_point_name"),
        )
        .join(subq, subq.c.upn == e.user_principal_name)
        .join(EmployeeCard, e.user_principal_name == EmployeeCard.employee_upn)
        .join(CardOwner, EmployeeCard.card_id == CardOwner.system_id)
        .join(ev, (CardOwner.system_id == ev.owner_id) & (ev.created == subq.c.last_created))
        .join(AccessPoint, ev.ap_id == AccessPoint.system_id)
        .where(e.department_id == department_id)
    )
    # Выполняем запрос
    result = await db.execute(query)
    rows = result.all()

    # Возвращаем как список словарей (опционально)
    return [
        {
            "eventDate": row.created.isoformat(),
            "displayName": row.display_name,
            "accessPoint": row.access_point_name,
            "departmentId": department_id,
        }
        for row in rows
    ]

async def get_pacs_last_event(session: AsyncSession, owner_id: Optional[int] = None) -> List[dict]:
    """
    Возвращает последние события по каждому владельцу карты (или по одному, если owner_id указан).
    Связь CardOwner → Employee осуществляется через EmployeeCard.
    """

    today = date.today()

    # Подзапрос: CTE — последние события по owner_id
    subq = (
        select(
            func.max(Event.id).label("last_event_id"),
            Event.owner_id
        )
        .group_by(Event.owner_id)
    )

    if owner_id is not None:
        subq = subq.where(Event.owner_id == owner_id)
    else:
        subq = subq.where(func.date(Event.created) == today)

    cte = subq.cte("cte_pacs_last_event")

    # Алиасы для удобства
    event_alias = aliased(Event)
    card_owner_alias = aliased(CardOwner)
    access_point_alias = aliased(AccessPoint)
    employee_card_alias = aliased(EmployeeCard)
    employee_alias = aliased(Employee)

    # Основной запрос
    stmt = (
        select(
            event_alias.created.label("eventDate"),
            card_owner_alias.display_name.label("pacsDisplayName"),
            access_point_alias.name.label("accessPointName"),
            employee_alias.user_principal_name.label("userPrincipalName"),
            employee_alias.display_name.label("displayName"),
            employee_alias.department_id.label("departmentId"),
        )
        .select_from(cte)
        .join(event_alias, event_alias.id == cte.c.last_event_id)
        .join(card_owner_alias, event_alias.owner_id == card_owner_alias.system_id)
        .join(access_point_alias, event_alias.ap_id == access_point_alias.system_id)
        # 👇 JOIN через EmployeeCard
        .outerjoin(employee_card_alias, employee_card_alias.card_id == card_owner_alias.system_id)
        .outerjoin(employee_alias, employee_alias.user_principal_name == employee_card_alias.employee_upn)
        .order_by(event_alias.created.desc())
    )

    result = await session.execute(stmt)
    events = result.mappings().all()

    # class LastEventDTO(BaseModel):
    #     eventDate: datetime
    #     pacsDisplayName: Optional[str]
    #     accessPointName: str
    #     # userPrincipalName: Optional[str]
    #     displayName: Optional[str]
    #     departmentId: Optional[int]


    return [
        {
            "eventDate": event['eventDate'].isoformat(),
            "displayName": event['displayName'] or "Неизвестно",
            "accessPoint": event['accessPointName'],
            "departmentId": event['departmentId'],
            "pacsDisplayName": event['pacsDisplayName'] or "Неизвестно",
        }
        for event in events
    ]

