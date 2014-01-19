# coding: utf-8

from django import template

from zds.member.models import Profile
from django.contrib.auth.models import User


register = template.Library()


@register.filter('profile')
def profile(user):
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        profile = None
    return profile

@register.filter('user')
def user(pk):
    try:
        user = User.objects.get(pk=pk)
    except:
        user = None
    return user

@register.filter('mode')
def mode(mode):
    if mode=='W':
        return 'pencil'
    else:
        return 'eye'