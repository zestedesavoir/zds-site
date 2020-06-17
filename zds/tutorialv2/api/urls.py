from django.urls import path, re_path

from zds.tutorialv2.api.views import ContentReactionKarmaView, ContainerPublicationReadinessView, ExportView, ExportsView

urlpatterns = [
    re_path(r'^reactions/(?P<pk>\d+)/karma/?$',
            ContentReactionKarmaView.as_view(), name='reaction-karma'),
    re_path(r'^publication/preparation/(?P<pk>[0-9]+)/',
            ContainerPublicationReadinessView.as_view(), name='readiness'),
    re_path(r'^export/(?P<pk>[0-9]+)/', ExportView.as_view(), name='generate_export'),
    path('exports/<int:pk>/', ExportsView.as_view(), name='list_exports')
]
