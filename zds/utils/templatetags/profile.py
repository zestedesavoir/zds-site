# coding: utf-8

from django import template

from django.contrib.auth.models import User

from zds.member.models import Profile
from zds.utils.models import CommentLike, CommentDislike


register = template.Library()


@register.filter('profile')
def profile(the_user):
    try:
        user_profile = the_user.profile
    except Profile.DoesNotExist:
        user_profile = None
    return user_profile


@register.filter('user')
def user(user_pk):
    try:
        the_user = User.objects.get(pk=user_pk)
    except:
        the_user = None
    return the_user


@register.filter('state')
def state(the_user):
    try:
        user_profile = the_user.profile
        if not user_profile.user.is_active:
            user_state = 'DOWN'
        elif not user_profile.can_read_now():
            user_state = 'BAN'
        elif not user_profile.can_write_now():
            user_state = 'LS'
        elif the_user.has_perm('forum.change_post'):
            user_state = 'STAFF'
        else:
            user_state = None
    except Profile.DoesNotExist:
        user_state = None
    return user_state


@register.filter('liked')
def liked(the_user, comment_pk):
    return CommentLike.objects.filter(comments__pk=comment_pk, user=the_user).exists()


@register.filter('disliked')
def disliked(the_user, comment_pk):
    return CommentDislike.objects.filter(comments__pk=comment_pk, user=the_user).exists()
