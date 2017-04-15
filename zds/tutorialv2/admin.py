# coding: utf-8

from django.contrib import admin

from zds.tutorialv2.models.models_database import PublishableContent, Validation, ContentReaction, PublishedContent


class PublishableContentnAdmin(admin.ModelAdmin):
    raw_id_fields = ('authors', 'tags', 'image', 'gallery', 'beta_topic', 'last_note', 'public_version')


class PublishedContentAdmin(admin.ModelAdmin):
    raw_id_fields = ('content', 'authors')


class ContentReactionAdmin(admin.ModelAdmin):
    raw_id_fields = ('author', 'editor')


class ValidationAdmin(admin.ModelAdmin):
    raw_id_fields = ('content', 'validator')


admin.site.register(PublishableContent, PublishableContentnAdmin)
admin.site.register(PublishedContent, PublishedContentAdmin)
admin.site.register(Validation, ValidationAdmin)
admin.site.register(ContentReaction, ContentReactionAdmin)
