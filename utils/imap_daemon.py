import asyncio
import email

from imapclient import IMAPClient
# from tasks.process_task import process_email
from core.settings import settings
from core.logging_config import logger


async def idle_loop():
    """Основной цикл IMAP IDLE"""
    while True:
        try:
            # Выбираем тип подключения
            if settings.IMAP_TLS:
                logger.info(f"🔒 Connecting to {settings.IMAP_HOST}:{settings.IMAP_PORT} via SSL")
                client = IMAPClient(settings.IMAP_HOST, port=settings.IMAP_PORT, ssl=True)
            else:
                logger.info(f"🔓 Connecting to {settings.IMAP_HOST}:{settings.IMAP_PORT} without SSL")
                client = IMAPClient(settings.IMAP_HOST, port=settings.IMAP_PORT, ssl=False)
                # если нужно явно STARTTLS
                try:
                    client.starttls()
                    logger.info("🔑 STARTTLS negotiation successful")
                except Exception as e:
                    logger.warning(f"STARTTLS not supported or failed: {e}")

            # Авторизация
            client.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
            client.select_folder("INBOX")

            logger.info("📡 IMAP IDLE started...")

            while True:
                client.idle()
                responses = client.idle_check(timeout=300)  # 5 минут
                if responses:
                    logger.info(f"📩 New IMAP event: {responses}")
                    messages = client.search(["UNSEEN"])
                    for uid in messages:
                        msg_data = client.fetch(uid, ["RFC822"])
                        raw_msg = msg_data[uid][b"RFC822"]
                        #
                        msg = email.message_from_string(raw_msg)
                        logger.info(f"New email from: {msg['From']} | Subject: {msg['Subject']}")
                        #
                        # process_email.delay(raw_msg.decode(errors="ignore"))
                client.idle_done()

        except Exception as e:
            logger.error(f"⚠️ IMAP IDLE error: {e}, reconnect in 60s...")
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(idle_loop())