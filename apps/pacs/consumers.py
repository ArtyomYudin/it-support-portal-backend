import json
import logging

from channels.generic.websocket import WebsocketConsumer

logger = logging.getLogger(__name__)

class PacsConsumer(WebsocketConsumer):
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
        #self.send(text_data=text_data)
