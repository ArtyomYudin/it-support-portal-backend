import asyncio

from django.shortcuts import render
from .models import CardOwner, Event
from rest_framework import generics
from .serializers import CardOwnerSerializer, EventSerializer

from .tcp_client import TcpClient

class CustomerList(generics.ListAPIView):
    # API endpoint that allows customer to be viewed.
    queryset = CardOwner.objects.all()
    serializer_class = CardOwnerSerializer

class EventList(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

pacs_tcp_client = TcpClient()
pacs_tcp_client.connect()