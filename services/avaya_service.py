from datetime import datetime, timedelta, date, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from typing import Optional, List

from db.models.avaya import AvayaCDR
from db.models.employee import Employee


async def get_avaya_cdr_list(session: AsyncSession, filter_hours: int):
    # Создаём алиасы для Employee — для вызывающего и вызываемого
    calling_employee = aliased(Employee, name='calling')
    called_employee = aliased(Employee, name='called')

    # Вычисляем минимальную дату (учитываем timezone, если используется)
    min_date = datetime.now(timezone.utc) - timedelta(hours=filter_hours)

    stmt = (
        select(
            AvayaCDR.id.label("id"),
            AvayaCDR.date.label("callStart"),
            AvayaCDR.duration.label("callDuration"),
            AvayaCDR.calling_number.label("callingNumber"),
            calling_employee.display_name.label("callingName"),
            AvayaCDR.called_number.label("calledNumber"),
            called_employee.display_name.label("calledName"),
            AvayaCDR.call_code.label("callCode"),
        )
        .outerjoin(calling_employee, calling_employee.call_number == AvayaCDR.calling_number)
        .outerjoin(called_employee, called_employee.call_number == AvayaCDR.called_number)
        .where(AvayaCDR.date >= min_date)
        .order_by(AvayaCDR.date.desc())
    )

    result = await session.execute(stmt)
    cdr_list = result.mappings().all()

    return [
        {
            "callStart": cdr["callStart"].isoformat(),
            "callDuration": cdr["callDuration"],
            "callingNumber": cdr["callingNumber"],
            "callingName": cdr["callingName"],
            "calledNumber": cdr["calledNumber"],
            "calledName": cdr["calledName"],
            "callCode": cdr["callCode"]
        }
        for cdr in cdr_list
    ]