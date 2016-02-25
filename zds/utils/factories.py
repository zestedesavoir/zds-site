# coding: utf-8
from zds.utils.models import HelpWriting
from zds.utils import slugify
from zds.settings import BASE_DIR, MEDIA_ROOT
from shutil import copyfile
from os.path import basename, join

import factory


class HelpWritingFactory(factory.DjangoModelFactory):
    class Meta:
        model = HelpWriting

    title = factory.Sequence("titre de l\'image {0}".format)
    slug = factory.LazyAttribute(lambda o: "{0}".format(slugify(o.title)))
    tablelabel = factory.LazyAttribute(lambda n: "Besoin de " + n.title)

    @classmethod
    def _prepare(cls, create, **kwargs):
        help_writing = super(HelpWritingFactory, cls)._prepare(create, **kwargs)
        image_path = kwargs.pop('image_path', None)
        fixture_image_path = kwargs.pop('fixture_image_path', None)

        if fixture_image_path is not None:
            image_path = join(BASE_DIR, "fixtures", fixture_image_path)

        if image_path is not None:
            copyfile(image_path, join(MEDIA_ROOT, basename(image_path)))
            help_writing.image = basename(image_path)
            help_writing.save()

        return help_writing

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        kwargs.pop('image_path', None)
        kwargs.pop('fixture_image_path', None)

        return super(HelpWritingFactory, cls)._create(target_class, *args, **kwargs)
