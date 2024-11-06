import json
import logging
from datetime import datetime

from channels.generic.websocket import WebsocketConsumer
from .models import Event
from .serializers import EventListSerializer

logger = logging.getLogger(__name__)

class PacsConsumer(WebsocketConsumer):

    def current_day_event(self):
        events = Event.objects.filter(created__gte = datetime.now().date())
        tt = EventListSerializer(instance=events, many=True)
        #logger.info(tt.data)
        return events

    def connect(self):
        logger.info("Connected to websocket")
        self.accept()

    def disconnect(self, close_code):
        logger.info("Disconnected to websocket")

    def receive(self, text_data):
        response = json.loads(text_data)
        event = response.get("event", None)
        message = response.get("message", None)
        logger.info('!!!!!!!!!!!!!!!!!!!!!!')
        logger.info(response)
        logger.info('!!!!!!!!!!!!!!!!!!!!!!')
        self.current_day_event()
        #self.send(text_data=text_data)
