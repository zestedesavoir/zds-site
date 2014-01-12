# coding: utf-8

from django.contrib import admin

from .models import Tutorial, Part, Chapter, Extract, Validation, Note


admin.site.register(Tutorial)
admin.site.register(Part)
admin.site.register(Chapter)
admin.site.register(Extract)
admin.site.register(Validation)
admin.site.register(Note)
