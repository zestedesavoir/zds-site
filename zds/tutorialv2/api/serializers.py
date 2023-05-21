from dry_rest_permissions.generics import DRYPermissions
from rest_framework.exceptions import ValidationError
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
    @staticmethod
    def validate_publication(publication):
        if not publication.in_beta() and not publication.in_public():
            raise ValidationError("Le contenu n'est pas disponible", "publication")
        return publication

    class Meta:
        model = Clap
        fields = ["user", "publication"]
