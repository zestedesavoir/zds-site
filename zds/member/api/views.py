# -*- coding: utf-8 -*-

from rest_framework.generics import ListAPIView

from zds.member.api.serializers import UserSerializer
from zds.member.models import Profile


class MemberListAPI(ListAPIView):
    """Displays the list of registered users."""

    queryset = Profile.objects.all_members_ordered_by_date_joined()
    serializer_class = UserSerializer
