
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^voir/(?P<news_pk>\d+)-(?P<news_slug>.+)$',views.view),
    url(r'^(?P<news_pk>\d+)/(?P<news_slug>.+)$', views.view),
    url(r'^nouveau$', views.new),
    url(r'^editer$', views.edit),
    url(r'^modifier$', views.modify),
    url(r'^rechercher/(?P<pk>\d+)$', views.find_news),
    url(r'^categorie/(?P<cat_pk>\d+)/(?P<cat_slug>.+)', views.list),
    url(r'^admin$', views.list_admin),
    url(r'^$', views.index),
    
    # Message-related
    url(r'^message/editer$', views.edit_comment),
    url(r'^message/nouveau$', views.answer),
)
