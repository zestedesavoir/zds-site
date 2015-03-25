# -*- coding: utf-8 -*-

from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from zds.mp.api.permissions import IsParticipant

from zds.mp.api.serializers import PrivateTopicSerializer
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


class PrivateTopicDetailAPI(RetrieveAPIView):
    """
    Private topic resource to display details of a private topic.
    """

    permission_classes = (IsAuthenticated, IsParticipant)
    queryset = PrivateTopic.objects.all()
    serializer_class = PrivateTopicSerializer
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
            - code: 404
              message: Not found
        """
        return self.retrieve(request, *args, **kwargs)
