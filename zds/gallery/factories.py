import contextlib

import factory

from zds.gallery.models import Image, Gallery, UserGallery
from zds.utils import old_slugify


# Don't try to directly use UserFactory, this didn't create Profile then
# don't work!
class ImageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Image

    title = factory.Sequence("titre de l'image {}".format)
    slug = factory.LazyAttribute(lambda o: "{}".format(old_slugify(o.title)))
    legend = factory.Sequence("legende de l'image {}".format)
    physical = factory.django.ImageField(color="blue")

    @classmethod
    def _prepare(cls, create, **kwargs):
        gallery = kwargs.pop("gallery", None)
        if gallery is not None:
            image = super()._prepare(create, gallery=gallery, **kwargs)
        else:
            image = None
        return image


class GalleryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Gallery

    title = factory.Sequence("titre de la gallerie {}".format)
    subtitle = factory.Sequence("Sous-titre de la gallerie {}".format)
    slug = factory.LazyAttribute(lambda o: "{}".format(old_slugify(o.title)))

    @classmethod
    def _prepare(cls, create, **kwargs):
        gal = super()._prepare(create, **kwargs)
        with contextlib.suppress(OSError):
            gal.get_gallery_path().mkdir(parents=True)
        return gal


class UserGalleryFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserGallery

    mode = "W"

    @classmethod
    def _prepare(cls, create, **kwargs):
        user = kwargs.pop("user", None)
        gallery = kwargs.pop("gallery", None)
        if user is not None and gallery is not None:
            user_gal = super()._prepare(create, user=user, gallery=gallery, **kwargs)
        else:
            user_gal = None
        return user_gal
