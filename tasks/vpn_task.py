import asyncio

import aio_pika
import asyncpg
from celery import shared_task

# from core.settings import settings
from core.logging_config import logger
from core.settings import settings
from services.vpn_service import create_pg_trigger_function, get_active_vpn_users_by_host
from db.database import AsyncSessionLocal
from utils.celery import publish_to_exchange

RABBITMQ_URL = f"amqp://{settings.RMQ_CELERY_USER}:{settings.RMQ_CELERY_PASSWORD}@{settings.RMQ_HOST}:{settings.RMQ_PORT}/{settings.RMQ_VIRTUAL_HOST}"

listener_started = False

async def _notify_handler(conn, pid, channel, payload):
    # Пришло уведомление из Postgres → шлём задачу в Celery
    # send_to_rabbitmq.delay(payload)
    async with AsyncSessionLocal() as db:
        active = await get_active_vpn_users_by_host(db)
    payload = {
        "event": "event_vpn_active_session",
        "data": { "results": active, "total": len(active) },
    }

    await publish_to_exchange(payload, RABBITMQ_URL)


async def listen_to_channel():
    global listener_started
    if listener_started:
        return  # уже слушаем
    listener_started = True

    conn = await asyncpg.connect(
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        database=settings.DATABASE_NAME,
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT
    )

    # Создаем если нужно триггер и функцию для прослушивания канала
    async with AsyncSessionLocal() as db:
        await create_pg_trigger_function(db)

    # Подписка на канал
    await conn.add_listener("vpn_event_channel", _notify_handler)
    logger.info("Listening for new VPN events...")

    try:
        while True:
            await asyncio.sleep(60)  # держим соединение живым
    finally:
        await conn.close()


async def get_cisco_vpn_activity(token: str):
    pass

async def publish_cisco_vpn_activity(token: str):
    pass


# @shared_task(bind=True, max_retries=3)
# def initializing_db_notification_listener(self):
#     try:
#         asyncio.run(listen_to_channel())
#     except Exception as exc:
#         logger.error(f"Task failed: {exc}")
#         raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# @shared_task(bind=True, max_retries=3)
# def fetch_cisco_vpn_activity(self, token=None):
#     try:
#         asyncio.run(publish_cisco_vpn_activity(token=token))
#     except Exception as exc:
#         logger.error(f"Task failed: {exc}")
#         raise self.retry(exc=exc, countdown=2 ** self.request.retries)