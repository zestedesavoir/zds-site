# coding: utf-8

from dry_rest_permissions.generics import DRYPermissions
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
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
    #tag = bits.TagKeyBit()
    
class TagListAPI(ListCreateAPIView):
    """
    Profile resource to list
    """

    queryset = Tag.objects.all()
    list_key_func = PagingSearchListKeyConstructor()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all tah in the system.
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

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TagSerializer

    def get_permissions(self):
        permission_classes = [AllowAny, ]
        if self.request.method == 'GET' : 
            permission_classes.append(DRYPermissions)
        return [permission() for permission in permission_classes]

