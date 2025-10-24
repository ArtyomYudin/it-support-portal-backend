import asyncio
import json
import aio_pika
import aiohttp
from celery import shared_task
from typing import List, Dict, Any, Optional, Union
from redis.asyncio import Redis

from core.settings import settings
from core.logging_config import logger
from utils.celery import publish_to_exchange

RABBITMQ_URL = (
    f"amqp://{settings.RMQ_CELERY_USER}:{settings.RMQ_CELERY_PASSWORD}"
    f"@{settings.RMQ_HOST}:{settings.RMQ_PORT}/{settings.RMQ_VIRTUAL_HOST}"
)

REDIS_URL = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

def safe_float(value: str, default: float = 0.0) -> float:
    """Безопасно преобразует строку в float, обрабатывая ошибки и научную нотацию."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Cannot convert to float: {value!r}")
        return default


def safe_int(value: str, default: int = 0) -> int:
    """Безопасно преобразует строку в int через float (для поддержки '1.23e6')."""
    return int(safe_float(value, float(default)))


async def _fetch_data(session: aiohttp.ClientSession, post_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Выполняет POST-запрос к Zabbix API и возвращает результат."""
    timeout = aiohttp.ClientTimeout(total=10)
    async with session.post(
            url=settings.ZABBIX_HOST,
            json=post_data,
            headers={"Content-Type": "application/json-rpc"},
            timeout=timeout,
    ) as response:
        data = await response.json()
        # Логируем ошибки Zabbix API (например, invalid auth)
        if "error" in data:
            logger.error(f"Zabbix API error: {data['error']}")
        return data.get("result", [])


async def _get_hardware_groups(token: str = None, retry_count: int = 0) -> List[Dict[str, str]]:
    """Получает список групп оборудования из Zabbix."""
    post_data = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {"output": ["groupid", "name"]},
    }

    try:
        async with aiohttp.ClientSession() as session:
            groups = await _fetch_data(session, post_data)
            return [{"id": g["groupid"], "name": g["name"]} for g in groups]
    except Exception as e:
        logger.error(f"Error fetching hardware groups: {e}")
        if retry_count < 3:
            await asyncio.sleep(0.5 * (retry_count + 1))
            return await _get_hardware_groups(token, retry_count + 1)
        return []


async def get_provider_info(token: str = None, retry_count: int = 0) -> Union[List[Dict[str, Any]], bool]:
    """Получает данные о трафике провайдеров."""
    if retry_count > 0:
        logger.info("Retry fetch provider info")

    post_data_host_1 = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {
            "hostids": ["10149"],
            "output": ["hostid", "key_", "lastvalue"],
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
            "hostids": ["10199"],
            "output": ["hostid", "key_", "lastvalue"],
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
            results_host1, results_host2 = await asyncio.gather(
                _fetch_data(session, post_data_host_1),
                _fetch_data(session, post_data_host_2)
            )
            return results_host1 + results_host2
    except Exception as e:
        logger.error(f"get_provider_info error: {e}")
        if retry_count < 3:
            await asyncio.sleep(0.5 * (retry_count + 1))
            return await get_provider_info(token, retry_count + 1)
        return False


async def publish_provider_info(token: str) -> None:
    provider_info = await get_provider_info(token=token)

    if not provider_info or provider_info is False:
        logger.error("Provider info is empty or failed, skipping publish")
        return

    # Собираем данные в словарь по (hostid, key_)
    items_map = {}
    for item in provider_info:
        hostid = item.get("hostid")
        key = item.get("key_")
        if hostid and key:
            items_map[(hostid, key)] = item.get("lastvalue", "0")

    def get_mbps(hostid: str, key: str) -> str:
        raw_val = items_map.get((hostid, key), "0")
        mbps = safe_int(raw_val) / 1_000_000
        return f"{mbps:.2f}"

    provider_speed = {
        "inSpeedFilanco": get_mbps("10149", "net.if.in[ifHCInOctets.4]"),
        "outSpeedFilanco": get_mbps("10149", "net.if.out[ifHCOutOctets.4]"),
        "inSpeedErTelecom100": get_mbps("10149", "net.if.in[ifHCInOctets.15]"),
        "outSpeedErTelecom100": get_mbps("10149", "net.if.out[ifHCOutOctets.15]"),
        "inSpeedErTelecom200": get_mbps("10199", "net.if.in[ifHCInOctets.7]"),
        "outSpeedErTelecom200": get_mbps("10199", "net.if.out[ifHCOutOctets.7]"),
    }

    payload = {
        "event": "event_provider_info",
        "data": {"results": provider_speed, "total": len(provider_speed)},
    }
    await publish_to_exchange(payload, RABBITMQ_URL)

    async with Redis.from_url(REDIS_URL, decode_responses=True) as redis:
        await redis.set("latest:event_provider_info", json.dumps(payload))


async def fetch_problems_for_group(session: aiohttp.ClientSession, group: Dict[str, str]) -> Dict[str, Any]:
    """Получает проблемы для одной группы оборудования."""
    post_data = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {
            "groupids": [group["id"]],
            "severities": [2, 3, 4, 5],
            "sortfield": ["eventid"],
            "sortorder": "DESC",
        },
    }
    try:
        problems = await _fetch_data(session, post_data)
        return {
            "group": group["name"],
            "event": problems,
            "count": len(problems)
        }
    except Exception as e:
        logger.error(f"Failed to fetch problems for group {group['name']}: {e}")
        return {
            "group": group["name"],
            "event": [],
            "count": 0
        }


async def get_hardware_group_problem(token: str = None, retry_count: int = 0) -> List[Dict[str, Any]]:
    """Получает проблемы по всем группам оборудования параллельно."""
    hardware_groups = await _get_hardware_groups(token=token)

    if not hardware_groups:
        logger.warning("No hardware groups found.")
        return []

    if retry_count > 0:
        logger.info("Retry fetch hardware problems")

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_problems_for_group(session, group) for group in hardware_groups]
        results = await asyncio.gather(*tasks)
    return results


async def publish_hardware_group_problem(token: str) -> None:
    hardware_problem = await get_hardware_group_problem(token=token)
    payload = {
        "event": "event_hardware_group_alarm",
        "data": {"results": hardware_problem, "total": len(hardware_problem)},
    }
    await publish_to_exchange(payload, RABBITMQ_URL)

    async with Redis.from_url(REDIS_URL, decode_responses=True) as redis:
        await redis.set("latest:event_hardware_group_alarm", json.dumps(payload))


async def get_avaya_e1_channel_info(token: str = None, retry_count: int = 0) -> Union[Dict[str, int], bool]:
    """Получает информацию о каналах E1 на Avaya."""
    if retry_count > 0:
        logger.info("Retry fetch Avaya E1 info")

    post_data = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {
            "hostids": ["10254"],
            "output": ["lastvalue"],
            "sortfield": "itemid",
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            e1_channels = await _fetch_data(session, post_data)
            active = sum(
                1 for ch in e1_channels
                if ch.get("lastvalue") == "in-service/active"
            )
            return {"active": active, "total": len(e1_channels)}
    except Exception as e:
        logger.error(f"get_avaya_e1_channel_info error: {e}")
        if retry_count < 3:
            await asyncio.sleep(0.5 * (retry_count + 1))
            return await get_avaya_e1_channel_info(token, retry_count + 1)
        return False


async def publish_avaya_e1_channel_info(token: str) -> None:
    e1_info = await get_avaya_e1_channel_info(token=token)

    if not e1_info or e1_info is False:
        logger.error("Avaya E1 info is empty or failed, skipping publish")
        return

    payload = {
        "event": "event_avaya_e1_channel_info",
        "data": {
            "activeChannel": e1_info["active"],
            "allChannel": e1_info["total"]
        },
    }
    await publish_to_exchange(payload, RABBITMQ_URL)

    async with Redis.from_url(REDIS_URL, decode_responses=True) as redis:
        await redis.set("latest:event_avaya_e1_channel_info", json.dumps(payload))


# === Celery Tasks ===

@shared_task(bind=True, max_retries=3)
def fetch_provider_info_task(self, token: Optional[str] = None):
    try:
        asyncio.run(publish_provider_info(token=token))
    except Exception as exc:
        logger.error(f"Task fetch_provider_info_task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def fetch_hardware_group_problem_task(self, token: Optional[str] = None):
    try:
        asyncio.run(publish_hardware_group_problem(token=token))
    except Exception as exc:
        logger.error(f"Task fetch_hardware_group_problem_task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
def fetch_avaya_e1_channel_info_task(self, token: Optional[str] = None):
    try:
        asyncio.run(publish_avaya_e1_channel_info(token=token))
    except Exception as exc:
        logger.error(f"Task fetch_avaya_e1_channel_info_task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)