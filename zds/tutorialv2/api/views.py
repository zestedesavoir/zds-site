from rest_framework.permissions import IsAuthenticatedOrReadOnly
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.utils.api.views import KarmaView
from zds.tutorialv2.models.models_database import ContentReaction


class ContentReactionKarmaView(KarmaView):
    queryset = ContentReaction.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly)
