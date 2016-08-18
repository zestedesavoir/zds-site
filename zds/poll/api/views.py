#!/usr/bin/python
# -*- coding: utf-8 -*-

from rest_framework.generics import RetrieveAPIView

from zds.poll.api.serializers import PollDetailSerializer
from zds.poll.models import Poll


class PollDetailAPIView(RetrieveAPIView):

    serializer_class = PollDetailSerializer
    queryset = Poll.objects.all()
