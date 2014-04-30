# coding: utf-8

from django import template

from django.contrib.auth.models import User

from zds.member.models import Profile


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
    if mode == 'W':
        return 'pencil'
    else:
        return 'eye'

@register.filter('state')
def state(user):
    try:
        profile = Profile.objects.get(user=user)
        if not profile.can_write_now() : state = 'BAN'
        elif not profile.can_read_now() : state = 'LS'
        elif user.has_perm('forum.change_post') : state = 'STAFF'
        else : state = None
    except Profile.DoesNotExist:
        state = None
    return state
