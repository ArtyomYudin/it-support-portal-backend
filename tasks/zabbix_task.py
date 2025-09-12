# tasks.py
import asyncio
import aiohttp
import logging
import os
from celery import shared_task

from core.settings import settings
from core.logging_config import logger

async def get_provider_info(token: str = None, retry_count: int = 0):
    if retry_count > 0:
        logger.info("Retry fetch!")

    post_data = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "id": 1,
        "auth": settings.ZABBIX_AUTH_TOKEN,
        "params": {
            "hostids": [10149, 10199],
            "output": ["hostid", "key_", "name", "lastvalue"],
            "filter": {
                "key_": [
                    "net.if.in[ifHCInOctets.6]",
                    "net.if.out[ifHCOutOctets.6]",
                    "net.if.in[ifHCInOctets.3]",
                    "net.if.out[ifHCOutOctets.3]",
                    "net.if.in[ifHCInOctets.4]",
                    "net.if.out[ifHCOutOctets.4]",
                ],
            },
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=settings.ZABBIX_HOST,
                json=post_data,
                headers={"Content-Type": "application/json-rpc"},
            ) as response:
                data = await response.json()
                return data.get("result", [])
    except Exception as e:
        logger.error(f"get_provider_info error: {e}")
        if retry_count < 3:
            return await get_provider_info(token, retry_count + 1)
        return False

@shared_task(bind=True, max_retries=3)
def fetch_provider_info_task(self, token=None):
    try:
        result = asyncio.run(get_provider_info(token=token))
        return result
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)