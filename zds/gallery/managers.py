from django.db import models
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Coalesce


class GalleryManager(models.Manager):
    def annotated_gallery(self):
        """Annotate gallery with

        - ``linked_content``, which contains the pk of the associated content if any ;
        - ``image_count``, which contains the number of images.

        :rtype: QuerySet
        """
        from zds.gallery.models import Image
        from zds.tutorialv2.models.database import PublishableContent

        linked_content = PublishableContent.objects.filter(gallery__pk=OuterRef("pk")).values("pk")

        images = (
            Image.objects.filter(gallery__pk=OuterRef("pk"))
            .values("gallery")
            .annotate(count=Count("pk"))
            .values("count")
        )

        return self.annotate(linked_content=Subquery(linked_content)).annotate(
            image_count=Coalesce(Subquery(images), 0)
        )

    def galleries_of_user(self, user):
        """Get galleries of user, and annotate with an extra field ``user_mode`` (which contains R or W)

        :param user:  the user
        :type user: zds.member.models.User
        :rtype: QuerySet
        """

        from zds.gallery.models import UserGallery

        user_galleries = UserGallery.objects.filter(user=user).prefetch_related("gallery").values("gallery__pk")
        user_mode = UserGallery.objects.filter(user=user, gallery__pk=OuterRef("pk"))
        return (
            self.annotated_gallery()
            .filter(pk__in=user_galleries)
            .annotate(user_mode=Subquery(user_mode.values("mode")))
        )
