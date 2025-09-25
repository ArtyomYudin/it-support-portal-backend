import asyncio
import json
from functools import partial

import asyncpg

from api.ws.manager import manager
from core.logging_config import logger
from core.settings import settings
from db.database import AsyncSessionLocal
from services.vpn_service import create_pg_trigger_function, get_active_vpn_users_by_host
from utils.celery import publish_to_exchange


async def _notify_handler(channel_handler, conn, pid, channel, payload):
    """
    Общий обработчик: вызывает конкретную функцию для канала
    """
    try:
        await channel_handler(payload)   # передаём дальше только payload
    except Exception as e:
        logger.error(f"Notify handler failed for {channel}: {e}", exc_info=True)


async def handle_vpn_event(payload: str):
    async with AsyncSessionLocal() as db:
        active_users = await get_active_vpn_users_by_host(db)
        logger.debug(f"Active VPN users: {active_users}")

    await manager.broadcast(json.dumps(
        {
            "event": "event_vpn_active_session_count",
            "data": {"results": active_users, "total": len(active_users)}
        })
    )

async def listen_to_channel():
    """
    Запускает бесконечный цикл с авто-реконнектом к Postgres LISTEN.
    """
    while True:
        conn = None
        try:
            logger.info("Connecting to Postgres for LISTEN ...")
            conn = await asyncpg.connect(
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PASSWORD,
                database=settings.DATABASE_NAME,
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
            )

            # создаём триггер для Postgres (если нужно)
            async with AsyncSessionLocal() as db:
                await create_pg_trigger_function(db)

            # подписка на канал
            await conn.add_listener(
                "vpn_event_channel",
                partial(_notify_handler, handle_vpn_event)
            )

            logger.info("Listening for new VPN events...")

            while True:
                await asyncio.sleep(60)  # держим соединение живым

        except asyncio.CancelledError:
            logger.info("Задача listen_to_channel отменена")
            break  # выходим из внешнего while True

        except (asyncpg.PostgresError, OSError) as e:
            logger.warning(f"Postgres LISTEN connection lost: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

        finally:
            if conn:
                try:
                    await conn.close()
                except Exception:
                    pass