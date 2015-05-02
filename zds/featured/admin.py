# coding: utf-8

from django.contrib import admin

from zds.featured.models import ResourceFeatured, MessageFeatured

admin.site.register(ResourceFeatured)
admin.site.register(MessageFeatured)
