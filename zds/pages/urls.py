from django.urls import re_path

from zds.pages.views import (
    about,
    association,
    eula,
    alerts,
    cookies,
    index,
    ContactView,
    CommentEditsHistory,
    EditDetail,
    restore_edit,
    delete_edit_content,
)

urlpatterns = [
    # single pages
    re_path(r"^apropos/$", about, name="pages-about"),
    re_path(r"^association/$", association, name="pages-association"),
    re_path(r"^contact/$", ContactView.as_view(), name="pages-contact"),
    re_path(r"^cgu/$", eula, name="pages-eula"),
    re_path(r"^alertes/$", alerts, name="pages-alerts"),
    re_path(r"^cookies/$", cookies, name="pages-cookies"),
    re_path(r"^historique-editions/(?P<comment_pk>\d+)/$", CommentEditsHistory.as_view(), name="comment-edits-history"),
    re_path(r"^contenu-original/(?P<pk>\d+)/$", EditDetail.as_view(), name="edit-detail"),
    re_path(r"^restaurer-edition/(?P<edit_pk>\d+)/$", restore_edit, name="restore-edit"),
    re_path(r"^supprimer-contenu-edition/(?P<edit_pk>\d+)/$", delete_edit_content, name="delete-edit-content"),
    # index
    re_path(r"^$", index, name="pages-index"),
]
