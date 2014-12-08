# coding: utf-8
from zds.utils.models import HelpWriting
from zds.utils import slugify
from zds.settings import SITE_ROOT, MEDIA_ROOT
from shutil import copyfile
from os.path import basename, join

import factory


class HelpWritingFactory(factory.DjangoModelFactory):
    FACTORY_FOR = HelpWriting

    title = factory.Sequence(lambda n: u"titre de l\'image {0}".format(n))
    slug = factory.LazyAttribute(lambda o: "{0}".format(slugify(o.title)))
    tablelabel = factory.LazyAttribute(lambda n: u"Besoin de " + n.title)

    @classmethod
    def _prepare(cls, create, **kwargs):
        a = super(HelpWritingFactory, cls)._prepare(create, **kwargs)
        image_path = kwargs.pop('image_path', None)
        fixture_image_path = kwargs.pop('fixture_image_path', None)

        if fixture_image_path is not None:
            image_path = join(SITE_ROOT, "fixtures", fixture_image_path)

        if image_path is not None:
            copyfile(image_path, join(MEDIA_ROOT, basename(image_path)))
            a.image = basename(image_path)
            a.save()

        return a

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        kwargs.pop('image_path', None)
        kwargs.pop('fixture_image_path', None)

        return super(HelpWritingFactory, cls)._create(target_class, *args, **kwargs)
