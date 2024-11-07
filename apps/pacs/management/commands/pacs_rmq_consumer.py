import os

import pika
from django.core.management.base import BaseCommand, CommandError
import logging

logger = logging.getLogger(__name__)
#logger.critical("Now logging consumer command")

class Command(BaseCommand):

    def handle(self, *args, **options):
        rmq_connection_params = pika.ConnectionParameters(
            host=os.getenv('RMQ_HOST'),
            port=os.getenv('RMQ_PORT'),
            virtual_host=os.getenv('RMQ_VIRTUAL_HOST'),
            credentials=pika.PlainCredentials(
                username=os.getenv('RMQ_USER'),
                password=os.getenv('RMQ_PASSWORD')
            )
        )
        queue_name = 'pacs_client'
        connection = pika.BlockingConnection(rmq_connection_params)
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)

        channel.basic_consume(queue=queue_name, on_message_callback=self.callback, auto_ack=True)

        logger.critical(f"Waiting for messages in {queue_name}. To exit press CTRL+C")
        channel.start_consuming()

    @staticmethod
    def callback(ch, method, properties, body):
        logger.critical(" Received body = %s ", body)
        logger.critical(" [x] Received properties = %s ", properties)
        logger.critical(" [x] Received method = %s ", method)
        #MqReceiveCallback.callback(ch, method, properties, body)

