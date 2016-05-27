# coding: utf-8

from django import template

from django.contrib.auth.models import User

from zds.member.models import Profile


register = template.Library()

perms = {'forum.change_post': {}}


@register.filter('profile')
def profile(current_user):
    try:
        current_profile = current_user.profile
    except Profile.DoesNotExist:
        current_profile = None
    return current_profile


@register.filter('user')
def user(user_pk):
    try:
        current_user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        current_user = None
    return current_user


@register.filter('state')
def state(current_user):
    try:
        user_profile = current_user.profile
        if not user_profile.user.is_active:
            user_state = 'DOWN'
        elif not user_profile.can_read_now():
            user_state = 'BAN'
        elif not user_profile.can_write_now():
            user_state = 'LS'
        elif current_user.pk in perms['forum.change_post'] and perms['forum.change_post'][current_user.pk]:
            user_state = 'STAFF'
        elif current_user.pk not in perms['forum.change_post']:
            perms['forum.change_post'][current_user.pk] = current_user.has_perm('forum.change_post')
            user_state = None
            if perms['forum.change_post'][current_user.pk]:
                user_state = 'STAFF'
        else:
            user_state = None
    except Profile.DoesNotExist:
        user_state = None
    return user_state
