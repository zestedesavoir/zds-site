from rest_framework.permissions import IsAuthenticatedOrReadOnly

from zds.forum.models import Post
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, CanReadTopic, IsNotOwnerOrReadOnly
from zds.utils.api.views import KarmaView


class PostKarmaView(KarmaView):
    queryset = Post.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly, CanReadTopic)
