import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.http import QueryDict
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import exceptions, filters, status
from rest_framework.generics import (
    DestroyAPIView,
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.api.bits import DJRF3xPaginationKeyBit, UpdatedAtKeyBit
from zds.api.key_constructor import DetailKeyConstructor, PagingListKeyConstructor
from zds.mp.api.permissions import (
    IsAuthor,
    IsLastPrivatePostOfCurrentUser,
    IsNotAloneInPrivatePost,
    IsParticipant,
    IsParticipantFromPrivatePost,
)
from zds.mp.api.serializers import (
    PrivatePostActionSerializer,
    PrivatePostKarmaSerializer,
    PrivatePostSerializer,
    PrivateTopicCreateSerializer,
    PrivateTopicSerializer,
    PrivateTopicUpdateSerializer,
)
from zds.mp.commons import LeavePrivateTopic
from zds.mp.models import PrivatePost, PrivateTopic, mark_read
from zds.notification.models import Notification


class PagingPrivateTopicListKeyConstructor(PagingListKeyConstructor):
    search = bits.QueryParamsKeyBit(["search", "ordering"])
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_topic")


class PagingPrivatePostListKeyConstructor(PagingListKeyConstructor):
    search = bits.QueryParamsKeyBit(["ordering"])
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_post")


class PagingNotificationListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_notification")


class PrivateTopicDetailKeyConstructor(DetailKeyConstructor):
    updated_at = UpdatedAtKeyBit("api_updated_topic")


class PrivatePostDetailKeyConstructor(DetailKeyConstructor):
    updated_at = UpdatedAtKeyBit("api_updated_post")


def change_api_private_topic_updated_at(sender=None, instance=None, *args, **kwargs):
    cache.set("api_updated_topic", datetime.datetime.utcnow())


def change_api_private_post_updated_at(sender=None, instance=None, *args, **kwargs):
    cache.set("api_updated_post", datetime.datetime.utcnow())


def change_api_notification_updated_at(sender=None, instance=None, *args, **kwargs):
    cache.set("api_updated_notification", datetime.datetime.utcnow())


for model, func in [
    (PrivateTopic, change_api_private_topic_updated_at),
    (PrivatePost, change_api_private_post_updated_at),
    (Notification, change_api_notification_updated_at),
]:
    post_save.connect(receiver=func, sender=model)
    post_delete.connect(receiver=func, sender=model)


class PrivateTopicListAPI(LeavePrivateTopic, ListCreateAPIView, DestroyAPIView):
    """
    Private topic resource to list of a member.
    """

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("title",)
    ordering_fields = ("pubdate", "last_message", "title")
    list_key_func = PagingPrivateTopicListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists an authenticated member's private topics.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of private topics per page.
              required: false
              paramType: query
            - name: search
              description: Filters by username.
              required: false
              paramType: query
            - name: ordering
              description: Sorts the results. You can order by (-)pubdate, (-)last_message or (-)title.
              paramType: query
            - name: expand
              description: Returns an object instead of an identifier representing the given field.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Creates a new private topic owned by the authenticated member.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: Private topic title.
              required: true
              paramType: form
            - name: subtitle
              description: Private topic subtitle.
              required: false
              paramType: form
            - name: participants
              description: To add a participant, specify its user identifier. Specify this parameter
                           several times to add several participants.
              required: true
              paramType: form
            - name: text
              description: First message text.
              required: true
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
        """
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Deletes a private topic to which the authenticated member participates.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: pk
              description: To remove several private topics, specify this parameter several times.
              required: true
              paramType: form
        responseMessages:
            - code: 401
              message: Not Authenticated
        """
        topics = self.get_queryset()
        if topics.count() == 0:
            raise exceptions.PermissionDenied()
        for topic in topics:
            self.perform_destroy(topic)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PrivateTopicSerializer
        elif self.request.method == "POST":
            return PrivateTopicCreateSerializer

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
        ]
        if self.request.method == "GET" or self.request.method == "POST":
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.request.method == "DELETE":
            qdict = QueryDict("", mutable=True)
            qdict.update(self.request.data)
            list_ = qdict.getlist("pk")
            return PrivateTopic.objects.get_private_topics_selected(self.request.user.id, list_)
        return PrivateTopic.objects.get_private_topics_of_user(self.request.user.id)


class PrivateTopicDetailAPI(LeavePrivateTopic, RetrieveUpdateDestroyAPIView):
    """
    Private topic resource for private topic details.
    """

    queryset = PrivateTopic.objects.all()
    obj_key_func = PrivateTopicDetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a private topic by identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: expand
              description: Returns an object instead of an identifier representing the given field.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates a private topic by id. Said private topic must be owned by the authenticated
        user.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: title
              description: New private topic title.
              required: false
              paramType: form
            - name: subtitle
              description: New private topic subtitle.
              required: false
              paramType: form
            - name: participants
              description: To add a participant, specify its user identifier. Specify this parameter
                           several times to add several participants.
              required: false
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Deletes a private topic by identifier from authenticated user's inbox.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.destroy(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PrivateTopicSerializer
        elif self.request.method == "PUT":
            return PrivateTopicUpdateSerializer
        else:  # used only for API documentation
            return PrivateTopicSerializer

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsParticipant,
        ]
        if self.request.method == "GET":
            permission_classes.append(DRYPermissions)
        elif self.request.method == "PUT":
            permission_classes.append(DRYPermissions)
            permission_classes.remove(IsParticipant)
            permission_classes.append(IsAuthor)
        return [permission() for permission in permission_classes]


class PrivatePostListAPI(ListCreateAPIView):
    """
    Private post resource for an authenticated member.
    """

    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ("position_in_topic", "pubdate", "update")
    list_key_func = PagingPrivatePostListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all private posts of a given private topic for an authenticated member.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: X-Data-Format
              description: Specify "Html" or "Markdown" for the desired resource. Defaults to "Markdown".
              required: false
              paramType: header
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of private posts per page.
              required: false
              paramType: query
            - name: ordering
              description: Sorts the results. You can order by (-)position_in_topic, (-)pubdate or (-)update.
              paramType: query
            - name: expand
              description: Returns an object instead of an identifier representing the given field.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 404
              message: Not Found
        """
        response = self.list(request, *args, **kwargs)
        topic = get_object_or_404(PrivateTopic, pk=self.kwargs.get("pk_ptopic"))
        mark_read(topic, self.request.user)
        return response

    def post(self, request, *args, **kwargs):
        """
        Create a new post in a Topic.
        ---
        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: text
              description: Message text.
              required: true
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.create(request, *args, **kwargs)

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsParticipantFromPrivatePost,
            DRYPermissions,
        ]
        if self.request.method == "POST":
            permission_classes.append(IsNotAloneInPrivatePost)
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PrivatePostSerializer
        elif self.request.method == "POST":
            return PrivatePostActionSerializer

    def get_queryset(self):
        return PrivatePost.objects.get_message_of_a_private_topic(self.kwargs.get("pk_ptopic"))


class PrivatePostDetailAPI(RetrieveUpdateAPIView):
    """
    Private post resource for a given private post details.
    """

    queryset = PrivatePost.objects.all()
    obj_key_func = PrivatePostDetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a private post given by its identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: X-Data-Format
              description: Specify "Html" or "Markdown" for the desired resource, "Markdown is the default value.
              required: false
              paramType: header
            - name: expand
              description: Returns an object instead of an identifier representing the given field.
              required: false
              paramType: query
        responseMessages:
            - code: 400
              message: Bad Request if you specify bad identifiers
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates the last private post of a given private topic. Said post must be owned by the
        authenticated member.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 400
              message: Bad Request if you specify a bad identifier
            - code: 401
              message: Not Authenticated
            - code: 403
              message: Permission Denied
            - code: 404
              message: Not Found
        """
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return PrivatePostSerializer
        elif self.request.method == "PUT":
            return PrivatePostActionSerializer
        else:  # used only for API documentation
            return PrivatePostSerializer

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsParticipantFromPrivatePost,
        ]
        if self.request.method == "GET":
            permission_classes.append(DRYPermissions)
        elif self.request.method == "PUT":
            permission_classes.append(DRYPermissions)
            permission_classes.append(IsLastPrivatePostOfCurrentUser)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return super().get_queryset().filter(privatetopic__pk=self.kwargs.get("pk_ptopic"))


class PrivateTopicReadAPI(ListAPIView):
    """
    Unread private topic resource for an authenticated member.
    """

    serializer_class = PrivateTopicSerializer
    list_key_func = PagingNotificationListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Displays all unread private topics for an authenticated member.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: true
              paramType: header
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of unread private topics per page.
              required: false
              paramType: query
            - name: expand
              description: Returns an object instead of an identifier representing the given field.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not Authenticated
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
        ]
        if self.request.method == "GET":
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        notifications = Notification.objects.get_unread_notifications_of(self.get_current_user()).filter(
            subscription__content_type=ContentType.objects.get_for_model(PrivateTopic)
        )
        return [notification.content_object.privatetopic for notification in notifications]


class PrivatePostReactionKarmaView(RetrieveUpdateDestroyAPIView):
    queryset = PrivatePost.objects.all()
    serializer_class = PrivatePostKarmaSerializer
    permission_classes = (IsAuthenticated, IsParticipantFromPrivatePost, DRYPermissions)
