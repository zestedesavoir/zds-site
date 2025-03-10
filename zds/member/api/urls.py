from django.urls import re_path

from zds.member.api.views import (
    MemberDetailAPI,
    MemberDetailBan,
    MemberDetailReadingOnly,
    MemberExistsAPI,
    MemberListAPI,
    MemberMyDetailAPI,
)

urlpatterns = [
    re_path(r"^$", MemberListAPI.as_view(), name="list"),
    re_path(r"^exists/?$", MemberExistsAPI.as_view(), name="exists"),
    re_path(r"^mon-profil/?$", MemberMyDetailAPI.as_view(), name="profile"),
    re_path(r"^(?P<user__id>[0-9]+)/?$", MemberDetailAPI.as_view(), name="detail"),
    re_path(r"^(?P<user__id>[0-9]+)/lecture-seule/?$", MemberDetailReadingOnly.as_view(), name="read-only"),
    re_path(r"^(?P<user__id>[0-9]+)/ban/?$", MemberDetailBan.as_view(), name="ban"),
]
