# -*- coding: utf-8 -*-
from dry_rest_permissions.generics import DRYPermissions
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from zds.member.api.serializers import UserListSerializer
from zds.notification.models import Notification


class NotificationSerializer(ModelSerializer):
    """
    Serializers of a notification object.
    """
    content_type = SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'title', 'is_read', 'url', 'sender', 'pubdate', 'content_type',)
        serializers = (UserListSerializer,)
        permissions_classes = DRYPermissions

    def get_content_type(self, obj):
        return obj.subscription.content_type.model
