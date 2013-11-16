# encoding: utf-8

from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.models import User, Group

import pages.views
import settings


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^tutoriels/', include('zds.tutorial.urls')),
    url(r'^forums/', include('zds.forum.urls')),
    url(r'^mp/', include('zds.mp.urls')),
    url(r'^membres/', include('zds.member.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^pages/', include('zds.pages.urls')),
    url(r'^galerie/', include('zds.gallery.urls')),

    url(r'^captcha/', include('captcha.urls')),

    url(r'^$', pages.views.home),

)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SERVE:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
