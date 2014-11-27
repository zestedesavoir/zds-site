# coding: utf-8

from django.conf.urls import patterns, url

from zds.member.api.views import MemberListAPI

urlpatterns = patterns('',
                       url(r'^$', MemberListAPI.as_view()),
                       )
