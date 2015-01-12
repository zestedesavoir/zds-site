# -*- coding: utf-8 -*-

from django.conf import settings

from rest_framework import status
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from zds.member.api.serializers import ProfileSanctionSerializer
from zds.member.models import Profile


class CreateDestroyMemberSanctionAPIView(CreateAPIView, DestroyAPIView):
    """
    Generic view used by the API about sanctions.
    """

    queryset = Profile.objects.all()
    serializer_class = ProfileSanctionSerializer
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        state = self.get_state_instance(request)

        try:
            ban = state.get_sanction(request.user, instance.user)
        except ValueError:
            return Response({u'detail': u'Sanction could not be applied with received data.'},
                            status=status.HTTP_400_BAD_REQUEST)

        state.apply_sanction(instance, ban)
        msg = state.get_message_sanction() \
            .format(ban.user,
                    ban.moderator,
                    ban.type,
                    state.get_detail(),
                    ban.text,
                    settings.ZDS_APP['site']['litteral_name'])

        state.notify_member(ban, msg)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        state = self.get_state_instance(request)

        try:
            ban = state.get_sanction(request.user, instance.user)
        except ValueError:
            return Response({u'detail': u'Sanction could not be applied with received data.'},
                            status=status.HTTP_400_BAD_REQUEST)

        state.apply_sanction(instance, ban)
        msg = state.get_message_sanction() \
            .format(ban.user,
                    ban.moderator,
                    ban.type,
                    state.get_detail(),
                    ban.text,
                    settings.ZDS_APP['site']['litteral_name'])
        state.notify_member(ban, msg)
        return Response(serializer.data)

    def get_state_instance(self, request):
        raise NotImplementedError('`get_state_instance()` must be implemented.')
