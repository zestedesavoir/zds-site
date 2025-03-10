from django.conf import settings
from django.utils.translation import gettext_lazy as _
from dry_rest_permissions.generics import DRYPermissionsField
from rest_framework import exceptions, serializers

from zds.api.serializers import ZdSModelSerializer
from zds.gallery.mixins import (
    GalleryCreateMixin,
    GalleryUpdateOrDeleteMixin,
    ImageCreateMixin,
    ImageTooLarge,
    ImageUpdateOrDeleteMixin,
    NotAnImage,
    UserNotInGallery,
)
from zds.gallery.models import Gallery, Image, UserGallery
from zds.member.models import User


class CustomParticipantField(serializers.Field):
    def to_representation(self, value):
        participants = []
        for user_pk, user_perms in value.items():
            participants.append({"id": user_pk, "permissions": user_perms})

        return participants


class ImageTooLargeError(exceptions.ValidationError):
    def __init__(self, e):
        super().__init__(
            detail=_("Votre image est trop lourde ({} Kio). La taille maximum est de {} Kio !").format(
                e.size / 1024, settings.ZDS_APP["gallery"]["image_max_size"] / 1024
            )
        )


class NotAnImageError(exceptions.ValidationError):
    def __init__(self):
        super().__init__(detail=_("Format d'image inconnu"))


class GallerySerializer(ZdSModelSerializer, GalleryCreateMixin, GalleryUpdateOrDeleteMixin):
    """
    Serializer of a gallery
    """

    permissions = DRYPermissionsField()
    linked_content = serializers.IntegerField(read_only=True)
    image_count = serializers.IntegerField(read_only=True, default=0, allow_null=False)
    participants = CustomParticipantField(source="get_users_and_permissions", read_only=True)

    class Meta:
        model = Gallery
        fields = "__all__"
        read_only_fields = ("id", "permissions", "pubdate", "update", "slug")

    def create(self, validated_data):
        return self.perform_create(
            validated_data.get("title"), self.context.get("request").user, validated_data.get("subtitle", "")
        )

    def update(self, instance, validated_data):
        self.gallery = instance
        return self.perform_update(validated_data)


class ImageSerializer(ZdSModelSerializer, ImageCreateMixin, ImageUpdateOrDeleteMixin):
    """
    Serializer of an image
    """

    permissions = DRYPermissionsField()
    thumbnail = serializers.CharField(source="get_thumbnail_url", read_only=True)
    url = serializers.CharField(source="get_absolute_url", read_only=True)
    physical = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Image
        read_only_fields = ("id", "slug", "permissions", "gallery", "pubdate", "update", "url", "thumbnail")
        fields = read_only_fields + ("title", "legend", "physical")

    def create(self, validated_data):
        if "physical" not in validated_data:
            raise exceptions.ValidationError(detail=_("Le champ `physical` est requis pour ajouter une image"))

        try:
            self.gallery = Gallery.objects.get(pk=self.context["view"].kwargs.get("pk_gallery"))
        except Gallery.DoesNotExist:
            raise exceptions.NotFound(detail=_("Galerie introuvable"))

        try:
            return self.perform_create(
                title=validated_data.get("title"),
                physical=validated_data.get("physical"),
                legend=validated_data.get("legend", ""),
            )
        except ImageTooLarge as e:
            raise ImageTooLargeError(e)
        except NotAnImage:
            raise NotAnImageError()

    def update(self, instance, validated_data):
        self.image = instance
        try:
            return self.perform_update(validated_data)
        except ImageTooLarge as e:
            raise ImageTooLargeError(e)
        except NotAnImage:
            raise NotAnImageError()


class CustomPermissionField(serializers.Field):
    def to_representation(self, value):
        return {"read": True, "write": value}


class ParticipantSerializer(ZdSModelSerializer, GalleryUpdateOrDeleteMixin):
    permissions = CustomPermissionField(source="can_write", read_only=True)
    id = serializers.IntegerField(source="user.pk", required=False)
    can_write = serializers.BooleanField(write_only=True)

    class Meta:
        model = UserGallery
        fields = ("id", "permissions", "can_write")

    def get_permissions(self, obj):
        return {"read": True, "write": obj.can_write()}

    def create(self, validated_data):
        if "user" not in validated_data:
            raise exceptions.ValidationError(_("Le champ `id` est obligatoire pour l'ajout d'un participant"))

        try:
            self.gallery = Gallery.objects.get(pk=self.context["view"].kwargs.get("pk_gallery"))
            self.users_and_permissions = self.gallery.get_users_and_permissions()
        except Gallery.DoesNotExist:
            raise exceptions.NotFound(detail=_("Gallerie introuvable"))

        try:
            user = User.objects.get(**validated_data.get("user"))
        except User.DoesNotExist:
            raise exceptions.ValidationError(detail=_("L'utilisateur n'existe pas"))

        if UserGallery.objects.filter(gallery=self.gallery, user=user).exists():
            raise exceptions.ValidationError(detail=_("L'utilisateur est déjà un participant"))

        return self.perform_add_user(user, can_write=validated_data.get("can_write", False))

    def update(self, instance, validated_data):
        self.gallery = instance.gallery
        self.users_and_permissions = self.gallery.get_users_and_permissions()

        try:
            return self.perform_update_user(instance.user, can_write=validated_data.get("can_write", False))
        except UserNotInGallery:
            raise exceptions.ValidationError(detail=_("L'utilisateur n'est pas/plus un participant!"))
