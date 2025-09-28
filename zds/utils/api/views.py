import datetime

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView, UpdateAPIView
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.api.bits import DJRF3xPaginationKeyBit, UpdatedAtKeyBit
from zds.utils.api.permissions import UpdatePotentialSpamPermission
from zds.utils.api.serializers import KarmaSerializer, PotentialSpamSerializer, TagSerializer
from zds.utils.models import Comment, Tag


class KarmaView(RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = KarmaSerializer


class UpdateCommentPotentialSpam(UpdateAPIView):
    queryset = Comment.objects.all()
    serializer_class = PotentialSpamSerializer
    permission_classes = [UpdatePotentialSpamPermission]


class PagingSearchListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    search = bits.QueryParamsKeyBit(["search"])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    updated_at = UpdatedAtKeyBit("api_updated_tag")


def change_api_tag_updated_at(sender=None, instance=None, *args, **kwargs):
    cache.set("api_updated_tag", datetime.datetime.utcnow())


post_save.connect(receiver=change_api_tag_updated_at, sender=Tag)
post_delete.connect(receiver=change_api_tag_updated_at, sender=Tag)


class TagListAPI(ListAPIView):
    """
    Profile resource to list
    """

    queryset = Tag.objects.all()
    list_key_func = PagingSearchListKeyConstructor()
    serializer_class = TagSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ("title",)

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
