from django.contrib import admin

from zds.member.models import Profile, Ban, TokenRegister, TokenForgotPassword, KarmaNote


class ProfileAdmin(admin.ModelAdmin):

    """Representation of Profile model in the admin interface."""

    list_display = ('user', 'last_ip_address', 'can_read', 'end_ban_read', 'can_write', 'end_ban_write', 'last_visit')
    list_filter = ('can_read', 'can_write')


class BanAdmin(admin.ModelAdmin):

    """Representation of Ban model in the admin interface."""

    list_display = ('user', 'moderator', 'type', 'text', 'pubdate')
    list_filter = ('type',)


class TokenRegisterAdmin(admin.ModelAdmin):

    """Representation of TokenRegister model in the admin interface."""

    list_display = ('user', 'date_end')


class TokenForgotPasswordAdmin(admin.ModelAdmin):

    """Representation of TokenForgotPassword model in the admin interface."""

    list_display = ('user', 'date_end')


class KarmaNoteAdmin(admin.ModelAdmin):

    """Representation of KarmaNote model in the admin interface."""

    list_display = ('user', 'staff', 'comment', 'value', 'create_at')


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Ban, BanAdmin)
admin.site.register(TokenRegister, TokenRegisterAdmin)
admin.site.register(TokenForgotPassword, TokenForgotPasswordAdmin)
admin.site.register(KarmaNote, KarmaNoteAdmin)
