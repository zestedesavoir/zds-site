# coding: utf-8

from django.contrib import admin

from .models import PublishableContent, Validation, ContentReaction


admin.site.register(PublishableContent)
admin.site.register(Validation)
admin.site.register(ContentReaction)
