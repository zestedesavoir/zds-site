from django.conf import settings
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import status
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from zds.member.api.permissions import IsStaffUser
from zds.member.api.serializers import ProfileSanctionSerializer
from zds.member.models import Profile


class CreateDestroyMemberSanctionAPIView(CreateAPIView, DestroyAPIView):
    """
    Generic view used by the API about sanctions.
    """

    queryset = Profile.objects.all()
    serializer_class = ProfileSanctionSerializer

    def post(self, request, *args, **kwargs):
        return self.process_request(request)

    def delete(self, request, *args, **kwargs):
        return self.process_request(request)

    def process_request(self, request):
        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        state = self.get_state_instance(request)

        ban = state.get_sanction(request.user, instance.user)

        if ban.user == ban.moderator:
            return Response({"detail": "Sanction can not be applied to yourself."}, status=status.HTTP_403_FORBIDDEN)

        try:
            state.apply_sanction(instance, ban)
        except ValueError:
            return Response(
                {"detail": "Sanction could not be applied with received data."}, status=status.HTTP_400_BAD_REQUEST
            )
        msg = state.get_message_sanction().format(
            ban.user, ban.moderator, ban.type, state.get_detail(), ban.note, settings.ZDS_APP["site"]["literal_name"]
        )
        state.notify_member(ban, msg)
        return Response(serializer.data)

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsStaffUser,
        ]
        if self.request.method == "POST" or self.request.method == "DELETE":
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]

    def get_state_instance(self, request):
        raise NotImplementedError("`get_state_instance()` must be implemented.")
