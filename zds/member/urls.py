from django.contrib.auth.views import LogoutView
from django.urls import path

from zds.member.views import MemberList
from zds.member.views.admin import settings_promote
from zds.member.views.emailproviders import (
    AddBannedEmailProvider,
    BannedEmailProvidersList,
    MembersWithProviderList,
    NewEmailProvidersList,
    check_new_email_provider,
    remove_banned_email_provider,
)
from zds.member.views.hats import (
    HatDetail,
    HatRequestDetail,
    HatsList,
    HatsSettings,
    RequestedHatsList,
    SolvedHatRequestsList,
    add_hat,
    remove_hat,
    solve_hat_request,
)
from zds.member.views.login import LoginView
from zds.member.views.moderation import member_from_ip, modify_karma, modify_profile, settings_mini_profile
from zds.member.views.password_recovery import forgot_password, new_password
from zds.member.views.profile import (
    UpdateAvatarMember,
    UpdateGitHubToken,
    UpdateMember,
    UpdatePasswordMember,
    UpdateUsernameEmailMember,
    redirect_old_profile_to_new,
    remove_github_token,
)
from zds.member.views.register import (
    RegisterView,
    SendValidationEmailView,
    activate_account,
    generate_token_account,
    unregister,
    warning_unregister,
)
from zds.member.views.reports import CreateProfileReportView, SolveProfileReportView
from zds.member.views.sessions import DeleteSession, ListSessions

urlpatterns = [
    # list
    path("", MemberList.as_view(), name="member-list"),
    # details
    path("voir/<str:user_name>/", redirect_old_profile_to_new, name="member-detail-redirect"),
    # modification
    path("parametres/profil/", UpdateMember.as_view(), name="update-member"),
    path("parametres/github/", UpdateGitHubToken.as_view(), name="update-github"),
    path("parametres/github/supprimer/", remove_github_token, name="remove-github"),
    path("parametres/profil/maj_avatar/", UpdateAvatarMember.as_view(), name="update-avatar-member"),
    path("parametres/compte/", UpdatePasswordMember.as_view(), name="update-password-member"),
    path("parametres/user/", UpdateUsernameEmailMember.as_view(), name="update-username-email-member"),
    path("parametres/sessions/", ListSessions.as_view(), name="list-sessions"),
    path("parametres/sessions/supprimer/", DeleteSession.as_view(), name="delete-session"),
    # moderation
    path("profil/signaler/<int:profile_pk>/", CreateProfileReportView.as_view(), name="report-profile"),
    path("profil/resoudre/<int:alert_pk>/", SolveProfileReportView.as_view(), name="solve-profile-alert"),
    path("profil/karmatiser/", modify_karma, name="member-modify-karma"),
    path("profil/modifier/<int:user_pk>/", modify_profile, name="member-modify-profile"),
    path("parametres/mini_profil/<user_name>/", settings_mini_profile, name="member-settings-mini-profile"),
    path("profil/multi/<ip_address>/", member_from_ip, name="member-from-ip"),
    # email providers
    path("fournisseurs-email/nouveaux/", NewEmailProvidersList.as_view(), name="new-email-providers"),
    path(
        "fournisseurs-email/nouveaux/verifier/<int:provider_pk>/",
        check_new_email_provider,
        name="check-new-email-provider",
    ),
    path("fournisseurs-email/bannis/", BannedEmailProvidersList.as_view(), name="banned-email-providers"),
    path("fournisseurs-email/bannis/ajouter/", AddBannedEmailProvider.as_view(), name="add-banned-email-provider"),
    path(
        "fournisseurs-email/bannis/rechercher/<int:provider_pk>/",
        MembersWithProviderList.as_view(),
        name="members-with-provider",
    ),
    path(
        "fournisseurs-email/bannis/supprimer/<int:provider_pk>/",
        remove_banned_email_provider,
        name="remove-banned-email-provider",
    ),
    # user rights
    path("profil/promouvoir/<int:user_pk>/", settings_promote, name="member-settings-promote"),
    # hats
    path("casquettes/", HatsList.as_view(), name="hats-list"),
    path("casquettes/<int:pk>/", HatDetail.as_view(), name="hat-detail"),
    path("parametres/casquettes/", HatsSettings.as_view(), name="hats-settings"),
    path("casquettes/demandes/", RequestedHatsList.as_view(), name="requested-hats"),
    path("casquettes/demandes/archives/", SolvedHatRequestsList.as_view(), name="solved-hat-requests"),
    path("casquettes/demandes/<int:pk>/", HatRequestDetail.as_view(), name="hat-request"),
    path("casquettes/demandes/<int:request_pk>/resoudre/", solve_hat_request, name="solve-hat-request"),
    path("casquettes/ajouter/<int:user_pk>/", add_hat, name="add-hat"),
    path("casquettes/retirer/<int:user_pk>/<int:hat_pk>/", remove_hat, name="remove-hat"),
    # membership
    path("connexion/", LoginView.as_view(), name="member-login"),
    path("deconnexion/", LogoutView.as_view(), name="member-logout"),
    path("inscription/", RegisterView.as_view(), name="register-member"),
    path("reinitialisation/", forgot_password, name="member-forgot-password"),
    path("validation/", SendValidationEmailView.as_view(), name="send-validation-email"),
    path("new_password/", new_password, name="member-new-password"),
    path("activation/", activate_account, name="member-active-account"),
    path("envoi_jeton/", generate_token_account, name="member-generate-token-account"),
    path("desinscrire/valider/", unregister, name="member-unregister"),
    path("desinscrire/avertissement/", warning_unregister, name="member-warning-unregister"),
]
