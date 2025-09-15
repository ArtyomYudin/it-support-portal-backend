import json

from api.ws.schemas import Event
from db.database import AsyncSessionLocal
from services.pacs_service import get_pacs_events_by_id, get_pacs_last_event
from api.ws.manager import manager
# === Обработчики сообщений ===
from core.logging_config import logger

async def events_handler(message):
    logger.info(f"📩 [events] {message.body.decode()}")

async def pacs_handler(message):
    logger.info(f"🔔 [PACS notifications] {message.body.decode()}")
    message_body = message.body.decode()
    data = json.loads(message_body)

    async with AsyncSessionLocal() as db:
        res = await get_pacs_events_by_id(db, int(data["new_pacs_event_id"]))
        res_last = await get_pacs_last_event(db)
        await manager.broadcast(json.dumps(
            {
                "event": "event_pacs_entry_exit",
                "data": {"results": res, "total": len(res)}
            })
        )
        await manager.broadcast(json.dumps(
            {
                "event": "event_pacs_last_event",
                "data": {"results": res_last, "total": len(res_last)}
            })
        )

async def celery_beat_handler(message):
    logger.info(f"🔔 [CELERY BEAT notifications] {message.body.decode()}")
    message_body = json.loads(message.body.decode())
    match message_body["event"]:
        case Event.EVENT_PROVIDER_INFO:
            await manager.broadcast(json.dumps(
                {
                    "event": "event_provider_info",
                    "data": message_body["data"]
                })
            )


async def logs_handler(message):
    logger.info(f"📝 [logs] {message.body.decode()}")