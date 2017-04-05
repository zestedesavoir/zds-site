# coding: utf-8

from django.conf.urls import url

from zds.tutorialv2.views.views_validations import AskValidationForContent, ReserveValidation, \
    HistoryOfValidationDisplay, AcceptValidation, RejectValidation, RevokeValidation, CancelValidation, \
    ValidationListView, PublishOpinion, UnpublishOpinion, PickOpinion, PromoteOpinionToArticle, \
    ValidationOpinionListView, UnpickOpinion, MarkObsolete, DoNotPickOpinion

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

    url(r'^publier/(?P<pk>\d+)/(?P<slug>.+)/$', PublishOpinion.as_view(), name='publish-opinion'),
    url(r'^depublier/(?P<pk>\d+)/(?P<slug>.+)/$', UnpublishOpinion.as_view(), name='unpublish-opinion'),
    url(r'^choisir/(?P<pk>\d+)/(?P<slug>.+)/$', PickOpinion.as_view(), name='pick-opinion'),
    url(r'^ignorer/(?P<pk>\d+)/(?P<slug>.+)/$', DoNotPickOpinion.as_view(), name='ignore-opinion'),
    url(r'^retirer/(?P<pk>\d+)/(?P<slug>.+)/$', UnpickOpinion.as_view(), name='unpick-opinion'),
    url(r'^promouvoir/(?P<pk>\d+)/(?P<slug>.+)/$', PromoteOpinionToArticle.as_view(), name='promote-opinion'),

    url(r'^marquer-obsolete/(?P<pk>\d+)/$', MarkObsolete.as_view(), name='mark-obsolete'),
    # VALIDATION VIEWS FOR STAFF

    url(r'^billets/$', ValidationOpinionListView.as_view(), name='list-opinion'),
    url(r'^$', ValidationListView.as_view(), name='list')
]
