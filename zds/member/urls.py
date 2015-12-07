# coding: utf-8

from django.conf.urls import url

from views import MemberList, MemberDetail, UpdateMember, UpdateAvatarMember, UpdatePasswordMember, \
    UpdateUsernameEmailMember, RegisterView, SendValidationEmailView

urlpatterns = [
    # list
    url(r'^$', MemberList.as_view(), name='member-list'),

    # details
    url(r'^voir/(?P<user_name>.+)/$', MemberDetail.as_view(), name='member-detail'),

    # modification
    url(r'^parametres/profil/$', UpdateMember.as_view(), name='update-member'),
    url(r'^parametres/profil/maj_avatar/$', UpdateAvatarMember.as_view(), name='update-avatar-member'),
    url(r'^parametres/compte/$', UpdatePasswordMember.as_view(), name='update-password-member'),
    url(r'^parametres/user/$', UpdateUsernameEmailMember.as_view(), name='update-username-email-member'),

    # old tuto
    url(r'^profil/lier/$', 'zds.member.views.add_oldtuto'),
    url(r'^profil/delier/$', 'zds.member.views.remove_oldtuto'),

    # moderation
    url(r'^profil/karmatiser/$', 'zds.member.views.modify_karma'),
    url(r'^profil/modifier/(?P<user_pk>\d+)/$', 'zds.member.views.modify_profile'),
    url(r'^parametres/mini_profil/(?P<user_name>.+)/$', 'zds.member.views.settings_mini_profile'),
    url(r'^profil/multi/(?P<ip_address>.+)/$', 'zds.member.views.member_from_ip'),

    # tutorials and articles
    url(r'^tutoriels/$', 'zds.member.views.tutorials'),
    url(r'^articles/$', 'zds.member.views.articles'),

    # user rights
    url(r'^profil/promouvoir/(?P<user_pk>\d+)/$', 'zds.member.views.settings_promote'),

    # membership
    url(r'^connexion/$', 'zds.member.views.login_view'),
    url(r'^deconnexion/$', 'zds.member.views.logout_view'),
    url(r'^inscription/$', RegisterView.as_view(), name='register-member'),
    url(r'^reinitialisation/$', 'zds.member.views.forgot_password'),
    url(r'^validation/$', SendValidationEmailView.as_view(), name='send-validation-email'),
    url(r'^new_password/$', 'zds.member.views.new_password'),
    url(r'^activation/$', 'zds.member.views.active_account'),
    url(r'^envoi_jeton/$', 'zds.member.views.generate_token_account'),
    url(r'^desinscrire/valider/$', 'zds.member.views.unregister'),
    url(r'^desinscrire/avertissement/$', 'zds.member.views.warning_unregister')
]
