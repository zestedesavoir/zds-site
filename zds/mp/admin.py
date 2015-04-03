# coding: utf-8

from django.contrib import admin

from .models import PrivatePost, PrivateTopic, PrivateTopicRead


class PrivatePostAdmin(admin.ModelAdmin):

    """Representation of PrivatePost model in the admin interface."""

    list_display = ('privatetopic', 'author', 'pubdate', 'update', 'position_in_topic')


class PrivateTopicAdmin(admin.ModelAdmin):

    """Representation of PrivateTopic model in the admin interface."""

    list_display = ('title', 'subtitle', 'author', 'last_message', 'pubdate')


class PrivateTopicReadAdmin(admin.ModelAdmin):

    """Representation of PrivateTopicRead model in the admin interface."""

    list_display = ('privatetopic', 'privatepost', 'user')


admin.site.register(PrivatePost, PrivatePostAdmin)
admin.site.register(PrivateTopic, PrivateTopicAdmin)
admin.site.register(PrivateTopicRead, PrivateTopicReadAdmin)
