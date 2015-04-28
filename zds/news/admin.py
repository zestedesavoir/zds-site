# coding: utf-8

from django.contrib import admin

from zds.news.models import News, MessageNews

admin.site.register(News)
admin.site.register(MessageNews)
