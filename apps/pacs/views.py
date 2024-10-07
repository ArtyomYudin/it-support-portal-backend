from django.shortcuts import render
from .models import CardOwner, Event
from rest_framework import generics
from .serializers import CardOwnerSerializer, EventSerializer


class CustomerList(generics.ListAPIView):
    # API endpoint that allows customer to be viewed.
    queryset = CardOwner.objects.all()
    serializer_class = CardOwnerSerializer

class EventList(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer