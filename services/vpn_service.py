import asyncio
import asyncpg

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging_config import logger


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

