# -*- coding: utf-8 -*-

from rest_framework import status, exceptions, filters
from django.http import Http404
from rest_framework.generics import RetrieveAPIView, DestroyAPIView, ListCreateAPIView, \
    get_object_or_404, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.etag.decorators import etag
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import DefaultKeyConstructor

from zds.stats.models import Log, Source, Device , OS, Browser, City, Country
from zds.tutorial.models import Tutorial, Chapter, Part
from zds.article.models import Article
from zds.stats.api.serializers import StatTutorialSerializer, StatPartSerializer, StatChapterSerializer, StatArticleSerializer, StatSourceContentSerializer, StatDeviceContentSerializer, StatBrowserContentSerializer, StatCountryContentSerializer, StatCityContentSerializer, StatOSContentSerializer

class PagingStatContentListKeyConstructor(DefaultKeyConstructor):
    pagination = bits.PaginationKeyBit()
    search = bits.QueryParamsKeyBit(['search', 'ordering'])
    list_sql_query = bits.ListSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()

class DetailKeyConstructor(DefaultKeyConstructor):
    format = bits.FormatKeyBit()
    language = bits.LanguageKeyBit()
    retrieve_sql_query = bits.RetrieveSqlQueryKeyBit()
    unique_view_id = bits.UniqueViewIdKeyBit()


def get_content_serialiser(content_type):
    if content_type == 'tutoriel':
        return StatTutorialSerializer
    elif content_type == 'partie':
        return StatPartSerializer
    elif content_type == 'chapitre':
        return StatChapterSerializer
    elif content_type == 'article':
        return StatArticleSerializer
    else:
        raise exceptions.NotFound()


class StatContentListAPI(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return get_content_serialiser(self.kwargs.get("content_type"))

    def get_queryset(self):
        if self.kwargs.get("content_type") == 'tutoriel':
            return Tutorial.objects.all().filter(sha_public__isnull=False)
        elif self.kwargs.get("content_type") == 'partie':
            return Part.objects.all().filter(tutorial__sha_public__isnull=False)
        elif self.kwargs.get("content_type") == 'chapitre':
            return Chapter.objects.all().filter(part__tutorial__sha_public__isnull=False)
        elif self.kwargs.get("content_type") == 'article':
            return Article.objects.all().filter(sha_public__isnull=False)
        else:
            raise exceptions.NotFound()

class StatContentDetailAPI(RetrieveAPIView):
    obj_key_func = DetailKeyConstructor()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return get_content_serialiser(self.kwargs.get("content_type"))

    def get_object(self):

        if self.kwargs.get("content_type") == 'tutoriel':
            return Tutorial.objects.all().filter(id=self.kwargs.get("content_id"), sha_public__isnull=False).first()
        elif self.kwargs.get("content_type") == 'partie':
            return Part.objects.all().filter(id=self.kwargs.get("content_id"), tutorial__sha_public__isnull=False).first()
        elif self.kwargs.get("content_type") == 'chapitre':
            return Chapter.objects.all().filter(id=self.kwargs.get("content_id"), part__tutorial__sha_public__isnull=False).first()
        elif self.kwargs.get("content_type") == 'article':
            return Article.objects.all().filter(id=self.kwargs.get("content_id"), sha_public__isnull=False).first()
        else:
            raise exceptions.NotFound()

def get_app_from_content_type(content_type):
    if content_type=="tutoriel":
        return "tutorial"
    elif content_type=="article":
        return "article"
    elif content_type=="chapitre":
        return "chapter"
    elif content_type=="partie":
        return "part"
    else:
        return None

class StatSourceContentListAPI(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StatSourceContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get("content_type")
        app_name = get_app_from_content_type(content_type)
        app_id = self.kwargs.get("content_id")

        if app_name is not None and app_id is not None:
            type_logs = Log.objects.filter(content_type=app_name, id_zds=app_id).values_list('dns_referal', flat=True)
            return Source.objects.all().filter(code__in=type_logs)

        if app_name is not None:
            type_logs = Log.objects.filter(content_type=app_name).values_list('dns_referal', flat=True)
            return Source.objects.all().filter(code__in=type_logs)

        raise exceptions.NotFound()

class StatDeviceContentListAPI(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StatDeviceContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get("content_type")
        app_name = get_app_from_content_type(content_type)
        app_id = self.kwargs.get("content_id")

        if app_name is not None and app_id is not None:
            type_logs = Log.objects.filter(content_type=app_name, id_zds=app_id).values_list('device_family', flat=True).distinct()
            return Device.objects.all().filter(code__in=type_logs)

        if app_name is not None:
            type_logs = Log.objects.filter(content_type=app_name).values_list('device_family', flat=True).distinct()
            return Device.objects.all().filter(code__in=type_logs)

        raise exceptions.NotFound()

class StatBrowserContentListAPI(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StatBrowserContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get("content_type")
        app_name = get_app_from_content_type(content_type)
        app_id = self.kwargs.get("content_id")

        if app_name is not None and app_id is not None:
            type_logs = Log.objects.filter(content_type=app_name, id_zds=app_id).values_list('browser_family', flat=True).distinct()
            return Browser.objects.all().filter(code__in=type_logs)

        if app_name is not None:
            type_logs = Log.objects.filter(content_type=app_name).values_list('browser_family', flat=True).distinct()
            return Browser.objects.all().filter(code__in=type_logs)

        raise exceptions.NotFound()

class StatCountryContentListAPI(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StatCountryContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get("content_type")
        app_name = get_app_from_content_type(content_type)
        app_id = self.kwargs.get("content_id")

        if app_name is not None and app_id is not None:
            type_logs = Log.objects.filter(content_type=app_name, id_zds=app_id).values_list('country', flat=True).distinct()
            return Country.objects.all().filter(code__in=type_logs)

        if app_name is not None:
            type_logs = Log.objects.filter(content_type=app_name).values_list('country', flat=True).distinct()
            return Country.objects.all().filter(code__in=type_logs)

        raise exceptions.NotFound()

class StatCityContentListAPI(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StatCityContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get("content_type")
        app_name = get_app_from_content_type(content_type)
        app_id = self.kwargs.get("content_id")

        if app_name is not None and app_id is not None:
            type_logs = Log.objects.filter(content_type=app_name, id_zds=app_id).values_list('city', flat=True).distinct()
            return City.objects.all().filter(code__in=type_logs)

        if app_name is not None:
            type_logs = Log.objects.filter(content_type=app_name).values_list('city', flat=True).distinct()
            return City.objects.all().filter(code__in=type_logs)

        raise exceptions.NotFound()

class StatOSContentListAPI(ListCreateAPIView):
    filter_backends = (filters.OrderingFilter, filters.OrderingFilter)
    list_key_func = PagingStatContentListKeyConstructor()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StatOSContentSerializer

    def get_queryset(self):
        content_type = self.kwargs.get("content_type")
        app_name = get_app_from_content_type(content_type)
        app_id = self.kwargs.get("content_id")

        if app_name is not None and app_id is not None:
            type_logs = Log.objects.filter(content_type=app_name, id_zds=app_id).values_list('os_family', flat=True).distinct()
            return OS.objects.all().filter(code__in=type_logs)

        if app_name is not None:
            type_logs = Log.objects.filter(content_type=app_name).values_list('os_family', flat=True).distinct()
            return OS.objects.all().filter(code__in=type_logs)

        raise exceptions.NotFound()