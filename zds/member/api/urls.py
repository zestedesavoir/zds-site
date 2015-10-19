# coding: utf-8

from django.conf.urls import patterns, url

from zds.member.api.views import MemberListAPI, MemberDetailAPI, \
    MemberDetailReadingOnly, MemberDetailBan, MemberMyDetailAPI

urlpatterns = patterns('',
                       url(r'^$', MemberListAPI.as_view(), name='api-member-list'),
                       url(r'^mon-profil/$', MemberMyDetailAPI.as_view(), name='api-member-profile'),
                       url(r'^(?P<id>[0-9]+)/$', MemberDetailAPI.as_view(), name='api-member-detail'),
                       url(r'^(?P<id>[0-9]+)/lecture-seule/$', MemberDetailReadingOnly.as_view(),
                           name='api-member-read-only'),
                       url(r'^(?P<id>[0-9]+)/ban/$', MemberDetailBan.as_view(), name='api-member-ban'),
                       )
