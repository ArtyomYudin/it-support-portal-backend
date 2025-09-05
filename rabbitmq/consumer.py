import asyncio

from aio_pika import RobustConnection, RobustChannel, connect_robust, IncomingMessage
from aiormq import AMQPConnectionError

from core.logging_config import logger

class RabbitMQConsumer:
    """
     Асинхронный потребитель RabbitMQ для получения сообщений.
     Использует aio-pika (поддержка reconnect).
     """
    def __init__(self, host: str, port: int, virtual_host: str, username: str, password: str, logger=None):
        self.host = host
        self.port = port
        self.virtual_host = virtual_host
        self.username = username
        self.password = password
        self.logger = logger

        self.connection: RobustConnection | None = None
        self.channel: RobustChannel | None = None

    async def __aenter__(self):
        """Вход в асинхронный контекстный менеджер."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из асинхронного контекстного менеджера."""
        await self.close()

    async def connect(self, retries: int = 5, delay: int = 5):
        """
        Подключение к RabbitMQ с повторными попытками.

        :param retries: количество попыток
        :param delay: задержка между попытками
        """
        for attempt in range(1, retries + 1):
            try:
                self.connection = await connect_robust(
                    host=self.host,
                    port=self.port,
                    login=self.username,
                    password=self.password,
                    virtualhost=self.virtual_host,
                    timeout=10
                )
                self.channel = await self.connection.channel()
                self.logger.info(f"Подключение к RabbitMQ {self.host}:{self.port}/{self.virtual_host}")
                return
            except AMQPConnectionError as e:
                self.logger.warning(f"Попытка подключения {attempt}/{retries} не удалась: {e}")
                await asyncio.sleep(delay)

        raise ConnectionError(f"Не удалось подключиться к RabbitMQ по адресу {self.host}:{self.port}")

    async def consume(self, queue_name: str, handler):
        """
        Подписка на очередь и обработка сообщений.
        handler — это асинхронная функция, которая принимает message: IncomingMessage
        """
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized. Call connect() first.")

        queue = await self.channel.declare_queue(queue_name, durable=True)

        async def wrapper(message: IncomingMessage):
            await self._handle_message(message, handler)

        await queue.consume(wrapper)
        self.logger.info(f"Начал слушать очередь {queue_name}")

    async def _handle_message(self, message: IncomingMessage, handler):
        """Вызов пользовательского обработчика"""
        try:
            async with message.process():  # подтверждение ack/nack автоматически
                await handler(message)  # вызываем твой кастомный обработчик
        except Exception as e:
            self.logger.error(f"Ошибка обработки сообщения: {e}")

    async def close(self):
        """Закрытие соединения."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.logger.info("Соединение RabbitMQ закрыто")

