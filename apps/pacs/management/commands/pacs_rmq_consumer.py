import json
import os
from datetime import datetime, timedelta

import pika
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import logging

from ...models import Event
from ...serializers import EventListSerializer
logger = logging.getLogger(__name__)
#logger.critical("Now logging consumer command")

class Command(BaseCommand):

    def handle(self, *args, **options):
        rmq_connection_params = pika.ConnectionParameters(
            host=settings.RMQ_HOST,
            port=settings.RMQ_PORT,
            virtual_host=settings.RMQ_VIRTUAL_HOST,
            credentials=pika.PlainCredentials(
                username=settings.RMQ_USER,
                password=settings.RMQ_PASSWORD
            )
        )
        queue_name = 'pacs_client'
        connection = pika.BlockingConnection(rmq_connection_params)
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)

        channel.basic_consume(queue=queue_name, on_message_callback=self.send_to_pacs_channel, auto_ack=True)

        logger.critical(f"Waiting for messages in {queue_name}. To exit press CTRL+C")
        channel.start_consuming()

    @staticmethod
    def send_to_pacs_channel(ch, method, properties, body, channel_layer=None):
        #events = Event.objects.filter(created__gte=datetime.now().date())
        events = Event.objects.filter(id = int(body))
        tt = EventListSerializer(instance=events, many=True)
        logger.info(tt.data)

        channel_layer = get_channel_layer()
        #data = [{"eventDate": "2024-11-15 13:28:27", "displayName": "Test Tes Test", "accessPoint": "20"}]
        data = {
                'event': 'event_pacs_entry_exit',
                'data': {
                    'results': [tt.data[0]],
                    'total': 1101,
                }
             }

        async_to_sync(channel_layer.group_send)(
            'pacs',
            {
                'type': 'pacs.message',
                'text': data,
                'sender': 'Test'
            },
        )