import factory

from zds.gallery.models import Image, Gallery, UserGallery
from zds.utils import slugify


# Don't try to directly use UserFactory, this didn't create Profile then
# don't work!
class ImageFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Image

    title = factory.Sequence(lambda n: u"titre de l\'image {0}".format(n))
    slug = factory.LazyAttribute(lambda o: "{0}".format(slugify(o.title)))
    legend = factory.Sequence(lambda n: u"legende de l'image {0}".format(n))
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
    FACTORY_FOR = Gallery

    title = factory.Sequence(lambda n: u"titre de la gallerie {0}".format(n))
    subtitle = factory.Sequence(lambda n: u"Sous-titre de la gallerie {0}".format(n))
    slug = factory.LazyAttribute(lambda o: "{0}".format(slugify(o.title)))


class UserGalleryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = UserGallery

    mode = "W"

    @classmethod
    def _prepare(cls, create, **kwargs):
        user = kwargs.pop('user', None)
        gallery = kwargs.pop('gallery', None)
        if user is not None and gallery is not None:
            ug = super(UserGalleryFactory, cls)._prepare(create, user=user, gallery=gallery, **kwargs)
        else:
            ug = None
        return ug
