import uuid
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2.models import SHAREABLE_LINK_TYPES
from zds.tutorialv2.models.database import PublishableContent


class ShareableLinkQuerySet(models.QuerySet):
    def for_content(self, content):
        return self.filter(content=content)

    def active_and_for_content(self, content):
        return self.for_content(content).active()

    def expired_and_for_content(self, content):
        return self.for_content(content).expired()

    def inactive_and_for_content(self, content):
        return self.for_content(content).inactive()

    def active(self):
        pivot_date = datetime.now()
        return self.filter(Q(active=True) & (Q(expiration__gte=pivot_date) | Q(expiration=None)))

    def expired(self):
        pivot_date = datetime.now()
        return self.filter(active=True, expiration__lt=pivot_date)

    def inactive(self):
        return self.filter(active=False)


class ShareableLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(PublishableContent, verbose_name="Contenu", on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    expiration = models.DateTimeField(null=True)
    description = models.CharField(default=_("Lien de partage"), max_length=150)
    # Types
    # DRAFT: always points to the last draft version
    # BETA: always points to the last beta version
    type = models.CharField(max_length=10, choices=SHAREABLE_LINK_TYPES, default="DRAFT")

    objects = ShareableLinkQuerySet.as_manager()

    def full_url(self):
        return settings.ZDS_APP["site"]["url"] + reverse("content:shareable-link", kwargs={"id": self.id})

    def deactivate(self):
        self.active = False
        self.save()

    def reactivate(self):
        self.active = True
        self.save()
