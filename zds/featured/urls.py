from django.conf.urls import url

from zds.featured.views import FeaturedResourceList, FeaturedResourceCreate, FeaturedResourceUpdate, \
    FeaturedResourceDeleteDetail, FeaturedResourceDeleteList, FeaturedMessageCreateUpdate, FeaturedRequestedList, \
    FeaturedRequestedUpdate

urlpatterns = [
    url(r'^$', FeaturedResourceList.as_view(), name='featured-resource-list'),
    url(r'^unes/creer/$', FeaturedResourceCreate.as_view(), name='featured-resource-create'),
    url(r'^unes/editer/(?P<pk>\d+)/$', FeaturedResourceUpdate.as_view(), name='featured-resource-update'),
    url(r'^unes/supprimer/(?P<pk>\d+)/$', FeaturedResourceDeleteDetail.as_view(), name='featured-resource-delete'),
    url(r'^unes/supprimer/$', FeaturedResourceDeleteList.as_view(), name='featured-resource-list-delete'),

    url(r'^unes/requetes/$', FeaturedRequestedList.as_view(), name='featured-resource-requests'),
    url(r'^unes/requete/(?P<pk>\d+)/$', FeaturedRequestedUpdate.as_view(), name='featured-resource-request-update'),

    url(r'^message/modifier/$', FeaturedMessageCreateUpdate.as_view(), name='featured-message-create'),
]
