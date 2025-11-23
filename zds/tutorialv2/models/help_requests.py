from django.db import models
from easy_thumbnails.fields import ThumbnailerImageField

from zds.utils import old_slugify
from zds.utils.models import image_path_help


class HelpWriting(models.Model):
    """Tutorial Help"""

    class Meta:
        verbose_name = "Aide à la rédaction"
        verbose_name_plural = "Aides à la rédaction"

    # A name for this help
    title = models.CharField("Name", max_length=20, null=False)
    slug = models.SlugField(max_length=20)

    # tablelabel: Used for the accessibility "This tutoriel need help for writing"
    tablelabel = models.CharField("TableLabel", max_length=150, null=False)

    # The image to use to illustrate this role
    image = ThumbnailerImageField(upload_to=image_path_help)

    def __str__(self):
        """Textual Help Form."""
        return self.title

    def save(self, *args, **kwargs):
        self.slug = old_slugify(self.title)
        super().save(*args, **kwargs)
