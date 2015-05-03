# coding: utf-8

from django.contrib import admin

from .models import Category, Forum, Topic, Post, TopicRead, TopicFollowed


admin.site.register(Category)
admin.site.register(Forum)
# TODO Topic admin is broken (load an admin Topic page implies to load ALL Members and Posts!)
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(TopicRead)
admin.site.register(TopicFollowed)
