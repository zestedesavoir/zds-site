from rest_framework import serializers
from dry_rest_permissions.generics import DRYPermissionsField

from zds.api.serializers import ZdSModelSerializer
from zds.gallery.models import Gallery
from zds.gallery.mixins import GalleryCreateMixin
from zds.member.api.serializers import UserListSerializer


class CustomParticipantField(serializers.Field):
    def to_representation(self, value):
        participants = []
        for user_pk, user_perms in value.items():
            participants.append({
                'pk': user_pk,
                'permissions': user_perms
            })

        return participants


class GallerySerializer(ZdSModelSerializer, GalleryCreateMixin):
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
        serializers = (UserListSerializer,)
        read_only_fields = ('id', 'permissions', 'pubdate', 'update', 'slug')

    def create(self, validated_data):
        return self.perform_create(
            validated_data.get('title'),
            self.context.get('request').user,
            validated_data.get('subtitle')
        )
