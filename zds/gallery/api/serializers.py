from rest_framework import serializers
from dry_rest_permissions.generics import DRYPermissionsField

from zds.api.serializers import ZdSModelSerializer
from zds.gallery.models import Gallery, Image
from zds.gallery.mixins import GalleryCreateMixin, GalleryUpdateOrDeleteMixin, ImageCreateMixin


class CustomParticipantField(serializers.Field):
    def to_representation(self, value):
        participants = []
        for user_pk, user_perms in value.items():
            participants.append({
                'pk': user_pk,
                'permissions': user_perms
            })

        return participants


class GallerySerializer(ZdSModelSerializer, GalleryCreateMixin, GalleryUpdateOrDeleteMixin):
    """
    Serializer of a gallery
    """

    permissions = DRYPermissionsField()
    linked_content = serializers.IntegerField(read_only=True)
    image_count = serializers.IntegerField(read_only=True, default=0, allow_null=False)
    participants = CustomParticipantField(source='get_users_and_permissions', read_only=True)

    class Meta:
        model = Gallery
        fields = '__all__'
        read_only_fields = ('id', 'permissions', 'pubdate', 'update', 'slug')

    def create(self, validated_data):
        return self.perform_create(
            validated_data.get('title'),
            self.context.get('request').user,
            validated_data.get('subtitle')
        )

    def update(self, instance, validated_data):
        self.gallery = instance
        return self.perform_update(validated_data)


class ImageSerializer(ZdSModelSerializer, ImageCreateMixin):
    """
    Serializer of an image
    """

    permissions = DRYPermissionsField()
    thumbnail = serializers.CharField(source='get_thumbnail_url', read_only=True)
    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Image
        fields = (
            'id', 'slug', 'permissions', 'gallery', 'title', 'legend', 'url', 'thumbnail', 'pubdate', 'update')
        read_only_fields = ('id', 'permissions', 'pubdate', 'update', 'slug', 'gallery')
