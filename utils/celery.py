import json
import aio_pika

async def publish_to_exchange(payload: dict, rabbitmq_url: str, exchange_name: str = "celery_beat"):
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.FANOUT, durable=True)
        await exchange.publish(
            aio_pika.Message(body=json.dumps(payload).encode()),
            routing_key=""
        )

