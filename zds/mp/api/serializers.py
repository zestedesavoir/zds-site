from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from dry_rest_permissions.generics import DRYPermissionsField
from rest_framework import serializers
from zds.api.serializers import ZdSModelSerializer

from zds.member.api.serializers import UserListSerializer
from zds.mp.commons import UpdatePrivatePost
from zds.mp.models import PrivateTopic, PrivatePost
from zds.mp.validators import ParticipantsUserValidator, TitleValidator, TextValidator
from zds.utils.mps import send_mp, send_message_mp


class PrivatePostSerializer(ZdSModelSerializer):
    """
    Serializers of a private post object.
    """
    permissions = DRYPermissionsField()

    class Meta:
        model = PrivatePost
        fields = '__all__'
        serializers = (UserListSerializer,)
        formats = {'Html': 'text_html', 'Markdown': 'text'}
        read_only_fields = ('permissions',)


class PrivateTopicSerializer(ZdSModelSerializer):
    """
    Serializers of a private topic object.
    """
    permissions = DRYPermissionsField()

    class Meta:
        model = PrivateTopic
        fields = '__all__'
        serializers = (PrivatePostSerializer, UserListSerializer,)
        read_only_fields = ('permissions',)


class PrivateTopicCreateSerializer(serializers.ModelSerializer, TitleValidator, TextValidator,
                                   ParticipantsUserValidator):
    """
    Serializer to create a new private topic.
    """
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=True, )
    text = serializers.CharField()
    permissions = DRYPermissionsField()

    class Meta:
        model = PrivateTopic
        fields = ('id', 'title', 'subtitle', 'participants', 'text',
                  'author', 'participants', 'last_message', 'pubdate',
                  'permissions')
        read_only_fields = ('id', 'author', 'last_message', 'pubdate', 'permissions')

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
    permissions = DRYPermissionsField()

    class Meta:
        model = PrivateTopic
        fields = ('id', 'title', 'subtitle', 'participants', 'permissions',)
        read_only_fields = ('id', 'permissions',)

    def update(self, instance, validated_data):
        for attr, value in list(validated_data.items()):
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


class PrivatePostActionSerializer(serializers.ModelSerializer, TextValidator, UpdatePrivatePost):
    """
    Serializer to update the last private post of a private topic.
    """
    permissions = DRYPermissionsField()

    class Meta:
        model = PrivatePost
        fields = ('id', 'privatetopic', 'author', 'text', 'text_html', 'pubdate', 'update', 'position_in_topic',
                  'permissions')
        read_only_fields = ('id', 'privatetopic', 'author', 'text_html', 'pubdate', 'update', 'position_in_topic',
                            'permissions')

    def create(self, validated_data):
        # Get topic
        pk_ptopic = self.context.get('view').kwargs.get('pk_ptopic')
        topic = get_object_or_404(PrivateTopic, pk=(pk_ptopic))

        # Get author
        author = self.context.get('view').request.user

        # Send post in mp
        send_message_mp(author, topic, self.validated_data.get('text'), True, False)
        return topic.last_message

    def update(self, instance, validated_data):
        return self.perform_update(instance, validated_data)

    def throw_error(self, key=None, message=None):
        raise serializers.ValidationError(message)
