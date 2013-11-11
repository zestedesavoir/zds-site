# coding: utf-8

from django.contrib import admin
from .models import Tutorial, Part, Chapter, Extract

admin.site.register(Tutorial)
admin.site.register(Part)
admin.site.register(Chapter)
admin.site.register(Extract)
