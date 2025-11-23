from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class TemplatableContentModelMixin:
    content_type_attribute = "content_type"

    @property
    def is_article(self):
        """
        :return: ``True`` if it is an article, ``False`` otherwise.
        :rtype: bool
        """
        return getattr(self, self.content_type_attribute) == "ARTICLE"

    @property
    def is_tutorial(self):
        """
        :return: ``True`` if it is an article, ``False`` otherwise.
        :rtype: bool
        """
        return getattr(self, self.content_type_attribute) == "TUTORIAL"

    @property
    def is_opinion(self):
        """
        :return: ``True`` if it is an article, ``False`` otherwise.
        :rtype: bool
        """
        return getattr(self, self.content_type_attribute) == "OPINION"

    def get_absolute_url(self, version=None) -> str:
        """
        If no version is given, return the URL to the draft page of the content.
        Otherwise, return the URL to the page of the specified version.
        """
        route_parameters = {"pk": self.pk, "slug": self.slug}
        if version and version != self.sha_draft:
            route_parameters["version"] = version
            return reverse("content:view-version", kwargs=route_parameters)
        else:
            return reverse("content:view", kwargs=route_parameters)

    @property
    def validation_message_title(self):
        """
        Generate validation private message title

        :return: the generated title
        """
        if self.is_article:
            return _("Suivi de l'article {}").format(self.title)
        if self.is_tutorial:
            return _("Suivi du tutoriel {}").format(self.title)
        if self.is_opinion:
            return _("Suivi du billet {}").format(self.title)

    def textual_type(self):
        """Create a internationalized string with the human readable type of this content e.g The Article

        :return: internationalized string
        :rtype: str
        """
        if self.is_article:
            return _("L'Article")
        elif self.is_tutorial:
            return _("Le Tutoriel")
        elif self.is_opinion:
            return _("Le Billet")
        else:
            return _("Le Contenu")


class OnlineLinkableContentMixin:
    content_type_attribute = "content_type"

    def get_absolute_url_online(self):
        """
        :return: the URL of the published content
        :rtype: str
        """
        content_type = getattr(self, self.content_type_attribute).lower()
        return reverse(f"{content_type}:view", kwargs={"pk": self.content_pk, "slug": self.content_public_slug})
