# coding: utf-8

from django import template

from django.contrib.auth.models import User

from zds.member.models import Profile
from zds.utils.models import Comment, CommentLike, CommentDislike


register = template.Library()


@register.filter('profile')
def profile(user):
    try:
        profile = user.profile
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
        profile = user.profile
        if not profile.user.is_active : state = 'DOWN'
        elif not profile.can_read_now() : state = 'BAN'
        elif not profile.can_write_now() : state = 'LS'
        elif user.has_perm('forum.change_post') : state = 'STAFF'
        else : state = None
    except Profile.DoesNotExist:
        state = None
    return state

@register.filter('liked')
def liked(user, comment_pk):
    comment = Comment.objects.get(pk = comment_pk)
    return CommentLike.objects.filter(comments = comment, user=user).count() > 0

@register.filter('disliked')
def disliked(user, comment_pk):
    comment = Comment.objects.get(pk = comment_pk)
    return CommentDislike.objects.filter(comments = comment, user=user).count() > 0