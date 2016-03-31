# coding: utf-8

from rest_framework.generics import RetrieveUpdateDestroyAPIView
from zds.utils.models import Comment
from zds.utils.api.serializers import KarmaSerializer


class KarmaView(RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = KarmaSerializer
