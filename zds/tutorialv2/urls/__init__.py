from django.urls import include, re_path

urlpatterns = [
    re_path(r'^contenus/', include(('zds.tutorialv2.urls.urls_contents',
                                    'zds.tutorialv2'), namespace='content')),
    re_path(r'^validations/', include(('zds.tutorialv2.urls.urls_validations',
                                       'zds.tutorialv2'), namespace='validation')),
    re_path(r'^tutoriels/', include(('zds.tutorialv2.urls.urls_tutorials',
                                     'zds.tutorialv2'), namespace='tutorial')),
    re_path(r'^billets/', include(('zds.tutorialv2.urls.urls_opinions',
                                   'zds.tutorialv2'), namespace='opinion')),
    re_path(r'^articles/', include(('zds.tutorialv2.urls.urls_articles',
                                    'zds.tutorialv2'), namespace='article')),
    re_path(r'^bibliotheque/', include(('zds.tutorialv2.urls.urls_publications', 'zds.tutorialv2'),
                                       namespace='publication')),
]
