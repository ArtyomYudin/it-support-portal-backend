import asyncio
import json
import aio_pika
import aiohttp
from celery import shared_task

from core.settings import settings
from core.logging_config import logger
from api.ws.manager import manager


async def get_provider_info(token: str = None, retry_count: int = 0):
    if retry_count > 0:
        logger.info("Retry fetch!")

    post_data_host_1 = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {
            # "hostids": [10149, 10199],
            "hostids": [10149],
            "output": ["hostid", "key_", "name", "lastvalue"],
            "filter": {
                "key_": [
                    "net.if.in[ifHCInOctets.4]",
                    "net.if.out[ifHCOutOctets.4]",
                    "net.if.in[ifHCInOctets.15]",
                    "net.if.out[ifHCOutOctets.15]",
                ],
            },
        },
    }

    post_data_host_2 = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {
            # "hostids": [10149, 10199],
            "hostids": [10199],
            "output": ["hostid", "key_", "name", "lastvalue"],
            "filter": {
                "key_": [
                    "net.if.in[ifHCInOctets.7]",
                    "net.if.out[ifHCOutOctets.7]",
                ],
            },
        },
    }

    async def fetch(session, post_data):
        async with session.post(
                url=settings.ZABBIX_HOST,
                json=post_data,
                headers={"Content-Type": "application/json-rpc"},
        ) as response:
            data = await response.json()
            return data.get("result", [])

    try:
        async with aiohttp.ClientSession() as session:
            # Параллельные запросы к двум хостам
            results_host1, results_host2 = await asyncio.gather(
                fetch(session, post_data_host_1),
                fetch(session, post_data_host_2)
            )
            # Объединяем результаты
            combined_results = results_host1 + results_host2
            return combined_results
    except Exception as e:
        logger.error(f"get_provider_info error: {e}")
        if retry_count < 3:
            return await get_provider_info(token, retry_count + 1)
        return False

async def publish_provider_info(token: str ):
    provider_info = await get_provider_info(token=token)
    # logger.info(provider_info)
    provider_speed = {
        "inSpeedFilanco": f"{int(provider_info[3]['lastvalue']) / 1000 / 1000:.2f}",
        "outSpeedFilanco": f"{int(provider_info[1]['lastvalue']) / 1000 / 1000:.2f}",
        "inSpeedErTelecom100": f"{int(provider_info[0]['lastvalue']) / 1000 / 1000:.2f}",
        "outSpeedErTelecom100": f"{int(provider_info[2]['lastvalue']) / 1000 / 1000:.2f}",
        "inSpeedErTelecom200": f"{int(provider_info[4]['lastvalue']) / 1000 / 1000:.2f}",
        "outSpeedErTelecom200": f"{int(provider_info[5]['lastvalue']) / 1000 / 1000:.2f}",
    }

    url = f"amqp://{settings.RMQ_CELERY_USER}:{settings.RMQ_CELERY_PASSWORD}@{settings.RMQ_HOST}:{settings.RMQ_PORT}/{settings.RMQ_VIRTUAL_HOST}"
    connection = await aio_pika.connect_robust(url)

    payload = {
        "event": "event_provider_info",
        "data": {"results": provider_speed, "total": len(provider_speed)},
    }

    async with connection:
        channel = await connection.channel()
        # Fanout exchange для всех подписчиков
        exchange = await channel.declare_exchange("celery_beat", aio_pika.ExchangeType.FANOUT)
        await exchange.publish(
            aio_pika.Message(body=json.dumps(payload).encode()),
            routing_key=""
        )


@shared_task(bind=True, max_retries=3)
def fetch_provider_info_task(self, token=None):
    try:
        asyncio.run(publish_provider_info(token=token))
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)