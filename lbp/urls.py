# encoding: utf-8

from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.auth.models import User, Group

from haystack.views import SearchView
from haystack.forms import ModelSearchForm

from rest_framework import viewsets, routers
from django.contrib import admin

autocomplete_light.autodiscover()

admin.autodiscover()

import pages.views
import settings

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    model = User

class GroupViewSet(viewsets.ModelViewSet):
    model = Group

# Routers provide an easy way of automatically determining the URL conf
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)

urlpatterns = patterns('',
    url(r'^news/', include('lbp.news.urls')),
    url(r'^projet/', include('lbp.project.urls')),
    url(r'^forums/', include('lbp.forum.urls')),
    url(r'^mp/', include('lbp.mp.urls')),
    url(r'^membres/', include('lbp.member.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^pages/', include('lbp.pages.urls')),
    url(r'^galerie/', include('lbp.gallery.urls')),
    url(r'^api/', include('lbp.api.urls')),

    url(r'^captcha/', include('captcha.urls')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),

    url(r'^$', pages.views.home),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api-docs/', include('rest_framework_swagger.urls')),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),

    url(r'^recherche/', SearchView(
            template='search/search.html',
            form_class=ModelSearchForm),
        name='haystack_search'),
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SERVE:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
