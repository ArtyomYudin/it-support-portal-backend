"""
обработчик WebSocket-сессии с аутентификацией.
"""
import json
import logging

from annotated_types.test_cases import cases
from fastapi import WebSocket
from pydantic import ValidationError
from redis.asyncio import Redis

from api.ws.schemas import ClientMessage, Event
from api.ws.manager import manager
from core.settings import settings
from services.vpn_service import get_active_vpn_users_by_host
from utils.security import decode_token
from db.database import AsyncSessionLocal
from services import pacs_service, employee_service, avaya_service

logger = logging.getLogger("app.ws")  # Подлоггер для WebSocket

REDIS_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


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

                    match message.event:
                        case Event.GET_DASHBOARD_EVENT:
                            vpn_value = await get_active_vpn_users_by_host(db)
                            await manager.send_personal_message(json.dumps({
                                "event": "event_vpn_active_session_count",
                                "data": {"results": vpn_value, "total": len(vpn_value)}
                            }), websocket)

                            # Берем последние значения с Redis.
                            async with Redis.from_url(REDIS_URL, decode_responses=True) as redis:
                                provider_info = await redis.get("latest:event_provider_info")
                                await manager.send_personal_message(provider_info, websocket)

                                avaya_e1_channel_info = await redis.get("latest:event_avaya_e1_channel_info")
                                logger.debug("!!!!!!!!!!!!!!!!")
                                logger.debug(avaya_e1_channel_info)
                                logger.debug("!!!!!!!!!!!!!!!!")
                                await manager.send_personal_message(avaya_e1_channel_info, websocket)

                                hardware_group_info = await redis.get("latest:event_hardware_group_alarm")
                                await manager.send_personal_message(hardware_group_info, websocket)

                        case Event.GET_PACS_INIT_VALUE:
                            res = await pacs_service.get_pacs_events_data(db)
                            await manager.send_personal_message(json.dumps({
                                "event": "event_pacs_entry_exit",
                                "data": {"results": res, "total": len(res)}
                            }), websocket)
                            res_last = await pacs_service.get_pacs_last_event(db)

                            await manager.send_personal_message(json.dumps({
                                "event": "event_pacs_last_event",
                                "data": {"results": res_last, "total": len(res_last)}
                            }), websocket)

                        case Event.GET_DEPARTMENT_STRUCTURE_BY_UPN:
                            structure = await employee_service.get_department_structure_by_upn(db, "a.yudin@center-inform.ru")
                            await manager.send_personal_message(json.dumps({
                                "event": 'event_department_structure_by_upn',
                                "data": structure,
                            }), websocket)

                        case Event.GET_FILTERED_REQUEST_INITIATOR:
                            filtered = await employee_service.get_filtered_employee(db, message.data)
                            await manager.send_personal_message(json.dumps({
                                "event": 'event_filtered_employee',
                                "data": filtered,
                            }), websocket)

                        case Event.GET_PACS_EMPLOYEE_LAST_EVENT:
                            employee_last_event = await pacs_service.get_pacs_last_event(db, message.data)
                            await manager.send_personal_message(json.dumps({
                                "event": "event_pacs_employee_last_event",
                                "data": {"results": employee_last_event, "total": len(employee_last_event)}
                            }), websocket)
                            #  event: 'event_filtered_employee',
                            #  data: filteredEmployeeArray,

                        case Event.GET_AVAYA_CDR:
                            avaya_cdr = await avaya_service.get_avaya_cdr_list(db, int(message.data))
                            await manager.send_personal_message(json.dumps({
                                "event": "event_avaya_cdr",
                                "data": {"results": avaya_cdr, "total": len(avaya_cdr)}
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