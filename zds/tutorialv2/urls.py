# coding: utf-8

from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
                       url(r'^contenus/', include('zds.tutorialv2.url.url_contents', namespace='content'))
)

"""urlpatterns = patterns('',
                       # viewing articles
                       url(r'^articles/$', ArticleList.as_view(), name="index-article"),
                       url(r'^articles/flux/rss/$', feeds.LastArticlesFeedRSS(), name='article-feed-rss'),
                       url(r'^articles/flux/atom/$', feeds.LastArticlesFeedATOM(), name='article-feed-atom'),


                       # Viewing
                       url(r'^flux/rss/$', feeds.LastTutorialsFeedRSS(), name='tutorial-feed-rss'),
                       url(r'^flux/atom/$', feeds.LastTutorialsFeedATOM(), name='tutorial-feed-atom'),

                       # Current URLs
                       # url(r'^recherche/(?P<pk_user>\d+)/$',
                       #     'zds.tutorialv2.views.find_tuto'),

                       # url(r'^off/(?P<content_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<chapter_slug>.+)/$',
                       #     'zds.tutorialv2.views.view_chapter',
                       #     name="view-chapter-url"),

                       # url(r'^off/(?P<content_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
                       #     'zds.tutorialv2.views.view_part',
                       #     name="view-part-url"),

                       url(r'^off/tutoriel/(?P<content_slug>.+)/$',
                           DisplayContent.as_view(),
                           name='view-tutorial-url'),

                       url(r'^off/article/(?P<content_slug>.+)/$',
                           DisplayArticle.as_view()),

                       # View online
                       # url(r'^(?P<content_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<chapter_slug>.+)/$',
                       #     'zds.tutorialv2.views.view_chapter_online',
                       #     name="view-chapter-url-online"),
                       #
                       # url(r'^(?P<content_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
                       #     'zds.tutorialv2.views.view_part_online',
                       #     name="view-part-url-online"),
                       #
                       # url(r'^tutoriel/(?P<content_pk>\d+)/(?P<tutorial_slug>.+)/$',
                       #     DisplayOnlineContent.as_view()),
                       #
                       # url(r'^article/(?P<content_pk>\d+)/(?P<tutorial_slug>.+)/$',
                       #     DisplayOnlineArticle.as_view()),

                       # Editing
                       # url(r'^editer/tutoriel/$',
                       #     'zds.tutorialv2.views.edit_tutorial'),
                       # url(r'^modifier/tutoriel/$',
                       #     'zds.tutorialv2.views.modify_tutorial'),
                       # url(r'^modifier/partie/$',
                       #     'zds.tutorialv2.views.modify_part'),
                       # url(r'^editer/partie/$',
                       #     'zds.tutorialv2.views.edit_part'),
                       # url(r'^modifier/chapitre/$',
                       #     'zds.tutorialv2.views.modify_chapter'),
                       # url(r'^editer/chapitre/$',
                       #     'zds.tutorialv2.views.edit_chapter'),
                       # url(r'^modifier/extrait/$',
                       #     'zds.tutorialv2.views.modify_extract'),
                       # url(r'^editer/extrait/$',
                       #     'zds.tutorialv2.views.edit_extract'),

                       # Adding
                       # url(r'^nouveau/tutoriel/$',
                       #     'zds.tutorialv2.views.add_tutorial'),
                       # url(r'^nouveau/partie/$',
                       #     'zds.tutorialv2.views.add_part'),
                       # url(r'^nouveau/chapitre/$',
                       #     'zds.tutorialv2.views.add_chapter'),
                       # url(r'^nouveau/extrait/$',
                       #     'zds.tutorialv2.views.add_extract'),

                       # url(r'^$', TutorialList.as_view, name='index-tutorial'),
                       # url(r'^importer/$', 'zds.tutorialv2.views.import_tuto'),
                       # url(r'^import_local/$',
                       #     'zds.tutorialv2.views.local_import'),
                       # url(r'^telecharger/$', 'zds.tutorialv2.views.download'),
                       # url(r'^telecharger/pdf/$',
                       #     'zds.tutorialv2.views.download_pdf'),
                       # url(r'^telecharger/html/$',
                       #     'zds.tutorialv2.views.download_html'),
                       # url(r'^telecharger/epub/$',
                       #     'zds.tutorialv2.views.download_epub'),
                       # url(r'^telecharger/md/$',
                       #     'zds.tutorialv2.views.download_markdown'),
                       url(r'^historique/(?P<tutorial_slug>.+)/$',
                           'zds.tutorialv2.views.history',
                           name='view-tutorial-history-url'),
                       # url(r'^comparaison/(?P<tutorial_slug>.+)/$',
                       #      DisplayDiff.as_view(),
                       #      name='view-tutorial-diff-url'),

                       # user actions
                       url(r'^suppression/(?P<tutorial_slug>.+)/$',
                           'zds.tutorialv2.views.delete_tutorial'),
                       url(r'^validation/tutoriel/$',
                           'zds.tutorialv2.views.ask_validation'),

                       # Validation
                       # url(r'^validation/$',
                       #     'zds.tutorialv2.views.list_validation'),
                       # url(r'^validation/reserver/(?P<validation_pk>\d+)/$',
                       #     'zds.tutorialv2.views.reservation'),
                       # url(r'^validation/reject/$',
                       #     'zds.tutorialv2.views.reject_tutorial'),
                       # url(r'^validation/valid/$',
                       #     'zds.tutorialv2.views.valid_tutorial'),
                       # url(r'^validation/invalid/(?P<tutorial_pk>\d+)/$',
                       #     'zds.tutorialv2.views.invalid_tutorial'),
                       url(r'^validation/historique/(?P<content_slug>.+)/$',
                           'zds.tutorialv2.views.history_validation'),
                       # url(r'^activation_js/$',
                       #     'zds.tutorialv2.views.activ_js'),
                       # # Reactions
                       # url(r'^message/editer/$',
                       #     'zds.tutorialv2.views.edit_note'),
                       # url(r'^message/nouveau/$', 'zds.tutorialv2.views.answer'),
                       # url(r'^message/like/$', 'zds.tutorialv2.views.like_note'),
                       # url(r'^message/dislike/$',
                       #     'zds.tutorialv2.views.dislike_note'),
                       #
                       # # Moderation
                       # url(r'^resolution_alerte/$',
                       #     'zds.tutorialv2.views.solve_alert'),

                       # Help
                       url(r'^aides/$',
                           TutorialWithHelp.as_view()),
                       )
"""
