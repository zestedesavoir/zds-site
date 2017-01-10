from django.conf.urls import url

from munin.views import total_users, active_users, total_sessions, \
    active_sessions, db_performance

urlpatterns = [
    url(r'^total_users/$', total_users),
    url(r'^active_users/$', active_users),
    url(r'^total_sessions/$', total_sessions),
    url(r'^active_sessions/$', active_sessions),
    url(r'^db_performance/$', db_performance),
]
