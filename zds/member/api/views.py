# -*- coding: utf-8 -*-

from rest_framework.generics import ListAPIView, RetrieveAPIView

from zds.member.api.serializers import UserSerializer, ProfileSerializer
from zds.member.models import Profile


class MemberListAPI(ListAPIView):
    """Displays the list of registered users."""

    queryset = Profile.objects.all_members_ordered_by_date_joined()
    serializer_class = UserSerializer


class MemberDetailAPI(RetrieveAPIView):
    """Displays details of a member."""

    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
