from django.conf.urls import include, url

urlpatterns = [
    url(r'^contenus/', include('zds.tutorialv2.urls.urls_contents', namespace='content')),
    url(r'^validations/', include('zds.tutorialv2.urls.urls_validations', namespace='validation')),
    url(r'^tutoriels/', include('zds.tutorialv2.urls.urls_tutorials', namespace='tutorial')),
    url(r'^billets/', include('zds.tutorialv2.urls.urls_opinions', namespace='opinion')),
    url(r'^articles/', include('zds.tutorialv2.urls.urls_articles', namespace='article')),
    url(r'^bibliotheque/', include('zds.tutorialv2.urls.urls_publications', namespace='publication')),
]
