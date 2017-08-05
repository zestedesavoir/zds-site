# encoding: utf-8

from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.contrib.sitemaps.views import index as index_view, sitemap as sitemap_view
from django.core.urlresolvers import get_resolver, reverse

from zds.forum.models import Category, Forum, Topic, Tag
from zds.pages.views import home as home_view
from zds.tutorialv2.models.models_database import PublishedContent

from . import settings


# SiteMap data
class ContentSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 1

    def items(self):
        return (
            PublishedContent.objects
            .filter(must_redirect=False, content_type=self.content_type)
            .prefetch_related('content')
        )

    def lastmod(self, content):
        return content.update_date or content.publication_date

    def location(self, content):
        return content.get_absolute_url_online()


class TutoSitemap(ContentSitemap):
    content_type = 'TUTORIAL'


class ArticleSitemap(ContentSitemap):
    content_type = 'ARTICLE'


class OpinionSitemap(ContentSitemap):
    content_type = 'OPINION'


class PageSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.5

    def items(self):
        urls = get_resolver(None).reverse_dict.keys()
        return [url for url in urls if 'pages-' in str(url)]

    def location(self, item):
        return reverse(item)


sitemaps = {
    'tutos': TutoSitemap,
    'articles': ArticleSitemap,
    'opinions': OpinionSitemap,
    'categories': GenericSitemap(
        {'queryset': Category.objects.all()},
        changefreq='yearly',
        priority=0.7
    ),
    'forums': GenericSitemap(
        {'queryset': Forum.objects.filter(groups__isnull=True).exclude(pk=settings.ZDS_APP['forum']['beta_forum_id'])},
        changefreq='yearly',
        priority=0.7
    ),
    'topics': GenericSitemap(
        {'queryset': Topic.objects.filter(is_locked=False,
                                          forum__groups__isnull=True)
                                  .exclude(forum__pk=settings.ZDS_APP['forum']['beta_forum_id']),
         'date_field': 'pubdate'},
        changefreq='hourly',
        priority=0.7
    ),
    'tags': GenericSitemap(
        {'queryset': Tag.objects.all()}
    ),
    'pages': PageSitemap,
}


admin.autodiscover()


urlpatterns = [
    url(r'^', include('zds.tutorialv2.urls')),
    url(r'^forums/', include('zds.forum.urls')),
    url(r'^mp/', include('zds.mp.urls')),
    url(r'^membres/', include('zds.member.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^pages/', include('zds.pages.urls')),
    url(r'^galerie/', include('zds.gallery.urls')),
    url(r'^rechercher/', include('zds.searchv2.urls', namespace='search')),
    url(r'^munin/', include('zds.munin.urls')),
    url(r'^mise-en-avant/', include('zds.featured.urls')),
    url(r'^notifications/', include('zds.notification.urls')),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url('', include('django.contrib.auth.urls', namespace='auth')),

    url(r'^munin/', include('munin.urls')),

    url(r'^$', home_view, name='homepage'),

    url(r'^api/', include('zds.api.urls', namespace='api')),
    url(r'^oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SiteMap URLs
urlpatterns += [
    url(r'^sitemap\.xml$', index_view, {'sitemaps': sitemaps}),
    url(r'^sitemap-(?P<section>.+)\.xml$', sitemap_view, {'sitemaps': sitemaps}),
]

if settings.SERVE:
    from django.views.static import serve
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

# custom view for 500 errors
handler500 = 'zds.pages.views.custom_error_500'
