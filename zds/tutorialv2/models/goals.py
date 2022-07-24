from django.db import models


class Goal(models.Model):
    """
    This model represents the categories used for the goal-based classification of publications.
    The goals are categories like "understand", "discover", "learn", "give an opinion", etc.
    They are thus distinct from the thematic categories and subcategories (physics,
    computer science, etc.) or the tags (even more precise).
    """

    class Meta:
        verbose_name = "Objectif"
        verbose_name_plural = "Objectifs"

    name = models.CharField("Nom", max_length=80)
    description = models.TextField("Description", blank=True)
    position = models.IntegerField("Position", default=0, db_index=True)
    slug = models.SlugField(max_length=80, unique=True)

    def __str__(self):
        return self.name
