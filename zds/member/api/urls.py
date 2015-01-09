# coding: utf-8

from django.conf.urls import patterns, url

from zds.member.api.views import MemberListAPI, MemberDetailAPI, \
    MemberDetailReadingOnly, MemberDetailBan

urlpatterns = patterns('',
                       url(r'^$', MemberListAPI.as_view()),
                       url(r'^(?P<pk>[0-9]+)/$', MemberDetailAPI.as_view()),
                       url(r'^(?P<pk>[0-9]+)/lecture-seule/$', MemberDetailReadingOnly.as_view()),
                       url(r'^(?P<pk>[0-9]+)/ban/$', MemberDetailBan.as_view()),
                       )
