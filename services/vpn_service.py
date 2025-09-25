import asyncio
from bisect import insort
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

import asyncpg

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging_config import logger
from db.models.vpn import CiscoVPNEvent
from utils.vpn import parse_event


async def create_pg_trigger_function(db: AsyncSession):
    # Создаем функцию notify_new_vpn_event
    # Создаем триггер на вставку в таблицу cisco_vpn_event
    # Проверка функции
    func_exists_result = await db.execute(text("""
                                        SELECT EXISTS (
                                            SELECT 1
                                            FROM pg_proc
                                            WHERE proname = 'notify_new_vpn_event');
                                    """))
    func_exists = func_exists_result.scalar()
    if not func_exists:
        await db.execute(text("""
                            CREATE OR REPLACE FUNCTION notify_new_vpn_event() RETURNS trigger AS $$
                            BEGIN
                                PERFORM pg_notify('vpn_event_channel', NEW.host || '|' || NEW.event);
                                 RETURN NEW;
                            END;
                            $$ LANGUAGE plpgsql;
                            """))
        await db.commit()
        logger.info("Function created.")
    else:
        logger.info("Function already exists.")

    # Проверка триггера
    trigger_exists_result = await db.execute(text("""
                                        SELECT EXISTS (
                                            SELECT 1
                                            FROM pg_trigger
                                            WHERE tgname = 'trg_vpn_event');
                                        """))
    trigger_exists = trigger_exists_result.scalar()
    if not trigger_exists:
        await db.execute(text("""
                            CREATE TRIGGER trg_vpn_event
                                AFTER INSERT ON cisco_vpn_event
                                FOR EACH ROW
                                EXECUTE FUNCTION notify_new_vpn_event();
                            """))
        await db.commit()
        logger.info("Trigger created.")
    else:
        logger.info("Trigger already exists.")

async def get_active_vpn_users_by_host(db: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    """
    Возвращает список активных пользователей AnyConnect на основе логов в CiscoVPNEvent, сгруппированных по хосту (host).
    Активный = есть событие входа (746012) без последующего события выхода (746013) для того же internal_ip.
    """

    # Запрос: только события входа/выхода, отсортированные по времени

    # MAX_SESSION_HOURS = 24
    # cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    stmt = (
        select(CiscoVPNEvent)
        .where(
            (CiscoVPNEvent.event.like('%ASA-7-746012%')) |
            (CiscoVPNEvent.event.like('%ASA-7-746013%')) ,
            # CiscoVPNEvent.created >= cutoff
        )
        .order_by(CiscoVPNEvent.created.asc())
    )

    result = await db.execute(stmt)
    events = result.scalars().all()

    # Словари для отслеживания последнего входа и выхода по internal_ip
    last_login = {}   # internal_ip → {username, login_time, host, internal_ip}
    last_logout = {}  # internal_ip → logout_time

    for event in events:
        parsed = parse_event(event.event)
        if not parsed:
            continue

        event_type, internal_ip, username = parsed
        event_time = event.created
        host = event.host or "unknown"  # на случай NULL

        if event_type == "login":
            last_login[internal_ip] = {
                "username": username,
                "login_time": event_time,
                "internal_ip": internal_ip,
                "host": host,
                "event_id": event.id
            }
        elif event_type == "logout":
            last_logout[internal_ip] = event_time

    # Группируем активных пользователей по хосту
    grouped_users: Dict[str, List[Dict]] = {}

    for internal_ip, login_info in last_login.items():
        # login_time = login_info["login_time"]
        # if (datetime.now(timezone.utc) - login_time).total_seconds() > MAX_SESSION_HOURS * 3600:
        #     continue  # пропускаем "подозрительно долгие" сессии
        logout_time = last_logout.get(internal_ip)

        if logout_time is None or logout_time < login_info["login_time"]:
            host = login_info["host"]
            if host not in grouped_users:
                grouped_users[host] = []

            user_entry = {
                "username": login_info["username"],
                "internal_ip": internal_ip,
                "login_time": login_info["login_time"].isoformat(),
                "duration_seconds": int((datetime.now(timezone.utc) - login_info["login_time"]).total_seconds()),
                "status": "active"
            }

            # вставляем пользователя в отсортированный по login_time список
            # преобразуем login_time обратно в datetime для правильной сортировки
            # используем отрицательное timestamp для обратной сортировки
            # timestamp = -login_info["login_time"].timestamp()
            # insort(grouped_users[host], (timestamp, user_entry))
            insort(grouped_users[host],
                   (login_info["login_time"], user_entry))

    # после вставки нужно распаковать кортежи, чтобы остались только словари
    for host, users in grouped_users.items():
        grouped_users[host] = [entry for _, entry in users]

    return  grouped_users