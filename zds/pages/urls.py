# coding: utf-8

from django.conf.urls import url

from zds.pages.views import about, association, eula, alerts, cookies, index, AssocSubscribeView, \
    ContactView, CommentEditsHistory, EditDetail, restore_edit, delete_edit_content

urlpatterns = [
    # single pages
    url(r'^apropos/$', about, name='pages-about'),
    url(r'^association/$', association, name='pages-association'),
    url(r'^contact/$', ContactView.as_view(), name='pages-contact'),
    url(r'^cgu/$', eula, name='pages-eula'),
    url(r'^alertes/$', alerts, name='pages-alerts'),
    url(r'^cookies/$', cookies, name='pages-cookies'),
    url(r'^association/inscription/$', AssocSubscribeView.as_view(), name='pages-assoc-subscribe'),
    url(r'^historique-editions/(?P<comment_pk>\d+)/$', CommentEditsHistory.as_view(), name='comment-edits-history'),
    url(r'^contenu-original/(?P<pk>\d+)/$', EditDetail.as_view(), name='edit-detail'),
    url(r'^restaurer-edition/(?P<edit_pk>\d+)/$', restore_edit, name='restore-edit'),
    url(r'^supprimer-contenu-edition/(?P<edit_pk>\d+)/$', delete_edit_content, name='delete-edit-content'),

    # index
    url(r'^$', index, name='pages-index'),
]
