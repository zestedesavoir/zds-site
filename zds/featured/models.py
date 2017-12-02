from django.db import models
from django.utils.translation import ugettext_lazy as _

from zds.featured.managers import FeaturedResourceManager, FeaturedMessageManager


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
        verbose_name = _('Une')
        verbose_name_plural = _('Unes')

    title = models.CharField(_('Titre'), max_length=80)
    type = models.CharField(_('Type'), max_length=80)
    authors = models.CharField(_('Auteurs'), max_length=100, blank=True, default='')
    image_url = models.CharField(
        _('URL de l\'image à la une'), max_length=2000, null=False, blank=False
    )
    url = models.CharField(
        _('URL de la une'), max_length=2000, null=False, blank=False
    )
    pubdate = models.DateTimeField(_('Date de publication'), blank=False, null=False, db_index=True)

    objects = FeaturedResourceManager()

    def __str__(self):
        """Textual form of a featured resource."""
        return self.title


class FeaturedMessage(models.Model):
    """
        The Featured Message is a simple one-line information on the home page.
        This message is divided in three parts:
            - The hook : displayed in bold, it shows the topic of the message (i.e.: "New", "Warning", "Info", ...)
            - The message : the info message itself (i.e.: "The site will be down for maintenance tomorrow")
            - The "tell me more" url : A tell me more button linking to a page giving more details
        All those elements are facultative.
    """

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')

    hook = models.CharField(_('Accroche'), max_length=100, blank=True, null=True)
    message = models.CharField(_('Message'), max_length=255, blank=True, null=True)
    url = models.CharField(_('URL du message'), max_length=2000, blank=True, null=True)

    objects = FeaturedMessageManager()

    def __str__(self):
        """Textual form of a featured message."""
        return self.message
