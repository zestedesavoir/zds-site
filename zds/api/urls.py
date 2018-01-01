from django.conf.urls import url, include

from rest_framework_swagger.views import get_swagger_view


schema_view = get_swagger_view()

urlpatterns = [
    url(r'^$', schema_view, name='docs'),
    url(r'^contenus/', include('zds.tutorialv2.api.urls', namespace='content')),
    url(r'^forums/', include('zds.forum.api.urls', namespace='forum')),
    url(r'^membres/', include('zds.member.api.urls', namespace='member')),
    url(r'^mps/', include('zds.mp.api.urls', namespace='mp')),
    url(r'^tags/', include('zds.utils.api.urls', namespace='tag')),
    url(r'^notifications/', include('zds.notification.api.urls', namespace='notification')),
]
