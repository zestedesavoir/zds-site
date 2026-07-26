from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import active_sessions, active_users, db_performance, total_sessions, total_users

urlpatterns = [
    path("total_users/", staff_member_required(total_users), name="total-users"),
    path("active_users/", staff_member_required(active_users), name="active-users"),
    path("total_sessions/", staff_member_required(total_sessions), name="total-sessions"),
    path("active_sessions/", staff_member_required(active_sessions), name="active-sessions"),
    path("db_performance/", staff_member_required(db_performance), name="db-performance"),
]
