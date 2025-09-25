import asyncio
import json
import aio_pika
import aiohttp
from celery import shared_task

from core.settings import settings
from core.logging_config import logger
from utils.celery import publish_to_exchange

RABBITMQ_URL = f"amqp://{settings.RMQ_CELERY_USER}:{settings.RMQ_CELERY_PASSWORD}@{settings.RMQ_HOST}:{settings.RMQ_PORT}/{settings.RMQ_VIRTUAL_HOST}"


async def _fetch_data(session, post_data):
    async with session.post(
            url=settings.ZABBIX_HOST,
            json=post_data,
            headers={"Content-Type": "application/json-rpc"},
    ) as response:
        data = await response.json()
        return data.get("result", [])


async def _get_hardware_groups(token: str = None, retry_count: int = 0):
    post_data = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {
            "output": ["groupid", "name"],
        },
    }
    try:
        async with aiohttp.ClientSession() as session:
            groups = []
            hardware_groups =  await _fetch_data(session, post_data)
            for group in hardware_groups:
                groups.append({ "id": group["groupid"], "name": group["name"] })
            return groups

    except Exception as e:
        logger.error(f"get_provider_info error: {e}")
        if retry_count < 3:
            return await _get_hardware_groups(token, retry_count + 1)
        return False

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

    try:
        async with aiohttp.ClientSession() as session:
            # Параллельные запросы к двум хостам
            results_host1, results_host2 = await asyncio.gather(
                _fetch_data(session, post_data_host_1),
                _fetch_data(session, post_data_host_2)
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

    payload = {
        "event": "event_provider_info",
        "data": {"results": provider_speed, "total": len(provider_speed)},
    }

    await publish_to_exchange(payload, RABBITMQ_URL)

async def get_hardware_group_problem(token: str = None, retry_count: int = 0):
    hardware_groups = await _get_hardware_groups(token=token)

    if retry_count > 0:
        logger.info("Retry fetch!")

    hw_group_problems = []

    for hardware_group in hardware_groups:
        post_data = {
            "jsonrpc": "2.0",
            "method": "problem.get",
            "id": 1,
            "auth": settings.ZABBIX_AUTH_TOKEN,
            "params": {
                "groupids": hardware_group["id"],
                "severities": [2, 3, 4, 5],
                "sortfield": ["eventid"],
                "sortorder": "DESC",
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                problems =  await _fetch_data(session, post_data)
                hw_group_problems.append({ "group": hardware_group["name"], "event": problems, "count": len(problems) })
        except Exception as e:
            logger.error(f"Failed to fetch problems for group {hardware_group['name']}: {e}")
            # Пропускаем эту группу, но не падаем и не ретраим всю функцию
            continue

    return hw_group_problems

async def publish_hardware_group_problem(token: str):
    hardware_problem = await get_hardware_group_problem(token=token)
    payload = {
        "event": "event_hardware_group_alarm",
        "data": {"results": hardware_problem, "total": len(hardware_problem)},
    }
    await publish_to_exchange(payload, RABBITMQ_URL)


async def get_avaya_e1_channel_info():
    pass

async def publish_avaya_e1_channel_info():
    pass


@shared_task(bind=True, max_retries=3)
def fetch_provider_info_task(self, token=None):
    try:
        asyncio.run(publish_provider_info(token=token))
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(bind=True, max_retries=3)
def fetch_hardware_group_problem_task(self, token=None):
    try:
        asyncio.run(publish_hardware_group_problem(token=token))
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
