from django.urls import re_path

from zds.tutorialv2.views.validations_contents import AskValidationForContent, ReserveValidation, \
    ValidationHistoryView, AcceptValidation, RejectValidation, RevokeValidation, CancelValidation, \
    ValidationListView, MarkObsolete
from zds.tutorialv2.views.validations_opinions import PublishOpinion, UnpublishOpinion, DoNotPickOpinion, \
    RevokePickOperation, PickOpinion, UnpickOpinion, ValidationOpinionListView, PromoteOpinionToArticle

urlpatterns = [
    re_path(r'^historique/(?P<pk>\d+)/(?P<slug>.+)/$',
            ValidationHistoryView.as_view(), name='history'),

    # VALIDATION BEFORE PUBLICATION

    # 1. ask validation
    re_path(r'^proposer/(?P<pk>\d+)/(?P<slug>.+)/$',
            AskValidationForContent.as_view(), name='ask'),
    # 2. take (or cancel) validation
    re_path(r'^reserver/(?P<pk>\d+)/$', ReserveValidation.as_view(), name='reserve'),
    re_path(r'^annuler/(?P<pk>\d+)/$', CancelValidation.as_view(), name='cancel'),
    # 3. accept or reject validation
    re_path(r'^refuser/(?P<pk>\d+)/$', RejectValidation.as_view(), name='reject'),
    re_path(r'^accepter/(?P<pk>\d+)/$', AcceptValidation.as_view(), name='accept'),
    # 4. cancel validation after publication
    re_path(r'^revoquer/(?P<pk>\d+)/(?P<slug>.+)/$',
            RevokeValidation.as_view(), name='revoke'),

    # NO VALIDATION BEFORE PUBLICATION

    re_path(r'^publier/(?P<pk>\d+)/(?P<slug>.+)/$',
            PublishOpinion.as_view(), name='publish-opinion'),
    re_path(r'^depublier/(?P<pk>\d+)/(?P<slug>.+)/$',
            UnpublishOpinion.as_view(), name='unpublish-opinion'),
    re_path(r'^choisir/(?P<pk>\d+)/(?P<slug>.+)/$',
            PickOpinion.as_view(), name='pick-opinion'),
    re_path(r'^ignorer/(?P<pk>\d+)/(?P<slug>.+)/$',
            DoNotPickOpinion.as_view(), name='ignore-opinion'),
    re_path(r'^operation/annuler/(?P<pk>\d+)/$',
            RevokePickOperation.as_view(), name='revoke-ignore-opinion'),
    re_path(r'^retirer/(?P<pk>\d+)/(?P<slug>.+)/$',
            UnpickOpinion.as_view(), name='unpick-opinion'),
    re_path(r'^promouvoir/(?P<pk>\d+)/(?P<slug>.+)/$',
            PromoteOpinionToArticle.as_view(), name='promote-opinion'),

    re_path(r'^marquer-obsolete/(?P<pk>\d+)/$',
            MarkObsolete.as_view(), name='mark-obsolete'),
    # VALIDATION VIEWS FOR STAFF

    re_path(r'^billets/$', ValidationOpinionListView.as_view(), name='list-opinion'),
    re_path(r'^$', ValidationListView.as_view(), name='list')
]
