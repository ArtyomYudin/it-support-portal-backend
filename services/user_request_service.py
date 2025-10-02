from sqlalchemy.orm import Session
from datetime import datetime, date

from db.models.user_request import UserRequest, UserRequestLifeCycle


async def create_user_request_with_lifecycle(
        session: Session,
        creator_upn: str | None,
        initiator_upn: str,
        executor_upn: str,
        service_id: int,
        topic: str | None,
        description: str | None,
        status_id: int,
        priority_id: int,
        deadline: date,
) -> UserRequest:
    # Шаг 1: Создаём и добавляем заявку
    new_request = UserRequest(
        creation_date=datetime.now(),
        change_date=datetime.now(),
        creator_upn=creator_upn,
        initiator_upn=initiator_upn,
        executor_upn=executor_upn,
        service_id=service_id,
        topic=topic,
        description=description,
        status_id=status_id,
        priority_id=priority_id,
        deadline=deadline,
        # reg_number будет установлен автоматически БД
    )
    session.add(new_request)

    # Важно: делаем flush(), чтобы получить reg_number,
    # но не commit(), чтобы всё было в одной транзакции
    session.flush()  # отправляет INSERT в БД и получает reg_number

    # Теперь new_request.reg_number заполнен!
    print(f"Сгенерирован reg_number: {new_request.reg_number}")

    # Шаг 2: Создаём запись в жизненном цикле
    lifecycle_event = UserRequestLifeCycle(
        reg_number=new_request.reg_number,
        user_principal_name=initiator_upn,  # или creator_upn — по логике
        event_date=new_request.creation_date,
        event_type="CREATED",  # или другое значение
        event_value="Заявка создана",
    )
    session.add(lifecycle_event)

    # Можно сделать commit() здесь или выше по стеку
    return new_request