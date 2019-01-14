from django.conf.urls import url, include

from rest_framework_swagger.views import get_swagger_view


schema_view = get_swagger_view()

urlpatterns = [
    url(r'^$', schema_view, name='docs'),
    url(r'^contenus/', include(('zds.tutorialv2.api.urls', 'zds.tutorialv2.api'), namespace='content')),
    url(r'^forums/', include(('zds.forum.api.urls', 'zds.forum.api'), namespace='forum')),
    url(r'^galeries/', include(('zds.gallery.api.urls', 'zds.gallery.api'), namespace='gallery')),
    url(r'^membres/', include(('zds.member.api.urls', 'zds.member.api'), namespace='member')),
    url(r'^mps/', include(('zds.mp.api.urls', 'zds.mp.api'), namespace='mp')),
    url(r'^tags/', include(('zds.utils.api.urls', 'zds.utils.api'), namespace='tag')),
    url(r'^notifications/', include(('zds.notification.api.urls', 'zds.notification.api'), namespace='notification')),
]
