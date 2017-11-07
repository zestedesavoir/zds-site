from django.urls import re_path

from zds.tutorialv2.api.views import ContentReactionKarmaView, ContainerPublicationReadinessView, ExportView,\
    RedactionChildrenListView, AuthorContentListCreateAPIView

urlpatterns = [
    re_path(r'^reactions/(?P<pk>\d+)/karma/?$',
            ContentReactionKarmaView.as_view(), name='reaction-karma'),
    re_path(r'^publication/preparation/(?P<pk>[0-9]+)/',
            ContainerPublicationReadinessView.as_view(), name='readiness'),
    re_path('export/(?P<pk>[0-9]+)/', ExportView.as_view(), name='generate_export'),
    re_path(r'^children-content/(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9_-]+)/'
            r'(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
            RedactionChildrenListView.as_view(public_is_prioritary=False),
            name='children-content'),
    re_path(r'^children-content/(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9_-]+)/(?P<container_slug>.+)/$',
            RedactionChildrenListView.as_view(public_is_prioritary=False),
            name='children-content'),

    re_path(r'^children-content/(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9_-]+)/$',
            RedactionChildrenListView.as_view(public_is_prioritary=False),
            name='children-content'),
    re_path(r'^(?P<user>\d+)/$',
            AuthorContentListCreateAPIView.as_view(),
            name='api-author-contents'),
    re_path(r'^(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9_-]+)/$',
            AuthorContentListCreateAPIView.as_view(),
            name='api-author-contents'),

]
