import contextlib

import factory

from zds.gallery.models import Gallery, Image, UserGallery
from zds.utils import old_slugify


class ImageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Image

    title = factory.Sequence("titre de l'image {}".format)
    slug = factory.LazyAttribute(lambda o: f"{old_slugify(o.title)}")
    legend = factory.Sequence("legende de l'image {}".format)
    physical = factory.django.ImageField(color="blue")

    @classmethod
    def _generate(cls, create, attrs):
        # Only creates the Image if a Gallery is associated
        gallery = attrs.get("gallery", None)
        if gallery is not None:
            image = super()._generate(create, attrs)
        else:
            image = None
        return image


class GalleryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Gallery

    title = factory.Sequence("titre de la gallerie {}".format)
    subtitle = factory.Sequence("Sous-titre de la gallerie {}".format)
    slug = factory.LazyAttribute(lambda o: f"{old_slugify(o.title)}")

    @classmethod
    def _generate(cls, create, attrs):
        gallery = super()._generate(create, attrs)
        with contextlib.suppress(OSError):
            gallery.get_gallery_path().mkdir(parents=True)
        return gallery


class UserGalleryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserGallery

    mode = "W"

    @classmethod
    def _generate(cls, create, attrs):
        # Only creates the UserGallery if a User and a Gallery are associated
        user = attrs.get("user", None)
        gallery = attrs.get("gallery", None)
        if user is not None and gallery is not None:
            user_gallery = super()._generate(create, attrs)
        else:
            user_gallery = None
        return user_gallery
