# -*- coding: utf-8 -*-

from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from zds.member.api.serializers import UserSerializer, ProfileSerializer, \
    ProfileUpdateSerializer
from zds.member.models import Profile
from .permissions import IsOwnerOrReadOnly


class MemberListAPI(ListAPIView):
    """Displays the list of registered users."""

    queryset = Profile.objects.all_members_ordered_by_date_joined()
    serializer_class = UserSerializer


class MemberDetailAPI(RetrieveUpdateAPIView):
    """Displays or updates details of a member."""

    queryset = Profile.objects.all()

    def get(self, request, *args, **kwargs):
        self.serializer_class = ProfileSerializer
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        self.serializer_class = ProfileUpdateSerializer
        self.permissions = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
        return self.update(request, *args, **kwargs)
