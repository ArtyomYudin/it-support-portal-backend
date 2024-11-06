from rest_framework import serializers
from .models import CardOwner, Event, AccessPoint


class CardOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardOwner
        fields = ['system_id', 'lastname', 'firstname', 'secondname']

class AccessPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPoint
        fields = ['system_id', 'name']

class EventListSerializer(serializers.ModelSerializer):
    ap_id = AccessPointSerializer()
    owner_id = CardOwnerSerializer()
    class Meta:
        model = Event
        fields = ['created', 'ap_id', 'owner_id']

    #def get_current_day_events(self, instance):
    #    event = instance.

