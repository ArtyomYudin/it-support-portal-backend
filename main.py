from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.settings import settings
from api.auth.routers import router as auth_router
from api.ws.routes import ws_router
from core.logging_config import logger  # импортируем логгер
from rabbitmq.consumer import RabbitMQConsumer
from rabbitmq.handlers import pacs_handler, celery_beat_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение ресурсов приложения"""
    logger.info("Запуск приложения...")

    # Подключение к RabbitMQ
    consumer = RabbitMQConsumer(
        settings.RMQ_HOST,
        settings.RMQ_PORT,
        settings.RMQ_VIRTUAL_HOST,
        settings.RMQ_BACKEND_USER,
        settings.RMQ_BACKEND_PASSWORD,
        logger,
    )
    await consumer.connect()

    # Регистрируем обработчики очередей
    # await consumer.consume("events", events_handler)
    await consumer.consume(settings.RMQ_PACS_EXCHANGE_NAME, "backend", pacs_handler)
    await consumer.consume(settings.RMQ_CELERY_BEAT_EXCHANGE_NAME, "celery_beat", celery_beat_handler)
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
origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

# Подключаем роутер из auth.py_bak
app.include_router(auth_router)
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