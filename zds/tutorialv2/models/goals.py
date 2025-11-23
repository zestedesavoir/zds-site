from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class Goal(models.Model):
    """
    This model represents the categories used for the goal-based classification of publications.
    The goals are categories like "understand", "discover", "learn", "give an opinion", etc.
    They are thus distinct from the thematic categories and subcategories (physics,
    computer science, etc.) or the tags (even more precise).
    """

    SLUG_UNCLASSIFIED = "non-classes"

    class Meta:
        verbose_name = "Objectif"
        verbose_name_plural = "Objectifs"

    name = models.CharField("Nom", max_length=80)
    description = models.TextField("Description", blank=True)
    position = models.IntegerField("Position", default=0, db_index=True)
    slug = models.SlugField(
        max_length=80,
        unique=True,
        validators=[
            RegexValidator("^" + SLUG_UNCLASSIFIED + "$", message=_("Ce slug est réservé."), inverse_match=True)
        ],
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("content:view-goals") + "?" + self.slug
