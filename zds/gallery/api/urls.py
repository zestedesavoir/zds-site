from django.conf.urls import url

from .views import GalleryListView, GalleryDetailView

urlpatterns = [
    url(r'^$', GalleryListView.as_view(), name='list'),
    url(r'^(?P<pk>[0-9]+)/?$', GalleryDetailView.as_view(), name='detail'),
]
