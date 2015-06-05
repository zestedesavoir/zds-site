# coding: utf-8

from django.conf.urls import include, url

urlpatterns = [
    url(r'^', include('rest_framework_swagger.urls', namespace='docs')),
    url(r'^contenus/', include('zds.tutorialv2.api.urls', namespace='content')),
    url(r'^forums/', include('zds.forum.api.urls', namespace='forum')),
    url(r'^membres/', include('zds.member.api.urls', namespace='member')),
    url(r'^mps/', include('zds.mp.api.urls', namespace='mp')),
    url(r'^tags/', include('zds.utils.api.urls', namespace='tag')),
    url(r'^notifications/', include('zds.notification.api.urls', namespace='notification')),
    url(r'^api/stats/contenus/', include('zds.stats.api.urls', namespace='stats')),
]
