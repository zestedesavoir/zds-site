# coding: utf-8
from dry_rest_permissions.generics import DRYPermissions
from rest_framework import filters
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.api.DJRF3xPaginationKeyBit import DJRF3xPaginationKeyBit
from zds.notification.api.serializers import NotificationSerializer
from zds.notification.models import Notification


class PagingNotificationListKeyConstructor(DefaultKeyConstructor):
    pagination = DJRF3xPaginationKeyBit()
    search = bits.QueryParamsKeyBit(['search', 'ordering', 'type'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()


class NotificationListAPI(ListAPIView):
    """
    List of notification.
    """

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('pubdate', 'title',)
    list_key_func = PagingNotificationListKeyConstructor()
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated, DRYPermissions,)

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all notifications of a user.
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
              description: Sets the number of notifications per page.
              required: false
              paramType: query
            - name: search
              description: Filters by title.
              required: false
              paramType: query
            - name: ordering
              description: Sorts the results. You can order by (-)pubdate or (-)title.
              paramType: query
            - name: type
              description: Filter the type of the notification.
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

    def get_queryset(self):
        queryset = Notification.objects.get_unread_notifications_of(self.request.user)
        _type = self.request.query_params.get('type', None)
        if _type:
            queryset = queryset.filter(subscription__content_type__model=_type)
        return queryset
