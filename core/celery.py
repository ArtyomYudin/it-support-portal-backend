import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from core.settings import settings
# ЯВНО ИМПОРТИРУЕМ МОДУЛЬ С ЗАДАЧАМИ — ЭТО КЛЮЧЕВОЕ!
import tasks.zabbix_task

app = Celery('core')

# Подключаемся к RabbitMQ
app.conf.broker_url = f"amqp://{settings.RMQ_CELERY_USER}:{settings.RMQ_CELERY_PASSWORD}@{settings.RMQ_HOST}:{settings.RMQ_PORT}/{settings.RMQ_VIRTUAL_HOST}"
#
# # Результаты задач тоже можно хранить в RabbitMQ (через RPC) или, лучше, в Redis/DB
app.conf.result_backend = 'rpc://'  # или 'redis://localhost:6379/0'

# QoS фикс для RabbitMQ
app.conf.broker_transport_options = {"global_qos": False}

# Принудительно задаём тип очереди
app.conf.task_queues = [
    Queue('celery', routing_key='celery', queue_arguments={'x-queue-type': 'classic'})
]

# Основные настройки Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,

    # Управление prefetch (распределение задач по воркерам)
    worker_prefetch_multiplier=1,
    task_acks_late=True,  # подтверждаем выполнение только после завершения задачи
)

# Автообнаружение задач
app.autodiscover_tasks(["tasks"])

# Планировщик
app.conf.beat_schedule = {
    'fetch-provider-info-every-5-minutes': {
        'task': 'tasks.zabbix_task.fetch_provider_info_task',  # Укажите правильный путь!
        'schedule': crontab(minute='*/1'),  # Каждые 1 минут
        'kwargs': {'token': None},   # Передаём token=None, если нужно — замените на актуальный токен
    },
    'fetch-hardware-problem-info-every-5-minutes': {
        'task': 'tasks.zabbix_task.fetch_hardware_group_problem_task',  # Укажите правильный путь!
        'schedule': crontab(minute='*/1'),  # Каждые 1 минут
        'kwargs': {'token': None},   # Передаём token=None, если нужно — замените на актуальный токен
    },
}
