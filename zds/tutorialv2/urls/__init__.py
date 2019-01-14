from django.conf.urls import include, url

urlpatterns = [
    url(r'^contenus/', include(('zds.tutorialv2.urls.urls_contents', 'zds.tutorialv2'), namespace='content')),
    url(r'^validations/', include(('zds.tutorialv2.urls.urls_validations', 'zds.tutorialv2'), namespace='validation')),
    url(r'^tutoriels/', include(('zds.tutorialv2.urls.urls_tutorials', 'zds.tutorialv2'), namespace='tutorial')),
    url(r'^billets/', include(('zds.tutorialv2.urls.urls_opinions', 'zds.tutorialv2'), namespace='opinion')),
    url(r'^articles/', include(('zds.tutorialv2.urls.urls_articles', 'zds.tutorialv2'), namespace='article')),
    url(r'^bibliotheque/', include(('zds.tutorialv2.urls.urls_publications', 'zds.tutorialv2'),
                                   namespace='publication')),
]
