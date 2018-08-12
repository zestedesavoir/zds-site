from django.conf.urls import url

from .views import GalleryListView

urlpatterns = [
    url(r'^$', GalleryListView.as_view(), name='list'),
]
