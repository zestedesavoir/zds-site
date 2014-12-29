# -*- coding: utf-8 -*-

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from zds.member.api.serializers import UserSerializer, UserCreateSerializer, \
    ProfileSerializer, ProfileValidatorSerializer
from zds.member.models import Profile
from .permissions import IsOwnerOrReadOnly


class MemberListAPI(ListCreateAPIView):
    """
    Displays the list of registered users or create one.
    """

    queryset = Profile.objects.all_members_ordered_by_date_joined()

    def get(self, request, *args, **kwargs):
        self.serializer_class = UserSerializer
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.serializer_class = UserCreateSerializer
        return self.create(request, *args, **kwargs)



class MemberDetailAPI(RetrieveUpdateAPIView):
    """
    Displays or updates details of a member.
    """

    queryset = Profile.objects.all()

    def get(self, request, *args, **kwargs):
        self.serializer_class = ProfileSerializer
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        self.serializer_class = ProfileValidatorSerializer
        self.permissions = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
        return self.update(request, *args, **kwargs)
