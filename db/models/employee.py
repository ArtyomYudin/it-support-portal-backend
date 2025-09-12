from sqlalchemy import String, Integer, ForeignKey, LargeBinary
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from typing import Optional, List, TYPE_CHECKING

from db.database import Base

if TYPE_CHECKING:
    from .pacs import CardOwner


class Employee(Base):
    __tablename__ = "employee"

    user_principal_name: Mapped[str] = mapped_column(String(40), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True)

    department_id: Mapped[int] = mapped_column(ForeignKey("department.id"))
    position_id: Mapped[int] = mapped_column(ForeignKey("position.id"))
    call_number: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    # связи
    department: Mapped["Department"] = relationship(back_populates="employees", foreign_keys=[department_id])
    position: Mapped["Position"] = relationship(back_populates="employees", foreign_keys=[position_id])
    photo: Mapped[Optional["EmployeePhoto"]] = relationship(back_populates="employee", uselist=False)

    # связь через таблицу employee_card
    employee_cards: Mapped[List["EmployeeCard"]] = relationship(back_populates="employee")
    cards: Mapped[List["CardOwner"]] = relationship(
        secondary="employee_card", back_populates="employees", overlaps="employee_cards"
    )

    # обратные связи (когда сотрудник — менеджер)
    managed_departments: Mapped[List["Department"]] = relationship(
        "Department", foreign_keys="[Department.manager_upn]", back_populates="manager"
    )
    direction_managed_departments: Mapped[List["Department"]] = relationship(
        "Department", foreign_keys="[Department.direction_manager_upn]", back_populates="direction_manager"
    )


class EmployeePhoto(Base):
    __tablename__ = "employee_photo"

    user_principal_name: Mapped[str] = mapped_column(
        String(40), ForeignKey("employee.user_principal_name"), primary_key=True
    )
    thumbnail_photo: Mapped[Optional[bytes]] = mapped_column(LargeBinary)

    employee: Mapped["Employee"] = relationship(back_populates="photo")


class Department(Base):
    __tablename__ = "department"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('department.id', use_alter=True),
                                                        index=True, nullable=True)
    manager_upn: Mapped[Optional[str]] = mapped_column(
        String(40), ForeignKey("employee.user_principal_name", use_alter=True), nullable=True
    )
    direction_manager_upn: Mapped[Optional[str]] = mapped_column(
        String(40), ForeignKey("employee.user_principal_name", use_alter=True), nullable=True
    )
    # связи
    parent: Mapped[Optional["Department"]] = relationship(
        "Department", remote_side=[id], back_populates="children"
    )
    children: Mapped[List["Department"]] = relationship("Department", back_populates="parent")

    manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", foreign_keys=[manager_upn], back_populates="managed_departments"
    )
    direction_manager: Mapped[Optional["Employee"]] = relationship(
        "Employee", foreign_keys=[direction_manager_upn], back_populates="direction_managed_departments"
    )

    employees: Mapped[List["Employee"]] = relationship(
        back_populates="department", foreign_keys="Employee.department_id"
    )


# Модель Position
class Position(Base):
    __tablename__ = "position"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Обратная связь с сотрудниками
    employees: Mapped[List["Employee"]] = relationship(back_populates="position",foreign_keys="Employee.position_id")


class EmployeeCard(Base):
    __tablename__ = "employee_card"

    employee_upn: Mapped[str] = mapped_column(
        ForeignKey("employee.user_principal_name"), primary_key=True
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("pacs_card_owner.system_id"), primary_key=True
    )
    employee: Mapped["Employee"] = relationship(back_populates="employee_cards", overlaps="cards")
    card: Mapped["CardOwner"] = relationship(back_populates="card_employees", overlaps="employees, cards")