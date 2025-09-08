"""
обработчик WebSocket-сессии с аутентификацией.
"""
import json
import logging
from fastapi import WebSocket
from pydantic import ValidationError

from api.ws.schemas import ClientMessage, Event
from api.ws.manager import manager
from utils.security import decode_token
from db.database import AsyncSessionLocal
from services import pacs_service

logger = logging.getLogger("app.ws")  # Подлоггер для WebSocket

async def websocket_auth_handler(websocket: WebSocket):
    token = websocket.query_params.get("token")
    username = decode_token(token)
    if not username:
        logger.warning(f"WebSocket: попытка подключения с невалидным токеном")
        await websocket.close(code=1008, reason="Invalid token")
        return

    logger.info(f"WebSocket: пользователь {username} подключился")
    await manager.connect(websocket)
    try:
        async with AsyncSessionLocal() as db:  # <--- тут создаём сессию
            while True:
                try:
                    text = await websocket.receive_text()
                    data = json.loads(text)

                    message = ClientMessage(**data)

                    logger.debug(f"WebSocket ({username}): получил сообщение {message.event}")

                    if message.event == Event.GET_PACS_INIT_VALUE:
                        res = await pacs_service.get_pacs_events_data(db)
                        await manager.send_personal_message(json.dumps({
                            "event": "event_pacs_entry_exit",
                            "data": {"results": res, "total": len(res)}
                        }), websocket)
                    # if message.type == "ping":
                    #     await manager.send_personal_message(json.dumps({"type": "pong"}), websocket)
                    # elif message.type == "chat":
                    #     await manager.broadcast(
                    #         json.dumps({"type": "chat", "data": {"user": username, "text": message.data.get("text")}})
                    #     )
                except ValidationError as e:
                    logger.warning(f"WebSocket: невалидное сообщение от {username} — {e.errors()}")
                    await manager.send_personal_message(
                        json.dumps({"error": "Invalid format", "detail": e.errors()}),
                        websocket
                    )
                except Exception as e:
                    logger.error(f"WebSocket: ошибка у {username} — {str(e)}")
                    break
    finally:
        manager.disconnect(websocket)
        logger.info(f"WebSocket: пользователь {username} отключился")