#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.core.exceptions import ObjectDoesNotExist
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response

from zds.poll.api.serializers import PollDetailSerializer, UsersSerializer, VoteSerializer
from zds.poll.models import Poll, Choice, UniqueVote, MultipleVote
from zds.poll.api.permissions import AccessUsersPermission


class PollDetailAPIView(RetrieveAPIView):

    serializer_class = PollDetailSerializer
    queryset = Poll.objects.all()

class UsersDetailAPIView(RetrieveAPIView):

    permissions_classes = (AccessUsersPermission,)
    queryset = Choice.objects.all()
    serializer_class = UsersSerializer


class VoteAPIView(RetrieveUpdateDestroyAPIView):

    serializer_class = VoteSerializer
    queryset = Poll.objects.all()

    def destroy(self, request, pk):
        poll = Poll.objects.get(pk=pk)
        if poll.type_vote == 'u':
            try:
                vote = UniqueVote.objects.get(choice=request.data['choice'], user=request.user)
                self.permform_destroy(vote)
                return Response(status=200)
            except ObjectDoesNotExist:
                return Response(status=404)
        elif poll.type_vote == 'm':
            try:
                vote = MultipleVote.objects.get(choice=request.data['choice'], user=request.user)
                self.permform_destroy(vote)
                return Response(status=200)
            except ObjectDoesNotExist:
                return Response(status=404)

    def permform_destroy(self, instance):
        instance.delete()
