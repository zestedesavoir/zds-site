# coding: utf-8

from django.contrib import admin

from .models import PrivatePost, PrivateTopic, PrivateTopicRead


admin.site.register(PrivatePost)
admin.site.register(PrivateTopic)
admin.site.register(PrivateTopicRead)
