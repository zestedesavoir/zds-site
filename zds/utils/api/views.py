# coding: utf-8

from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from zds.api.DJRF3xPaginationKeyBit import DJRF3xPaginationKeyBit
from zds.utils.models import Comment, Tag
from zds.utils.api.serializers import KarmaSerializer, TagSerializer


class KarmaView(RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = KarmaSerializer

class PagingSearchListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    search = bits.QueryParamsKeyBit(['search'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    
class TagListAPI(ListAPIView):
    """
    Profile resource to list
    """

    queryset = Tag.objects.all()
    list_key_func = PagingSearchListKeyConstructor()
    serializer_class = TagSerializer

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all tag in the system.
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of tag per page.
              required: false
              paramType: query
            - name: search
              description: Filters by tagname.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)
