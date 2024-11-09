from rest_framework import serializers
from .models import CardOwner, Event, AccessPoint


class CardOwnerSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    class Meta:
        model = CardOwner
        fields = ['system_id', 'lastname', 'firstname', 'secondname', 'display_name']

    def get_display_name(self, obj):
        return f'{obj.lastname} {obj.firstname} {obj.secondname}'

class AccessPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPoint
        fields = ['name']

class EventListSerializer(serializers.ModelSerializer):
    #ap_id = AccessPointSerializer()
    #owner_id = CardOwnerSerializer()
    #owner_name = serializers.SerializerMethodField()
    displayName = serializers.CharField(source='owner_id.lastname', read_only=True)
    accessPoint = serializers.CharField(source='ap_id.name', read_only=True)
    eventDate = serializers.CharField(source='created', read_only=True)
    class Meta:
        model = Event
        fields = ['eventDate',  'displayName', 'accessPoint']

