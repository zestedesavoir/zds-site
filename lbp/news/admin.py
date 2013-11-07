from django.contrib import admin
from lbp.news.models import News, Comment, AlertNews
 
admin.site.register(News)
admin.site.register(Comment)
admin.site.register(AlertNews)