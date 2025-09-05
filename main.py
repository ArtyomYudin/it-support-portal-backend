import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from api import auth
from core.settings import settings
from ws.routes import ws_router
from core.logging_config import logger  # импортируем логгер
from rabbitmq.consumer import RabbitMQConsumer
from rabbitmq.handlers import notifications_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение ресурсов приложения"""
    logger.info("Запуск приложения...")

    # Подключение к RabbitMQ
    consumer = RabbitMQConsumer(
        settings.RMQ_HOST,
        settings.RMQ_PORT,
        settings.RMQ_VIRTUAL_HOST,
        settings.RMQ_USER,
        settings.RMQ_PASSWORD,
        logger,
    )
    await consumer.connect()

    # Регистрируем обработчики очередей
    # await consumer.consume("events", events_handler)
    await consumer.consume("pacs_client", notifications_handler)
    # await consumer.consume("logs", logs_handler)

    # сохраняем consumer в app.state
    app.state.consumer = consumer

    yield  # <--- точка работы приложения

    # Завершение
    await consumer.close()
    logger.info("Приложение остановлено")

app = FastAPI(title="IT Support Portal API", lifespan=lifespan)
logger.info("Starting application...")

# CORS (разреши фронтенду)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# @app.on_event("startup")
# async def startup_event():
#     # Запуск фоновых задач
#     logger.info("Startup: запуск фоновых задач...")
#     asyncio.create_task(background_tasks.check_emails())
#     asyncio.create_task(background_tasks.fetch_zabbix_data())
#     asyncio.create_task(rabbitmq_client.consume_messages("my_queue"))
#     logger.info("Все фоновые задачи запущены")

# Подключаем роутер из auth.py
app.include_router(auth.router)
app.include_router(ws_router)

@app.get("/")
async def root():
    return {"message": "IT Support Portal API is running"}

#
# app.include_router(api.routes.router, prefix="/api")

# if __name__ == "__main__":
#     import uvicorn
#     print('!!!!!!!!!!!')
#     log_level = "debug" if settings.DEBUG else "info"
#     logger.info(f"Запуск сервера на http://{settings.HOST}:{settings.PORT}")
#     uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)