# coding: utf-8

from django.contrib import admin

from zds.member.models import Profile, Ban, TokenRegister, TokenForgotPassword, KarmaNote


class ProfileAdmin(admin.ModelAdmin):
    """Representation of Profile model in the admin interface."""
    list_display = ('user', 'last_ip_address', 'can_read', 'end_ban_read', 'can_write', 'end_ban_write', 'last_visit')
    list_filter = ('can_read', 'can_write')
    search_fields = ['user__username']
    raw_id_fields = ('user',)


class BanAdmin(admin.ModelAdmin):
    """Representation of Ban model in the admin interface."""
    list_display = ('user', 'moderator', 'type', 'note', 'pubdate')
    list_filter = ('type',)
    search_fields = ['user__username']
    raw_id_fields = ('user', 'moderator')


class TokenRegisterAdmin(admin.ModelAdmin):
    """Representation of TokenRegister model in the admin interface."""
    list_display = ('user', 'date_end')
    search_fields = ['user__username']
    raw_id_fields = ('user',)


class TokenForgotPasswordAdmin(admin.ModelAdmin):
    """Representation of TokenForgotPassword model in the admin interface."""
    list_display = ('user', 'date_end')
    search_fields = ['user__username']
    raw_id_fields = ('user',)


class KarmaNoteAdmin(admin.ModelAdmin):
    """Representation of KarmaNote model in the admin interface."""
    list_display = ('user', 'moderator', 'note', 'karma', 'pubdate')
    search_fields = ['user__username']
    raw_id_fields = ('user', 'moderator')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Ban, BanAdmin)
admin.site.register(TokenRegister, TokenRegisterAdmin)
admin.site.register(TokenForgotPassword, TokenForgotPasswordAdmin)
admin.site.register(KarmaNote, KarmaNoteAdmin)
