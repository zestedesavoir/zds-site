# -*- coding: utf-8 -*-

from rest_framework import exceptions, filters
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.stats.models import Log, Source, Device, OS, Browser, City, Country
from zds.stats.api.serializers import StatContentSerializer, StatSourceContentSerializer
from zds.tutorialv2.models.models_database import PublishedContent


class PagingStatContentListKeyConstructor(DefaultKeyConstructor):
    pagination = bits.PaginationKeyBit()
    search = bits.QueryParamsKeyBit(['search', 'ordering'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()


class DetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()
    user = bits.UserKeyBit()


class StatContentListAPI(ListAPIView):
    """
    Statistic resource to list all content stats.
    """
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()
    serializer_class = StatContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get('content_type')
        if content_type:
            attr_name = get_name_in_model_content_database(content_type)
            return PublishedContent.objects.all().filter(content_type=attr_name)
        else:
            return PublishedContent.objects.all()

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """
        Lists all content stats in the system.
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of contents stats per page.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)


class StatContentDetailAPI(RetrieveAPIView):
    """
    Statistic resource to content stats details.
    """
    obj_key_func = DetailKeyConstructor()
    serializer_class = StatContentSerializer

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StatContentSerializer

    def get_object(self):
        content_type = self.kwargs.get('content_type')
        attr_name = get_name_in_model_content_database(content_type)
        return PublishedContent.objects.all().filter(
            id=self.kwargs.get('content_id'),
            content_type=attr_name,
            sha_public__isnull=False).first()

    @etag(obj_key_func)
    @cache_response(key_func=obj_key_func)
    def get(self, request, *args, **kwargs):
        """
        Gets information for content stats.
        ---

        parameters:
            - name: Authorization
              description: Bearer token to make an authenticated request.
              required: false
              paramType: header
        responseMessages:
            - code: 401
              message: Not Authenticated
        """
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)


def get_app_from_content_type(content_type):
    """receives a literal content type and return his key as stored in the Log model

    :return: Log key associated with the content type
    """
    if content_type == 'tutoriel':
        return 'tutorial'
    elif content_type == 'article':
        return 'article'
    else:
        raise exceptions.NotFound()


def get_name_in_model_content_database(content_type):
    """receives a literal content type and return his key as stored in the PublishedContent model

    :return: PublishedContent key associated with the content type
    """
    if content_type == 'tutoriel':
        return 'TUTORIAL'
    elif content_type == 'article':
        return 'ARTICLE'
    else:
        raise exceptions.NotFound()


class StatSubListAPI(ListAPIView):
    map_attr = ''
    map_query_set = None
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()
    serializer_class = StatSourceContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get('content_type')
        app_name = get_app_from_content_type(content_type)
        app_id = self.kwargs.get('content_id')
        params = {"content_type": app_name, self.map_attr + "__isnull": False}

        if app_id:
            params["id_zds"] = app_id

        type_logs = Log.objects.filter(**params).values_list(self.map_attr, flat=True)
        return self.map_query_set.filter(code__in=type_logs)

    @etag(list_key_func)
    @cache_response(key_func=list_key_func)
    def get(self, request, *args, **kwargs):
        """"
        Lists all dimensions stats in the system.
        ---

        parameters:
            - name: page
              description: Restricts output to the given page number.
              required: false
              paramType: query
            - name: page_size
              description: Sets the number of dimension per page.
              required: false
              paramType: query
        responseMessages:
            - code: 404
              message: Not Found
        """
        return self.list(request, *args, **kwargs)


class StatSourceContentListAPI(StatSubListAPI):
    map_attr = 'dns_referal'
    map_query_set = Source.objects.all()


class StatDeviceContentListAPI(StatSubListAPI):
    map_attr = 'device_family'
    map_query_set = Device.objects.all()


class StatBrowserContentListAPI(StatSubListAPI):
    map_attr = 'browser_family'
    map_query_set = Browser.objects.all()


class StatCountryContentListAPI(StatSubListAPI):
    map_attr = 'country'
    map_query_set = Country.objects.all()


class StatCityContentListAPI(StatSubListAPI):
    map_attr = 'city'
    map_query_set = City.objects.all()


class StatOSContentListAPI(StatSubListAPI):
    map_attr = 'os_family'
    map_query_set = OS.objects.all()
