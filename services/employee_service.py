from datetime import datetime, timedelta
from enum import unique

from sqlalchemy import select, func, Sequence, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from typing import Optional, List, TYPE_CHECKING, Dict

from db.models.employee import Employee, EmployeeCard, Department
from db.models.pacs import Event, CardOwner, AccessPoint

async def get_department_structure_by_upn(db: AsyncSession, user_principal_name:str) -> List[any]:
    """
        Возвращает список отделов, которые являются "братьями" отдела сотрудника
        (т.е. имеют того же родителя, что и отдел сотрудника).
        """

    # Алиас для CTE-подобной логики — сначала найдём parent_id отдела сотрудника
    department_structure: List[int] = []
    seen = set()

    stmt = (
        select(Department.parent_id)
        .join(Employee, Department.id == Employee.department_id)
        .where(Employee.user_principal_name == user_principal_name)
        .limit(1)
        .scalar_subquery()  # <-- это будет подзапрос, который вернёт parent_id
    )

    # Теперь выбираем все отделы, у которых parent_id равен найденному
    sibling_departments_stmt = (
        select(Department)
        .where(Department.parent_id == stmt)
    )

    result = await db.execute(sibling_departments_stmt)
    siblings = result.scalars().all()

    if siblings:
        # Добавляем parent_id первого отдела
        parent_id = siblings[0].parent_id
        if parent_id is not None and parent_id not in seen:
            department_structure.append(parent_id)
            seen.add(parent_id)

        # Добавляем id всех "братских" отделов
        for dep in siblings:
            if dep.id not in seen:
                department_structure.append(dep.id)

    return department_structure


async def get_filtered_employee(db: AsyncSession, filter_value: str | None) -> List[Dict]:
    result = await db.execute(
        select(
            Employee.user_principal_name,
            Employee.display_name,
            Employee.department_id,
            EmployeeCard.card_id
        )
        .join(EmployeeCard, Employee.user_principal_name == EmployeeCard.employee_upn)
        .where(Employee.display_name.ilike(bindparam("filter")))
        .order_by(Employee.display_name.desc()),
        {"filter": f"{filter_value}%"}
    )
    rows = result.all()

    return [
        {
            "userPrincipalName": r.user_principal_name,
            "displayName": r.display_name,
            "departmentId": r.department_id,
            "pacsCardId": r.card_id
        }
        for r in rows
    ]