from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import GenericSitemap, Sitemap
from django.contrib.sitemaps.views import index as index_view, sitemap as sitemap_view
from django.urls import include, re_path, path, get_resolver, reverse

from zds.forum.models import ForumCategory, Forum, Topic, Tag
from zds.pages.views import home as home_view
from zds.tutorialv2.models.database import PublishedContent

from django.conf import settings


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
        urls = list(get_resolver(None).reverse_dict.keys())
        return [url for url in urls if 'pages-' in str(url)]

    def location(self, item):
        return reverse(item)


sitemaps = {
    'tutos': TutoSitemap,
    'articles': ArticleSitemap,
    'opinions': OpinionSitemap,
    'categories': GenericSitemap(
        {'queryset': ForumCategory.objects.all()},
        changefreq='yearly',
        priority=0.7
    ),
    'forums': GenericSitemap(
        {'queryset': Forum.objects.filter(groups__isnull=True).exclude(
            pk=settings.ZDS_APP['forum']['beta_forum_id'])},
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
    re_path(r'^', include(('zds.tutorialv2.urls', ''))),
    re_path(r'^forums/', include(('zds.forum.urls', ''))),
    re_path(r'^mp/', include(('zds.mp.urls', ''))),
    re_path(r'^membres/', include(('zds.member.urls', ''))),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^pages/', include(('zds.pages.urls', ''))),
    re_path(r'^galerie/', include(('zds.gallery.urls', ''))),
    re_path(r'^rechercher/', include(('zds.searchv2.urls',
                                      'zds.searchv2'), namespace='search')),
    re_path(r'^munin/', include(('zds.munin.urls', ''))),
    re_path(r'^mise-en-avant/', include(('zds.featured.urls', ''))),
    re_path(r'^notifications/',
            include(('zds.notification.urls', ''))),
    path('', include(('social_django.urls', 'social_django'), namespace='social')),

    re_path(r'^munin/', include(('munin.urls', 'munin'))),

    re_path(r'^$', home_view, name='homepage'),

    re_path(r'^api/', include(('zds.api.urls', 'zds.api'), namespace='api')),
    re_path(r'^oauth2/', include(('oauth2_provider.urls',
                                  'oauth2_provider'), namespace='oauth2_provider')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# SiteMap URLs
urlpatterns += [
    re_path(r'^sitemap\.xml$', index_view, {'sitemaps': sitemaps}),
    re_path(r'^sitemap-(?P<section>.+)\.xml$', sitemap_view, {'sitemaps': sitemaps},
            name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static
    from django.contrib.staticfiles.views import serve

    urlpatterns += [
        re_path(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.STATIC_URL, view=serve)

# custom view for 500 errors
handler500 = 'zds.pages.views.custom_error_500'
