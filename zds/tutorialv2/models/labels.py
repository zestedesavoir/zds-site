from django.db import models
from django.urls import reverse


class Label(models.Model):
    """
    This model represents the labels used to highlight the quality of publications.
    Here few example of labels: "well-written", "comprehensive", "well-researched", etc.
    """

    class Meta:
        verbose_name = "Label"
        verbose_name_plural = "Labels"

    name = models.CharField("Nom", max_length=80, help_text="Nom du label")
    description = models.TextField("Description", blank=True, help_text="Description du label")
    slug = models.SlugField(
        max_length=80,
        unique=True,
        help_text="L'URL pour voir les contenus associés au label est de la forme contenus/labels/slug",
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("content:view-labels", args=[self.slug])
