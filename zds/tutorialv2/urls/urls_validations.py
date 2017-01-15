# coding: utf-8

from django.conf.urls import url

from zds.tutorialv2.views.views_validations import AskValidationForContent, ReserveValidation, \
    HistoryOfValidationDisplay, AcceptValidation, RejectValidation, RevokeValidation, CancelValidation, \
    ValidationListView

urlpatterns = [
    url(r'^proposer/(?P<pk>\d+)/(?P<slug>.+)/$', AskValidationForContent.as_view(), name='ask'),
    url(r'^historique/(?P<pk>\d+)/(?P<slug>.+)/$', HistoryOfValidationDisplay.as_view(), name='history'),

    url(r'^annuler/(?P<pk>\d+)/$', CancelValidation.as_view(), name='cancel'),
    url(r'^reserver/(?P<pk>\d+)/$', ReserveValidation.as_view(), name='reserve'),
    url(r'^refuser/(?P<pk>\d+)/$', RejectValidation.as_view(), name='reject'),
    url(r'^accepter/(?P<pk>\d+)/$', AcceptValidation.as_view(), name='accept'),

    url(r'^depublier/(?P<pk>\d+)/(?P<slug>.+)/$', RevokeValidation.as_view(), name='revoke'),

    url(r'^$', ValidationListView.as_view(), name='list')
]
