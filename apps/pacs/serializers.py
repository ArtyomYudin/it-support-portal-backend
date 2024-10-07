from rest_framework import serializers
from .models import CardOwner, Event


class CardOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardOwner
        fields = ['system_id', 'user_principal_name', 'display_name']

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

