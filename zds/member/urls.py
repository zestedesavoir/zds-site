# coding: utf-8

from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
                       url(r'^$', 'zds.member.views.index'),
                       url(r'^voir/ABC(?P<user_name>\w+)XYZ$', 'zds.member.views.details'),
                       url(r'^profil/modifier/(?P<user_pk>\d+)/$', 'zds.member.views.modify_profile'),
                       url(r'^profil/lier/$', 'zds.member.views.add_oldtuto'),
                       url(r'^profil/delier/$', 'zds.member.views.remove_oldtuto'),

                       url(r'^tutoriels/$', 'zds.member.views.tutorials'),
                       url(r'^articles/$', 'zds.member.views.articles'),
                       url(r'^actions/$', 'zds.member.views.actions'),

                       url(r'^parametres/profil/$', 'zds.member.views.settings_profile'),
                       url(r'^parametres/mini_profil/(?P<user_name>.+)/$', 'zds.member.views.settings_mini_profile'),
                       url(r'^parametres/compte/$', 'zds.member.views.settings_account'),
                       url(r'^parametres/user/$', 'zds.member.views.settings_user'),

                       url(r'^connexion/$', 'zds.member.views.login_view'),
                       url(r'^deconnexion/$', 'zds.member.views.logout_view'),
                       url(r'^inscription/$', 'zds.member.views.register_view'),
                       url(r'^reinitialisation/$', 'zds.member.views.forgot_password'),
                       url(r'^new_password/$', 'zds.member.views.new_password'),
                       url(r'^activation/$', 'zds.member.views.active_account'),
                       url(r'^envoi_jeton/$', 'zds.member.views.generate_token_account'),
                       )
