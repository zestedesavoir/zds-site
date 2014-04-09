# coding: utf-8

from django import forms

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

from .models import Article, Validation, Reaction, ArticleRead


admin.site.register(Article)
admin.site.register(ArticleRead)
admin.site.register(Reaction)
admin.site.register(Validation)

class MyUserCreationForm(UserCreationForm):
    username = forms.RegexField(
        label='Username', 
        max_length=30, 
        regex=r'^(.*)$',
        help_text = 'Required. 30 characters or fewer. Alphanumeric characters only (letters, digits, hyphens and underscores).',
        error_message = 'This value must contain only letters, numbers, hyphens and underscores.')

class MyUserChangeForm(UserChangeForm):
    username = forms.RegexField(
        label='Username', 
        max_length=30, 
        regex=r'^(.*)$',
        help_text = 'Required. 30 characters or fewer. Alphanumeric characters only (letters, digits, hyphens and underscores).',
        error_message = 'This value must contain only letters, numbers, hyphens and underscores.')

class MyUserAdmin(UserAdmin):
    form = MyUserChangeForm
    add_form = MyUserCreationForm

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)