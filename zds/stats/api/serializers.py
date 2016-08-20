# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from zds.tutorialv2.models.models_database import PublishedContent
from zds.stats.models import Source, Device, OS, Browser, Country, City


class StatContentSerializer(serializers.ModelSerializer):
    """
    Serializer of a generic content statistic object.
    """

    class Meta:
        model = PublishedContent
        fields = ('id', 'title', 'slug', 'pubdate', 'update', 'total_visits', 'unique_visits', 'avg_load_speed', 'min_load_speed', 'max_load_speed', 'avg_size_page', 'min_size_page', 'max_size_page', 'description', 'sources', 'countrys', 'cities')

    slug = serializers.CharField(source='content_public_slug')
    pubdate = serializers.CharField(source='publication_date')
    update = serializers.CharField(source='update_date')
    total_visits = serializers.IntegerField(source='get_total_visits')
    unique_visits = serializers.IntegerField(source='get_unique_visits')
    avg_load_speed = serializers.IntegerField(source='get_avg_load_speed')
    min_load_speed = serializers.IntegerField(source='get_min_load_speed')
    max_load_speed = serializers.IntegerField(source='get_max_load_speed')
    avg_size_page = serializers.IntegerField(source='get_avg_size_page')
    min_size_page = serializers.IntegerField(source='get_min_size_page')
    max_size_page = serializers.IntegerField(source='get_max_size_page')
    sources = serializers.ListField(source='get_sources', child=serializers.DictField(child=serializers.CharField()))
    countrys = serializers.ListField(source='get_countrys', child=serializers.DictField(child=serializers.CharField()))
    cities = serializers.ListField(source='get_cities', child=serializers.DictField(child=serializers.CharField()))

class StatDimSerializer(serializers.ModelSerializer):
    """
    Serializer of a tutorial statistic object.
    """
    total_visits = serializers.IntegerField(source='get_total_visits')
    unique_visits = serializers.IntegerField(source='get_unique_visits')
    avg_load_speed = serializers.IntegerField(source='get_avg_load_speed')
    avg_size_page = serializers.IntegerField(source='get_avg_size_page')

    class Meta:
        fields = ('code', 'total_visits', 'unique_visits', 'avg_load_speed', 'avg_size_page')

class StatSourceContentSerializer(StatDimSerializer):
    """
    Serializer of a source statistic object.
    """
    class Meta:
        model = Source

class StatDeviceContentSerializer(StatDimSerializer):
    """
    Serializer of a devices statistic object.
    """
    class Meta:
        model = Device

class StatBrowserContentSerializer(StatDimSerializer):
    """
    Serializer of a browser statistic object.
    """
    class Meta:
        model = Browser

class StatCountryContentSerializer(StatDimSerializer):
    """
    Serializer of a countries statistic object.
    """
    class Meta:
        model = Country

class StatCityContentSerializer(StatDimSerializer):
    """
    Serializer of a cities statistic object.
    """
    class Meta:
        model = City

class StatOSContentSerializer(StatDimSerializer):
    """
    Serializer of a operating system statistic object.
    """
    class Meta:
        model = OS
