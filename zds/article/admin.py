# coding: utf-8

from django.contrib import admin

from .models import Article, Validation, Reaction, ArticleRead


admin.site.register(Article)
admin.site.register(ArticleRead)
admin.site.register(Reaction)
admin.site.register(Validation)
