from django.urls import path

from zds.featured.views import (
    FeaturedResourceList,
    FeaturedResourceCreate,
    FeaturedResourceUpdate,
    FeaturedResourceDeleteDetail,
    FeaturedResourceDeleteList,
    FeaturedMessageCreateUpdate,
    FeaturedRequestedList,
    FeaturedRequestedUpdate,
)

app_name = "featured"

urlpatterns = [
    path("", FeaturedResourceList.as_view(), name="resource-list"),
    path("unes/creer/", FeaturedResourceCreate.as_view(), name="resource-create"),
    path("unes/modifier/<int:pk>/", FeaturedResourceUpdate.as_view(), name="resource-update"),
    path("unes/supprimer/<int:pk>/", FeaturedResourceDeleteDetail.as_view(), name="resource-delete"),
    path("unes/supprimer/", FeaturedResourceDeleteList.as_view(), name="resource-list-delete"),
    path("message/modifier/", FeaturedMessageCreateUpdate.as_view(), name="message-create"),
    path("unes/requetes/", FeaturedRequestedList.as_view(), name="resource-requests"),
    path("unes/requete/<int:pk>/", FeaturedRequestedUpdate.as_view(), name="resource-request-update"),
]
