from dry_rest_permissions.generics import DRYPermissions
from rest_framework.serializers import ModelSerializer

from zds.tutorialv2.models.database import PublicationEvent, Clap


class PublicationEventSerializer(ModelSerializer):
    """
    Serializer of a subscription object.
    """

    class Meta:
        model = PublicationEvent
        fields = ("state_of_processing", "format_requested", "date", "url")
        permissions_classes = DRYPermissions


class ClapSerializer(ModelSerializer):
    class Meta:
        model = Clap
        fields = ["user", "publication"]
