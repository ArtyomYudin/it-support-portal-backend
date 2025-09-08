import json

from db.database import AsyncSessionLocal
from services.pacs_service import get_pacs_events_by_id
from api.ws.manager import manager
# === Обработчики сообщений ===
from core.logging_config import logger

async def events_handler(message):
    logger.info(f"📩 [events] {message.body.decode()}")

async def notifications_handler(message):
    logger.info(f"🔔 [notifications] {message.body.decode()}")
    async with AsyncSessionLocal() as db:
        res = await get_pacs_events_by_id(db, int(message.body.decode()))
        await manager.broadcast(json.dumps({
                            "event": "event_pacs_entry_exit",
                            "data": {"results": res, "total": len(res)}
                        }))

async def logs_handler(message):
    logger.info(f"📝 [logs] {message.body.decode()}")