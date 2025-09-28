from django.urls import path

from .views import active_sessions, active_users, db_performance, total_sessions, total_users

urlpatterns = [
    path("total_users/", total_users, name="total-users"),
    path("active_users/", active_users, name="active-users"),
    path("total_sessions/", total_sessions, name="total-sessions"),
    path("active_sessions/", active_sessions, name="active-sessions"),
    path("db_performance/", db_performance, name="db-performance"),
]
