import asyncio

import asyncpg
from celery import shared_task

# from core.settings import settings
from core.logging_config import logger
from core.settings import settings
from services.vpn_service import create_pg_trigger_function
from db.database import AsyncSessionLocal

listener_started = False

def _notify_handler(conn, pid, channel, payload):
    # Пришло уведомление из Postgres → шлём задачу в Celery
    # send_to_rabbitmq.delay(payload)
    logger.info("!!!!!! Пришло событие от VPN !!!!!!!!")
    logger.info(payload)

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


@shared_task(bind=True, max_retries=3)
def initializing_db_notification_listener(self):
    try:
        asyncio.run(listen_to_channel())
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# @shared_task(bind=True, max_retries=3)
# def fetch_cisco_vpn_activity(self, token=None):
#     try:
#         asyncio.run(publish_cisco_vpn_activity(token=token))
#     except Exception as exc:
#         logger.error(f"Task failed: {exc}")
#         raise self.retry(exc=exc, countdown=2 ** self.request.retries)