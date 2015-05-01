# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from rest_framework import serializers

from zds.member.api.generics import ZdSModelSerializer
from zds.member.api.serializers import UserListSerializer
from zds.mp.commons import ParticipantsUserValidator, TitleValidator, TextValidator
from zds.mp.models import PrivateTopic, PrivatePost
from zds.utils.mps import send_mp


class PrivatePostSerializer(ZdSModelSerializer):
    """
    Serializers of a private post object.
    """

    class Meta:
        model = PrivatePost
        serializers = (UserListSerializer,)
        formats = {'Html': 'text_html', 'Markdown': 'text'}


class PrivateTopicSerializer(ZdSModelSerializer):
    """
    Serializers of a private topic object.
    """

    class Meta:
        model = PrivateTopic
        serializers = (PrivatePostSerializer, UserListSerializer,)


class PrivateTopicCreateSerializer(serializers.ModelSerializer, TitleValidator, TextValidator,
                                   ParticipantsUserValidator):
    """
    Serializer to create a new private topic.
    """
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=True, )
    text = serializers.CharField()

    class Meta:
        model = PrivateTopic
        fields = ('title', 'subtitle', 'participants', 'text')

    def create(self, validated_data):
        # This hack is necessary because `text` isn't a field of PrivateTopic.
        self._fields.pop('text')
        return send_mp(self.context.get('request').user,
                       validated_data.get('participants'),
                       validated_data.get('title'),
                       validated_data.get('subtitle') or '',
                       validated_data.get('text'),
                       True,
                       False)

    def get_current_user(self):
        return self.context.get('request').user

    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)


class PrivateTopicUpdateSerializer(serializers.ModelSerializer, TitleValidator, TextValidator,
                                   ParticipantsUserValidator):
    """
    Serializer to update a private topic.
    """
    can_be_empty = True
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
