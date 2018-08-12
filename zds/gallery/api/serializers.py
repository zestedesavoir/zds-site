from zds.api.serializers import ZdSModelSerializer
from dry_rest_permissions.generics import DRYPermissionsField

from zds.gallery.models import Gallery
from zds.member.api.serializers import UserListSerializer


class GallerySerializer(ZdSModelSerializer):
    """
    Serializer of a gallery
    """
    permissions = DRYPermissionsField()

    class Meta:
        model = Gallery
        fields = '__all__'
        serializers = (UserListSerializer,)
        read_only_fields = ('permissions',)
