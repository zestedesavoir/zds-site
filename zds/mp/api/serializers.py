# -*- coding: utf-8 -*-
from django.contrib.auth.models import User

from rest_framework import serializers

from zds.mp.commons import ParticipantsUserValidator, TitleValidator, TextValidator
from zds.mp.models import PrivateTopic


class PrivateTopicSerializer(serializers.ModelSerializer):
    """
    Serializers of a private topic object.
    """

    class Meta:
        model = PrivateTopic


class PrivateTopicUpdateSerializer(serializers.ModelSerializer, TitleValidator, TextValidator,
                                   ParticipantsUserValidator):
    title = serializers.CharField(required=False, allow_blank=True)
    subtitle = serializers.CharField(required=False, allow_blank=True)
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False, )

    class Meta:
        model = PrivateTopic
        fields = ('title', 'subtitle', 'participants',)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'participants':
                [instance.participants.add(participant) for participant in value]
            elif value:
                setattr(instance, attr, value)
        instance.save()
        return instance

    def get_current_user(self):
        return self.context.get('request').user

    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)
