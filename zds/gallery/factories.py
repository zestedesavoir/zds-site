import contextlib
from pathlib import Path

import factory

from zds.gallery.models import Image, Gallery, UserGallery
from zds.utils import slugify


# Don't try to directly use UserFactory, this didn't create Profile then
# don't work!
class ImageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Image

    title = factory.Sequence("titre de l'image {0}".format)
    slug = factory.LazyAttribute(lambda o: '{0}'.format(slugify(o.title)))
    legend = factory.Sequence("legende de l'image {0}".format)
    physical = factory.django.ImageField(color='blue')

    @classmethod
    def _prepare(cls, create, **kwargs):
        gallery = kwargs.pop('gallery', None)
        if gallery is not None:
            image = super(ImageFactory, cls)._prepare(create, gallery=gallery, **kwargs)
        else:
            image = None
        return image


class GalleryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Gallery

    title = factory.Sequence('titre de la gallerie {0}'.format)
    subtitle = factory.Sequence('Sous-titre de la gallerie {0}'.format)
    slug = factory.LazyAttribute(lambda o: '{0}'.format(slugify(o.title)))

    @classmethod
    def _prepare(cls, create, **kwargs):
        gal = super(GalleryFactory, cls)._prepare(create, **kwargs)
        with contextlib.suppress(OSError):
            Path(gal.get_gallery_path()).mkdir(parents=True)
        return gal


class UserGalleryFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserGallery

    mode = 'W'

    @classmethod
    def _prepare(cls, create, **kwargs):
        user = kwargs.pop('user', None)
        gallery = kwargs.pop('gallery', None)
        if user is not None and gallery is not None:
            user_gal = super(UserGalleryFactory, cls)._prepare(create, user=user, gallery=gallery, **kwargs)
        else:
            user_gal = None
        return user_gal
