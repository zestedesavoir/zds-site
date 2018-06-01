from rest_framework.permissions import IsAuthenticatedOrReadOnly
from zds.member.api.permissions import CanReadTopic, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.utils.api.views import KarmaView
from zds.forum.models import Post


class PostKarmaView(KarmaView):
    queryset = Post.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly, CanReadTopic)
