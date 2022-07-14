from django.urls import path

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
    path("apropos/", about, name="pages-about"),
    path("association/", association, name="pages-association"),
    path("contact/", ContactView.as_view(), name="pages-contact"),
    path("cgu/", eula, name="pages-eula"),
    path("alertes/", alerts, name="pages-alerts"),
    path("cookies/", cookies, name="pages-cookies"),
    path("historique-editions/<int:comment_pk>/", CommentEditsHistory.as_view(), name="comment-edits-history"),
    path("contenu-original/<int:pk>/", EditDetail.as_view(), name="edit-detail"),
    path("restaurer-edition/<int:edit_pk>/", restore_edit, name="restore-edit"),
    path("supprimer-contenu-edition/<int:edit_pk>/", delete_edit_content, name="delete-edit-content"),
    # index
    path("", index, name="pages-index"),
]
