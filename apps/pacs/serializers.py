from rest_framework import serializers
from .models import CardOwner, Event, AccessPoint


class CardOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardOwner
        fields = ['system_id', 'lastname']

class AccessPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPoint
        fields = ['system_id', 'name']

class EventSerializer(serializers.ModelSerializer):
    #ap_id = AccessPointSerializer()
    #owner_id = CardOwnerSerializer()
    class Meta:
        model = Event
        fields = '__all__'
        #fields = ['name']
