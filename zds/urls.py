# encoding: utf-8

from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.sitemaps import GenericSitemap

from zds.forum.models import Category, Forum

import pages.views
import settings

# SiteMap data
sitemaps = {
#    'blog': GenericSitemap(info_dict, priority=0.6),
    'categories':   GenericSitemap({'queryset': Category.objects.all()}, priority=0.7),
    'forums':       GenericSitemap({'queryset': Forum.objects.filter(group__isnull=True)}, priority=0.7),
}


admin.autodiscover()


urlpatterns = patterns('',
    url(r'^tutoriels/', include('zds.tutorial.urls')),
    url(r'^articles/', include('zds.article.urls')),
    url(r'^forums/', include('zds.forum.urls')),
    url(r'^mp/', include('zds.mp.urls')),
    url(r'^membres/', include('zds.member.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^pages/', include('zds.pages.urls')),
    url(r'^galerie/', include('zds.gallery.urls')),
    url(r'^teasing/', include('zds.newsletter.urls')),

    url(r'^captcha/', include('captcha.urls')),

    url(r'^$', pages.views.home),

)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SiteMap URLs
urlpatterns += patterns('django.contrib.sitemaps.views',
    (r'^sitemap\.xml$', 'index', {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'sitemap', {'sitemaps': sitemaps}),
)

if settings.SERVE:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
