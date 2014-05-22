# coding: utf-8

from django.contrib import admin

from .models import Profile, Ban, TokenRegister, TokenForgotPassword


admin.site.register(Profile)
admin.site.register(Ban)
admin.site.register(TokenRegister)
admin.site.register(TokenForgotPassword)
