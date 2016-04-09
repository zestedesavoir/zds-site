# coding: utf-8

from django.conf.urls import url

from zds.member.api.views import MemberListAPI, ContactableMemberListAPI, MemberDetailAPI, MemberDetailReadingOnly, MemberDetailBan, \
    MemberMyDetailAPI

urlpatterns = [
    url(r'^$', MemberListAPI.as_view(), name='list'),
    url(r'^contactable/$', ContactableMemberListAPI.as_view(), name='list'),
    url(r'^mon-profil/$', MemberMyDetailAPI.as_view(), name='profile'),
    url(r'^(?P<user__id>[0-9]+)/$', MemberDetailAPI.as_view(), name='detail'),
    url(r'^(?P<user__id>[0-9]+)/lecture-seule/$', MemberDetailReadingOnly.as_view(), name='read-only'),
    url(r'^(?P<user__id>[0-9]+)/ban/$', MemberDetailBan.as_view(), name='ban'),
]
