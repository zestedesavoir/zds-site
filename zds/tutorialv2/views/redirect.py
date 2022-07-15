from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.utils import search_container_or_404


class RedirectContentSEO(RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        """Redirects the user to the new url"""
        obj = get_object_or_404(PublishableContent, old_pk=int(kwargs.get("pk")), type="TUTORIAL")
        if not obj.in_public():
            raise Http404("Aucun contenu public n'est disponible avec cet identifiant.")
        kwargs["parent_container_slug"] = str(kwargs["p2"]) + "_" + kwargs["parent_container_slug"]
        kwargs["container_slug"] = str(kwargs["p3"]) + "_" + kwargs["container_slug"]
        obj = search_container_or_404(obj.load_version(public=True), kwargs)

        return obj.get_absolute_url_online()


class RedirectOldBetaTuto(RedirectView):
    """
    allows to redirect /tutoriels/beta/old_pk/slug to /contenus/beta/new_pk/slug
    """

    permanent = True

    def get_redirect_url(self, **kwargs):
        tutorial = PublishableContent.objects.filter(type="TUTORIAL", old_pk=kwargs["pk"]).first()
        if tutorial is None or tutorial.sha_beta is None or tutorial.sha_beta == "":
            raise Http404("Aucun contenu en bêta trouvé avec cet ancien identifiant.")
        return tutorial.get_absolute_url_beta()


class RedirectOldContentOfAuthor(RedirectView):
    """
    allows to redirect the old lists of users' tutorials/articles/opinions (with
    pks) to the new ones (with usernames and different root).
    """

    permanent = True
    type = None

    def get_redirect_url(self, **kwargs):
        user = User.objects.filter(pk=int(kwargs["pk"])).first()
        route = None

        if not user:
            raise Http404("Cet utilisateur est inconnu dans le système")

        if self.type == "TUTORIAL":
            route = "tutorial:find-tutorial"
        elif self.type == "ARTICLE":
            route = "article:find-article"
        elif self.type == "OPINION":
            route = "opinion:find-opinion"

        if not route:
            raise Http404("Ce type de contenu est inconnu dans le système")

        return reverse(route, args=[user.username])
