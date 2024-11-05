from django.urls import re_path, path

from .consumers import PacsConsumer

websocket_urlpatterns = [
    re_path(r'ws/pacs/$', PacsConsumer.as_asgi()),
]