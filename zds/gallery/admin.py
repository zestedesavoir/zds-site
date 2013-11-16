# coding: utf-8

from django.contrib import admin

from .models import Gallery, Image, UserGallery


admin.site.register(Gallery)
admin.site.register(Image)
admin.site.register(UserGallery)

