from dry_rest_permissions.generics import DRYPermissions
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from zds.member.api.serializers import UserListSerializer
from zds.notification.models import Notification, Subscription


class SubscriptionSerializer(ModelSerializer):
    """
    Serializer of a subscription object.
    """

    content_type = SerializerMethodField()
    user = UserListSerializer()

    class Meta:
        model = Subscription
        fields = ("id", "user", "is_active", "by_email", "content_type", "pubdate", "last_notification")
        permissions_classes = DRYPermissions

    def get_content_type(self, obj):
        return obj.content_type.model


class NotificationSerializer(ModelSerializer):
    """
    Serializer of a notification object.
    """

    content_type = SerializerMethodField()
    subscription = SubscriptionSerializer()
    sender = UserListSerializer()

    class Meta:
        model = Notification
        fields = (
            "id",
            "title",
            "is_read",
            "url",
            "sender",
            "pubdate",
            "content_type",
            "subscription",
        )
        permissions_classes = DRYPermissions

    def get_content_type(self, obj):
        return obj.content_type.model
