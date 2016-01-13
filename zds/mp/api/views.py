# -*- coding: utf-8 -*-
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import status, exceptions, filters
from rest_framework.generics import RetrieveUpdateDestroyAPIView, DestroyAPIView, ListCreateAPIView, \
    get_object_or_404, RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from zds.api.DJRF3xPaginationKeyBit import DJRF3xPaginationKeyBit

from zds.mp.api.permissions import IsParticipant, IsParticipantFromPrivatePost, IsLastPrivatePostOfCurrentUser, \
    IsAloneInPrivatePost, IsAuthor
from zds.mp.api.serializers import PrivateTopicSerializer, PrivateTopicUpdateSerializer, PrivateTopicCreateSerializer, \
    PrivatePostSerializer, PrivatePostUpdateSerializer, PrivatePostCreateSerializer
from zds.mp.commons import LeavePrivateTopic, MarkPrivateTopicAsRead
from zds.mp.models import PrivateTopic, PrivatePost
from zds.utils.templatetags.interventions import interventions_privatetopics


class PagingPrivateTopicListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    search = bits.QueryParamsKeyBit(['search', 'ordering'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class PagingPrivateTopicUnreadListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class DetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class PagingPrivatePostListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    search = bits.QueryParamsKeyBit(['ordering'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class PrivateTopicListAPI(LeavePrivateTopic, ListCreateAPIView, DestroyAPIView):
    """
    Private topic resource to list of a member.
    """

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('pubdate', 'last_message', 'title')
    list_key_func = PagingPrivateTopicListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all private topics of the member authenticated.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: page
              description: Displays users of the page given.
              required: false
              paramType: query
            - name: page_size
              description: Sets size of the pagination.
              required: false
              paramType: query
            - name: search
              description: Makes a search on the username.
              required: false
              paramType: query
            - name: ordering
              description: Applies an order at the list. You can order by (-)pubdate, (-)last_message or (-)title.
              paramType: query
            - name: expand
              description: Expand a field with an identifier.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 404
              message: Not found
        """
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Create a new private topic for the member authenticated.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: title
              description: New title of the MP.
              required: true
              paramType: form
            - name: subtitle
              description: New subtitle of the MP.
              required: false
              paramType: form
            - name: participants
              description: If you would like to add a participant, you must specify its user identifier and if you
                            would like to add more than one participant, you must specify this parameter several times.
              required: true
              paramType: form
            - name: text
              description: Text of the first message of the private topic.
              required: true
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not authenticated
        """
        return self.create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Deletes a list of private topic of the member authenticated.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: pk
              description: if you would like to remove more than one private topic,
                            you must specify this parameter several times.
              required: true
              paramType: form
        responseMessages:
            - code: 401
              message: Not authenticated
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
        if self.request.method == 'GET':
            return PrivateTopicSerializer
        elif self.request.method == 'POST':
            return PrivateTopicCreateSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, ]
        if self.request.method == 'GET' or self.request.method == 'POST':
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.request.method == 'DELETE':
            list = self.request.data.getlist('pk')
            return PrivateTopic.objects.get_private_topics_selected(self.request.user.id, list)
        return PrivateTopic.objects.get_private_topics_of_user(self.request.user.id)


class PrivateTopicDetailAPI(LeavePrivateTopic, RetrieveUpdateDestroyAPIView):
    """
    Private topic resource to display details of a private topic.
    """

    queryset = PrivateTopic.objects.all()
    obj_key_func = DetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a private topic given by its identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: expand
              description: Expand a field with an identifier.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 403
              message: Not permissions
            - code: 404
              message: Not found
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates a MP given by its identifier of the current user authenticated.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: title
              description: New title of the MP.
              required: false
              paramType: form
            - name: subtitle
              description: New subtitle of the MP.
              required: false
              paramType: form
            - name: participants
              description: If you would like to add a participant, you must specify its user identifier and if you
                            would like to add more than one participant, you must specify this parameter several times.
              required: false
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not authenticated
            - code: 403
              message: Not permissions
            - code: 404
              message: Not found
        """
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """
        Leaves a MP given by its identifier of the current user authenticated.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 403
              message: Not permissions
            - code: 404
              message: Not found
        """
        return self.destroy(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PrivateTopicSerializer
        elif self.request.method == 'PUT':
            return PrivateTopicUpdateSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsParticipant, ]
        if self.request.method == 'GET':
            permission_classes.append(DRYPermissions)
        elif self.request.method == 'PUT':
            permission_classes.append(DRYPermissions)
            permission_classes.remove(IsParticipant)
            permission_classes.append(IsAuthor)
        return [permission() for permission in permission_classes]


class PrivatePostListAPI(MarkPrivateTopicAsRead, ListCreateAPIView):
    """
    Private post resource to list of a member.
    """

    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('position_in_topic', 'pubdate', 'update')
    list_key_func = PagingPrivatePostListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all private posts of a private topic given of the member authenticated.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: X-Data-Format
              description: Specify "Html" or "Markdown" for the desired resource, "Markdown is the default value.
              required: false
              paramType: header
            - name: page
              description: Displays users of the page given.
              required: false
              paramType: query
            - name: page_size
              description: Sets size of the pagination.
              required: false
              paramType: query
            - name: ordering
              description: Applies an order at the list. You can order by (-)position_in_topic, (-)pubdate or (-)update.
              paramType: query
            - name: expand
              description: Expand a field with an identifier.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 404
              message: Not found
        """
        response = self.list(request, *args, **kwargs)
        self.perform_list(get_object_or_404(PrivateTopic, pk=(self.kwargs.get('pk_ptopic'))), self.request.user)
        return response

    def post(self, request, *args, **kwargs):
        """
        Create a new post in a Topic.
        ---
        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: text
              description: Text of the first message of the private topic.
              required: true
              paramType: form
        responseMessages:
            - code: 400
              message: Bad Request
            - code: 401
              message: Not authenticated
            - code: 403
              message: Not permissions
            - code: 404
              message: Not found
        """
        return self.create(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PrivatePostSerializer
        elif self.request.method == 'POST':
            return PrivatePostCreateSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsParticipantFromPrivatePost, ]
        if self.request.method == 'GET':
            permission_classes.append(DRYPermissions)
        elif self.request.method == 'POST':
            permission_classes.append(IsAloneInPrivatePost)
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return PrivatePost.objects.get_message_of_a_private_topic(self.kwargs.get('pk_ptopic'))


class PrivatePostDetailAPI(RetrieveUpdateAPIView):
    """
    Private post resource to display details of a private post.
    """

    queryset = PrivatePost.objects.all()
    obj_key_func = DetailKeyConstructor()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets a private post given by its identifier.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: X-Data-Format
              description: Specify "Html" or "Markdown" for the desired resource, "Markdown is the default value.
              required: false
              paramType: header
            - name: expand
              description: Expand a field with an identifier.
              required: false
              paramType: query
        responseMessages:
            - code: 400
              message: Bad Request if you specify bad identifiers
            - code: 401
              message: Not authenticated
            - code: 403
              message: Not permissions
            - code: 404
              message: Not found
        """
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Updates the last private post of a MP given by its identifier of the current user authenticated.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
        responseMessages:
            - code: 400
              message: Bad Request if you specify bad identifiers
            - code: 401
              message: Not authenticated
            - code: 403
              message: Not permissions
            - code: 404
              message: Not found
        """
        return self.update(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PrivatePostSerializer
        elif self.request.method == 'PUT':
            return PrivatePostUpdateSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsParticipantFromPrivatePost, ]
        if self.request.method == 'GET':
            permission_classes.append(DRYPermissions)
        elif self.request.method == 'PUT':
            permission_classes.append(DRYPermissions)
            permission_classes.append(IsLastPrivatePostOfCurrentUser)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return super(PrivatePostDetailAPI, self).get_queryset().filter(privatetopic__pk=self.kwargs['pk_ptopic'])


class PrivateTopicReadAPI(ListAPIView):
    """
    Private topic unread resource to list of the member authenticated.
    """

    serializer_class = PrivateTopicSerializer
    list_key_func = PagingPrivateTopicUnreadListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Displays all private topics unread.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make a authenticated request.
              required: true
              paramType: header
            - name: page
              description: Displays users of the page given.
              required: false
              paramType: query
            - name: page_size
              description: Sets size of the pagination.
              required: false
              paramType: query
            - name: expand
              description: Expand a field with an identifier.
              required: false
              paramType: query
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 404
              message: Not found
        """
        return self.list(request, *args, **kwargs)

    def get_current_user(self):
        return self.request.user

    def get_permissions(self):
        permission_classes = [IsAuthenticated, ]
        if self.request.method == 'GET':
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return interventions_privatetopics(user=self.get_current_user())['unread']
