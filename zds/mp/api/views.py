# -*- coding: utf-8 -*-

from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.mp.api.permissions import IsParticipant
from zds.mp.api.serializers import PrivateTopicSerializer, PrivateTopicUpdateSerializer
from zds.mp.commons import LeavePrivateTopic
from zds.mp.models import PrivateTopic


class PagingPrivateTopicListKeyConstructor(DefaultKeyConstructor):
    pagination = bits.PaginationKeyBit()
    search = bits.QueryParamsKeyBit(['search', 'ordering'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class DetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


class PrivateTopicListAPI(ListAPIView):
    """
    Private topic resource to list of a member.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = PrivateTopicSerializer
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
        responseMessages:
            - code: 401
              message: Not authenticated
            - code: 404
              message: Not found
        """
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        return PrivateTopic.objects.get_private_topics_of_user(self.request.user.id)


class PrivateTopicDetailAPI(LeavePrivateTopic, RetrieveUpdateDestroyAPIView):
    """
    Private topic resource to display details of a private topic.
    """

    permission_classes = (IsAuthenticated, IsParticipant)
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
