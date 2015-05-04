# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views.views_validations import AskValidationForContent, ReserveValidation, \
    HistoryOfValidationDisplay, AcceptValidation, RejectValidation, RevokeValidation, CancelValidation, \
    ValidationListView

urlpatterns = patterns('',
                       url(r'^valider/proposer/(?P<pk>\d+)/(?P<slug>.+)/$', AskValidationForContent.as_view(),
                           name="ask"),
                       url(r'^valider/historique/(?P<pk>\d+)/(?P<slug>.+)/$', HistoryOfValidationDisplay.as_view(),
                           name="history"),

                       url(r'^valider/annuler/(?P<pk>\d+)/$', CancelValidation.as_view(),
                           name="cancel"),
                       url(r'^valider/reserver/(?P<pk>\d+)/$', ReserveValidation.as_view(),
                           name="reserve"),
                       url(r'^valider/refuser/(?P<pk>\d+)/$', RejectValidation.as_view(),
                           name="reject"),
                       url(r'^valider/accepter/(?P<pk>\d+)/$', AcceptValidation.as_view(),
                           name="accept"),

                       url(r'^valider/depublier/(?P<pk>\d+)/(?P<slug>.+)/$', RevokeValidation.as_view(),
                           name="revoke"),

                       url(r'^valider/liste/$', ValidationListView.as_view(), name="list"))
