from django.db import models


class UserGalleryManager(models.Manager):
    def galleries_of_user(self, user):
        user_galleries = self.filter(user=user).prefetch_related('gallery').all()
        return [g.gallery for g in user_galleries]
