import json
import logging
from datetime import datetime

from channels.generic.websocket import WebsocketConsumer, JsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

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
        #user = self.scope['user']
        #if user.is_authenticated:
            logger.info("Connected to websocket")
            self.accept()
        #else:
        #    self.close(code=1000)

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
        data = {
            "event": "event_pacs_entry_exit",
            "data": {
                "results": {"eventDate": "2024-11-02 11:48:27", "displayName": "Test Tes Test", "accessPoint": "20"},
                "total": 1
            }
        }
        send_mess = json.dumps(data)
        #print(send_mess)
        #self.send(data)
