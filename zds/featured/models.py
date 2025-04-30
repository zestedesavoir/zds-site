from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from zds.featured.managers import FeaturedMessageManager, FeaturedRequestedManager, FeaturedResourceManager
from zds.member.models import User


class FeaturedResource(models.Model):
    """
    A FeaturedResource is a link to a resource that is featured by the Staff
    It displays 3 main informations:

    - A background picture
    - A title
    - The author(s) of the resource

    Currently, the five newer FeaturedResource are displayed on the front page.
    """

    class Meta:
        verbose_name = _("Une")
        verbose_name_plural = _("Unes")

    title = models.CharField(_("Titre"), max_length=80)
    type = models.CharField(_("Type"), max_length=80)
    authors = models.CharField(_("Auteurs"), max_length=100, blank=True, default="")
    image_url = models.CharField(_("URL de l'image à la une"), max_length=2000, null=False, blank=False)
    url = models.CharField(_("URL de la une"), max_length=2000, null=False, blank=False)
    pubdate = models.DateTimeField(_("Date de publication"), blank=False, null=False, db_index=True)

    objects = FeaturedResourceManager()

    def __str__(self):
        """Textual form of a featured resource."""
        return self.title


FEATUREABLES_TYPES = ["content", "topic"]  # keep order!

FEATUREABLES = {
    "content": {"name": "CONTENT", "verbose_name": _("Contenu")},
    "topic": {"name": "TOPIC", "verbose_name": _("Sujet")},
}

FEATUREABLE_TYPE_CHOICES = [(FEATUREABLES[a]["name"], FEATUREABLES[a]["verbose_name"]) for a in FEATUREABLES_TYPES]


class FeaturedRequested(models.Model):
    """
    This class hold votes for a topic or content to be featured.
    """

    class Meta:
        verbose_name = _("Mise en avant souhaitée")
        verbose_name_plural = _("Mises en avant souhaitées")

    content_type = models.ForeignKey(ContentType, verbose_name=_("Type de l'objet"), on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True, verbose_name=_("Id de l'objet"))
    content_object = GenericForeignKey("content_type", "object_id")

    users_voted = models.ManyToManyField(User, verbose_name=_("Auteur(s)"), db_index=True, blank=True)

    type = models.CharField(
        max_length=10, choices=FEATUREABLE_TYPE_CHOICES, verbose_name=_("Type de l'objet"), db_index=True
    )

    rejected = models.BooleanField(default=False, verbose_name=_("Est rejeté"))
    rejected_for_good = models.BooleanField(default=False, verbose_name=_("Est rejeté pour de bon"))

    featured = models.ForeignKey(
        FeaturedResource, verbose_name=_("Une"), blank=True, null=True, on_delete=models.SET_NULL
    )

    objects = FeaturedRequestedManager()

    def toggle(self, user):
        """Toogle featured request for user. Do not reject the vote anymore.

        :param user: the user
        :type user: User
        :return: tuple of the form (user has voted, number of votes)
        :rtype: (bool, int)
        """
        new_value = False
        new_count = self.users_voted.count()

        if self.users_voted.filter(pk=user.pk).exists():
            self.users_voted.remove(user)
            new_count -= 1
        else:
            self.users_voted.add(user)
            new_count += 1
            new_value = True

        if self.rejected:
            self.rejected = False
            self.save()

        return new_value, new_count

    def __str__(self):
        return f'<RequestFeatured for "{self.content_object.title}">'


class FeaturedMessage(models.Model):
    """
    The Featured Message is a simple one-line information on the home page.
    This message is divided in three parts:

    - The hook : displayed in bold, it shows the topic of the message (i.e.: "New", "Warning", "Info", ...)
    - The message : the info message itself (i.e.: "The site will be down for maintenance tomorrow")
    - The "tell me more" url : A tell me more button linking to a page giving more details

    Only the message is mandatory.
    """

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

    hook = models.CharField(_("Accroche"), max_length=100, blank=True, null=True)
    message = models.CharField(_("Message"), max_length=255)
    url = models.CharField(_("URL du message"), max_length=2000, blank=True, null=True)

    objects = FeaturedMessageManager()

    def __str__(self):
        """Textual form of a featured message."""
        return self.message
