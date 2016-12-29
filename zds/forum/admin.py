# coding: utf-8

from django.contrib import admin

from zds.forum.models import Category, Forum, Post, Topic, TopicRead


class TopicAdmin(admin.ModelAdmin):
    fields = ('title', 'subtitle', 'is_solved', 'is_locked', 'is_sticky', 'forum', 'author',
              'last_message', 'tags', 'pubdate', 'update_index_date')
    raw_id_fields = ('forum', 'author', 'last_message', 'tags')
    readonly_fields = ('pubdate', 'update_index_date')


class TopicReadAdmin(admin.ModelAdmin):
    fields = ('topic', 'post', 'user')
    raw_id_fields = ('topic', 'post', 'user')


admin.site.register(Category)
admin.site.register(Forum)
admin.site.register(Post)
admin.site.register(Topic, TopicAdmin)
admin.site.register(TopicRead, TopicReadAdmin)
