# coding: utf-8

from django.http import Http404

from zds.member.models import Profile

def can_read_now(func):
    '''Decorator to check that the user can read now'''
    def _can_read_now(request, *args, **kwargs):
        profile = Profile.objects.filter(user__pk=request.user.pk).all()
        if len(profile)>0:
            if not profile[0].can_read_now():
                raise Http404
        return func(request, *args, **kwargs)
    return _can_read_now

def can_write_and_read_now(func):
    '''Decorator to check that the user can read and write now'''
    def _can_write_and_read_now(request, *args, **kwargs):
        profile = Profile.objects.filter(user__pk=request.user.pk).all()
        if len(profile)>0:
            if not profile[0].can_read_now() or not profile[0].can_write_now():
                raise Http404
        return func(request, *args, **kwargs)
    return _can_write_and_read_now