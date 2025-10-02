import asyncio
import email
import imaplib
import json
import aio_pika
import aiohttp
from celery import shared_task

from core.settings import settings
from core.logging_config import logger
from utils.celery import publish_to_exchange

RABBITMQ_URL = f"amqp://{settings.RMQ_CELERY_USER}:{settings.RMQ_CELERY_PASSWORD}@{settings.RMQ_HOST}:{settings.RMQ_PORT}/{settings.RMQ_VIRTUAL_HOST}"


def imap_client():
    mail = imaplib.IMAP4_SSL(settings.IMAP_HOST)
    mail.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
    mail.select('inbox')

    status, data = mail.search(None, 'UNSEEN')
    messages = []
    for num in data[0].split():
        status, msg_data = mail.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        messages.append(msg.as_string())

    mail.logout()
    return messages





@shared_task
def process_email(raw_message):
    msg = email.message_from_string(raw_message)
    logger.debug(f"New email from: {msg['From']} | Subject: {msg['Subject']}")

    # with Session() as session:
    #     req = create_user_request_with_lifecycle(
    #         session=session,
    #         creator_upn="user@example.com",
    #         initiator_upn="user@example.com",
    #         executor_upn="executor@example.com",
    #         service_id=1,
    #         topic="Проблема с доступом",
    #         description="Не могу зайти в систему",
    #         status_id=1,
    #         priority_id=2,
    #         deadline=date(2025, 12, 31),
    #     )
    #     session.commit()  # ← фиксируем обе записи
    #     print(f"Заявка создана: {req.formatted_reg_number}")

@shared_task(bind=True, max_retries=3)
def check_email(self):
    try:
        for raw_msg in imap_client():
            process_email.delay(raw_msg)
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
