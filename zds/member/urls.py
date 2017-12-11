from django.conf.urls import url

from zds.member.views import MemberList, MemberDetail, UpdateMember, UpdateGitHubToken, remove_github_token, \
    UpdateAvatarMember, UpdatePasswordMember, UpdateUsernameEmailMember, RegisterView, \
    SendValidationEmailView, modify_karma, modify_profile, settings_mini_profile, member_from_ip, \
    settings_promote, login_view, logout_view, forgot_password, new_password, activate_account, \
    generate_token_account, unregister, warning_unregister, BannedEmailProvidersList, NewEmailProvidersList, \
    AddBannedEmailProvider, remove_banned_email_provider, check_new_email_provider, MembersWithProviderList, \
    HatsSettings, RequestedHatsList, HatRequestDetail, add_hat, remove_hat, solve_hat_request, HatsList, HatDetail, \
    SolvedHatRequestsList

urlpatterns = [
    # list
    url(r'^$', MemberList.as_view(), name='member-list'),

    # details
    url(r'^voir/(?P<user_name>.+)/$', MemberDetail.as_view(), name='member-detail'),

    # modification
    url(r'^parametres/profil/$', UpdateMember.as_view(), name='update-member'),
    url(r'^parametres/github/$', UpdateGitHubToken.as_view(), name='update-github'),
    url(r'^parametres/github/supprimer/$', remove_github_token, name='remove-github'),
    url(r'^parametres/profil/maj_avatar/$', UpdateAvatarMember.as_view(), name='update-avatar-member'),
    url(r'^parametres/compte/$', UpdatePasswordMember.as_view(), name='update-password-member'),
    url(r'^parametres/user/$', UpdateUsernameEmailMember.as_view(), name='update-username-email-member'),

    # moderation
    url(r'^profil/karmatiser/$', modify_karma, name='member-modify-karma'),
    url(r'^profil/modifier/(?P<user_pk>\d+)/$', modify_profile, name='member-modify-profile'),
    url(r'^parametres/mini_profil/(?P<user_name>.+)/$', settings_mini_profile, name='member-settings-mini-profile'),
    url(r'^profil/multi/(?P<ip_address>.+)/$', member_from_ip, name='member-from-ip'),

    # email providers
    url(r'^fournisseurs-email/nouveaux/$', NewEmailProvidersList.as_view(), name='new-email-providers'),
    url(r'^fournisseurs-email/nouveaux/verifier/(?P<provider_pk>\d+)/$', check_new_email_provider,
        name='check-new-email-provider'),
    url(r'^fournisseurs-email/bannis/$', BannedEmailProvidersList.as_view(), name='banned-email-providers'),
    url(r'^fournisseurs-email/bannis/ajouter/$', AddBannedEmailProvider.as_view(), name='add-banned-email-provider'),
    url(r'^fournisseurs-email/bannis/rechercher/(?P<provider_pk>\d+)/$', MembersWithProviderList.as_view(),
        name='members-with-provider'),
    url(r'^fournisseurs-email/bannis/supprimer/(?P<provider_pk>\d+)/$', remove_banned_email_provider,
        name='remove-banned-email-provider'),

    # user rights
    url(r'^profil/promouvoir/(?P<user_pk>\d+)/$', settings_promote, name='member-settings-promote'),

    # hats
    url(r'^casquettes/$', HatsList.as_view(), name='hats-list'),
    url(r'^casquettes/(?P<pk>\d+)/$', HatDetail.as_view(), name='hat-detail'),
    url(r'^parametres/casquettes/$', HatsSettings.as_view(), name='hats-settings'),
    url(r'^casquettes/demandes/$', RequestedHatsList.as_view(), name='requested-hats'),
    url(r'^casquettes/demandes/archives/$', SolvedHatRequestsList.as_view(), name='solved-hat-requests'),
    url(r'^casquettes/demandes/(?P<pk>\d+)/$', HatRequestDetail.as_view(), name='hat-request'),
    url(r'^casquettes/demandes/(?P<request_pk>\d+)/resoudre/$', solve_hat_request, name='solve-hat-request'),
    url(r'^casquettes/ajouter/(?P<user_pk>\d+)/$', add_hat, name='add-hat'),
    url(r'^casquettes/retirer/(?P<user_pk>\d+)/(?P<hat_pk>\d+)/$', remove_hat, name='remove-hat'),

    # membership
    url(r'^connexion/$', login_view, name='member-login'),
    url(r'^deconnexion/$', logout_view, name='member-logout'),
    url(r'^inscription/$', RegisterView.as_view(), name='register-member'),
    url(r'^reinitialisation/$', forgot_password, name='member-forgot-password'),
    url(r'^validation/$', SendValidationEmailView.as_view(), name='send-validation-email'),
    url(r'^new_password/$', new_password, name='member-new-password'),
    url(r'^activation/$', activate_account, name='member-active-account'),
    url(r'^envoi_jeton/$', generate_token_account, name='member-generate-token-account'),
    url(r'^desinscrire/valider/$', unregister, name='member-unregister'),
    url(r'^desinscrire/avertissement/$', warning_unregister, name='member-warning-unregister')
]
