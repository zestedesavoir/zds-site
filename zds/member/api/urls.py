# coding: utf-8

from django.conf.urls import patterns, url

from zds.member.api.views import MemberListAPI, MemberDetailAPI

urlpatterns = patterns('',
                       url(r'^$', MemberListAPI.as_view()),
                       url(r'^(?P<pk>[0-9]+)/$', MemberDetailAPI.as_view()),
                       )
