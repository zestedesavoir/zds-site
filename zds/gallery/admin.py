# coding: utf-8

from django.contrib import admin

from models import Gallery, Image, UserGallery


class GalleryAdmin(admin.ModelAdmin):

    """Representation of Gallery model in the admin interface."""

    list_display = ('title', 'subtitle', 'pubdate', 'update')


class ImageAdmin(admin.ModelAdmin):

    """Representation of Image model in the admin interface."""

    list_display = ('title', 'gallery', 'legend', 'pubdate', 'update')


class UserGalleryAdmin(admin.ModelAdmin):

    """Representation of UserGallery model in the admin interface."""

    list_display = ('user', 'gallery', 'mode')


admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(UserGallery, UserGalleryAdmin)
