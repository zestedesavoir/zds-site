
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^voir/(?P<news_pk>\d+)-(?P<news_slug>.+)$',views.view),
    url(r'^(?P<news_pk>\d+)/(?P<news_slug>.+)$', views.view),
    url(r'^nouveau$', views.new),
    url(r'^editer$', views.edit),
    url(r'^modifier$', views.modify),
    url(r'^$', views.index),
)
