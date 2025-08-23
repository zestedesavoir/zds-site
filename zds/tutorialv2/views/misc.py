from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.views.generic import FormView

from zds import json_handler
from zds.featured.mixins import FeatureableMixin
from zds.member.decorator import LoggedWithReadWriteHability
from zds.notification.models import NewPublicationSubscription
from zds.tutorialv2.mixins import SingleOnlineContentViewMixin
from zds.utils.misc import is_ajax


class RequestFeaturedContent(LoggedWithReadWriteHability, FeatureableMixin, SingleOnlineContentViewMixin, FormView):
    redirection_is_needed = False

    def featured_request_allowed(self):
        """Featured request is not allowed on obsolete content and opinions"""
        return self.object.type != "OPINION" and not self.object.is_obsolete

    def post(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()

        response = dict()
        response["requesting"], response["newCount"] = self.toogle_featured_request(request.user)
        if is_ajax(self.request):
            return HttpResponse(json_handler.dumps(response), content_type="application/json")
        return redirect(self.public_content_object.get_absolute_url_online())


class FollowNewContent(LoggedWithReadWriteHability, FormView):
    @staticmethod
    def perform_follow(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user).is_active

    @staticmethod
    def perform_follow_by_email(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user, True).is_active

    def post(self, request, *args, **kwargs):
        response = {}

        # get user to follow
        try:
            user_to_follow = User.objects.get(pk=kwargs["pk"])
        except User.DoesNotExist:
            raise Http404

        # follow content if user != user_to_follow only
        if user_to_follow == request.user:
            raise PermissionDenied

        with transaction.atomic():
            if "follow" in request.POST:
                response["follow"] = self.perform_follow(user_to_follow, request.user)
                response["subscriberCount"] = NewPublicationSubscription.objects.get_subscriptions(
                    user_to_follow
                ).count()
            elif "email" in request.POST:
                response["email"] = self.perform_follow_by_email(user_to_follow, request.user)

        if is_ajax(self.request):
            return HttpResponse(json_handler.dumps(response), content_type="application/json")
        return redirect(request.META.get("HTTP_REFERER"))
