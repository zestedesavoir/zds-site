# coding: utf-8

from django.contrib import admin

from .models import PublishableContent, Container, Extract, Validation, ContentReaction


admin.site.register(PublishableContent)
admin.site.register(Container)
admin.site.register(Extract)
admin.site.register(Validation)
admin.site.register(ContentReaction)
