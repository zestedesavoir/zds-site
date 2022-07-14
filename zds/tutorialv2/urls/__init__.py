from django.urls import include, path

urlpatterns = [
    path("contenus/", include(("zds.tutorialv2.urls.urls_contents", "zds.tutorialv2.urls"), namespace="content")),
    path(
        "validations/",
        include(("zds.tutorialv2.urls.urls_validations", "zds.tutorialv2.urls"), namespace="validation"),
    ),
    path("tutoriels/", include(("zds.tutorialv2.urls.urls_tutorials", "zds.tutorialv2.urls"), namespace="tutorial")),
    path("billets/", include(("zds.tutorialv2.urls.urls_opinions", "zds.tutorialv2.urls"), namespace="opinion")),
    path("articles/", include(("zds.tutorialv2.urls.urls_articles", "zds.tutorialv2.urls"), namespace="article")),
    path(
        "bibliotheque/",
        include(("zds.tutorialv2.urls.urls_publications", "zds.tutorialv2.urls"), namespace="publication"),
    ),
]
