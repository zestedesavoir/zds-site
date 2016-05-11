# coding: utf-8

from django.conf.urls import url

from zds.tutorialv2.views.views_validations import AskValidationForContent, ReserveValidation, \
    HistoryOfValidationDisplay, AcceptValidation, RejectValidation, RevokeValidation, CancelValidation, \
    ValidationListView, MarkObsolete, Publish, Unpublish, ValidPublication

urlpatterns = [
    url(r'^historique/(?P<pk>\d+)/(?P<slug>.+)/$', HistoryOfValidationDisplay.as_view(), name='history'),

    # VALIDATION BEFORE PUBLICATION

    # 1. ask validation
    url(r'^proposer/(?P<pk>\d+)/(?P<slug>.+)/$', AskValidationForContent.as_view(), name='ask'),
    # 2. take (or cancel) validation
    url(r'^reserver/(?P<pk>\d+)/$', ReserveValidation.as_view(), name='reserve'),
    url(r'^annuler/(?P<pk>\d+)/$', CancelValidation.as_view(), name='cancel'),
    # 3. accept or reject validation
    url(r'^refuser/(?P<pk>\d+)/$', RejectValidation.as_view(), name='reject'),
    url(r'^accepter/(?P<pk>\d+)/$', AcceptValidation.as_view(), name='accept'),
    # 4. cancel validation after publication
    url(r'^revoquer/(?P<pk>\d+)/(?P<slug>.+)/$', RevokeValidation.as_view(), name='revoke'),

    # NO VALIDATION BEFORE PUBLICATION

    url(r'^publier/(?P<pk>\d+)/(?P<slug>.+)/$', Publish.as_view(), name='publish'),
    url(r'^depublier/(?P<pk>\d+)/(?P<slug>.+)/$', Unpublish.as_view(), name='unpublish'),
    url(r'^valider/(?P<pk>\d+)/(?P<slug>.+)/$', ValidPublication.as_view(), name='valid'),

    url(r'^$', ValidationListView.as_view(), name='list'),

    url(r'^marquer-obsolete/(?P<pk>\d+)/$', MarkObsolete.as_view(), name='mark-obsolete'),
]
