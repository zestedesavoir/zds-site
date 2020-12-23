from django.contrib.auth.models import Group, User
from django.db import models
from django.utils.translation import gettext_lazy as _


class GroupContact(models.Model):
    """
    Groups displayed in contact page and their informations.
    """

    class Meta:
        verbose_name = _("Groupe de la page de contact")
        verbose_name_plural = _("Groupes de la page de contact")

    group = models.OneToOneField(Group, verbose_name=_("Groupe d'utilisateur"), on_delete=models.CASCADE)
    name = models.CharField(_("Nom (ex: Le staff)"), max_length=32, unique=True)
    description = models.TextField(_("Description (en markdown)"), blank=True, null=True)
    email = models.EmailField(_("Adresse mail du groupe"), blank=True, null=True)
    persons_in_charge = models.ManyToManyField(User, verbose_name=_("Responsables"), blank=True)
    position = models.PositiveSmallIntegerField(_("Position dans la page"), unique=True)

    def __str__(self):
        return self.name
