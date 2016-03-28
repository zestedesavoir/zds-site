# coding: utf-8

from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from zds.member.api.permissions import CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly
from zds.utils.models import Comment
from zds.utils.api.serializers import KarmaSerializer


class KarmaView(RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = KarmaSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, CanReadAndWriteNowOrReadOnly, IsNotOwnerOrReadOnly)
