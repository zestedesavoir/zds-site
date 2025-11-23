from django.urls import path

from zds.pages.views import (
    CommentEditsHistory,
    ContactView,
    EditDetail,
    about,
    accessibility,
    alerts,
    association,
    cookies,
    delete_edit_content,
    eula,
    index,
    restore_edit,
)

urlpatterns = [
    # single pages
    path("technologies/", about, name="pages-technologies"),
    path("association/", association, name="pages-association"),
    path("contact/", ContactView.as_view(), name="pages-contact"),
    path("accessibilite/", accessibility, name="pages-accessibility"),
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
