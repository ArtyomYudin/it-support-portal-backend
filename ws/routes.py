from fastapi import APIRouter, WebSocket
from ws.handlers import websocket_auth_handler

ws_router = APIRouter()

@ws_router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_auth_handler(websocket)