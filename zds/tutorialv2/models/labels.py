from django.db import models


class Label(models.Model):
    """
    This model represents the labels used to highlight the quality of publications.
    Here few example of labels: "well-written", "comprehensive", "well-researched", etc.
    """

    class Meta:
        verbose_name = "Label"
        verbose_name_plural = "Labels"

    name = models.CharField("Nom", max_length=80)
    description = models.TextField("Description", blank=True)
    position = models.IntegerField("Position", default=0, db_index=True)
    slug = models.SlugField(max_length=80, unique=True)

    def __str__(self):
        return self.name
