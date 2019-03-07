from django.urls import re_path

from zds.featured.views import FeaturedResourceList, FeaturedResourceCreate, FeaturedResourceUpdate, \
    FeaturedResourceDeleteDetail, FeaturedResourceDeleteList, FeaturedMessageCreateUpdate

urlpatterns = [
    re_path(r'^$', FeaturedResourceList.as_view(),
            name='featured-resource-list'),
    re_path(r'^unes/creer/$', FeaturedResourceCreate.as_view(),
            name='featured-resource-create'),
    re_path(r'^unes/editer/(?P<pk>\d+)/$',
            FeaturedResourceUpdate.as_view(), name='featured-resource-update'),
    re_path(r'^unes/supprimer/(?P<pk>\d+)/$',
            FeaturedResourceDeleteDetail.as_view(), name='featured-resource-delete'),
    re_path(r'^unes/supprimer/$', FeaturedResourceDeleteList.as_view(),
            name='featured-resource-list-delete'),
    re_path(r'^message/modifier/$', FeaturedMessageCreateUpdate.as_view(),
            name='featured-message-create'),
]
