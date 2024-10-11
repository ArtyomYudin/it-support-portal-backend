import asyncio

from django.core.serializers import serialize
from django.shortcuts import render
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import CardOwner, Event
from rest_framework import generics
from .serializers import CardOwnerSerializer, EventSerializer

from .tcp_client import TcpClient

#class CustomerList(generics.ListAPIView):
#    # API endpoint that allows customer to be viewed.
#    queryset = CardOwner.objects.all()
#    serializer_class = CardOwnerSerializer

#class EventList(generics.ListAPIView):
#    queryset = Event.objects.all()
#    serializer_class = EventSerializer

@extend_schema(
    summary='List all events',
    description='',
    #request='',
    responses={200: EventSerializer}
)
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_all_events(request):
    queryset = Event.objects.all()
    serializer = EventSerializer(queryset, many=True)
    return Response(serializer.data)



#pacs_tcp_client = TcpClient()
#pacs_tcp_client.connect()