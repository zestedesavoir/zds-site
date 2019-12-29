from os.path import basename, join
from shutil import copyfile

import factory

from django.conf import settings

from zds.utils.models import HelpWriting, Category
from zds.utils import old_slugify


class HelpWritingFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a HelpWriting.
    """

    class Meta:
        model = HelpWriting

    title = factory.Sequence("titre de l'image {}".format)
    slug = factory.LazyAttribute(lambda o: "{}".format(old_slugify(o.title)))
    tablelabel = factory.LazyAttribute(lambda n: "Besoin de " + n.title)

    @classmethod
    def _generate(cls, create, attrs):
        # These parameters are only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (they are removed from attrs).
        image_path = attrs.pop("image_path", None)
        fixture_image_path = attrs.pop("fixture_image_path", None)

        help_writing = super()._generate(create, attrs)

        if fixture_image_path is not None:
            image_path = join(settings.BASE_DIR, "fixtures", fixture_image_path)

        if image_path is not None:
            copyfile(image_path, settings.MEDIA_ROOT / basename(image_path))
            help_writing.image = basename(image_path)
            help_writing.save()

        return help_writing

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        kwargs.pop("image_path", None)
        kwargs.pop("fixture_image_path", None)

        return super()._create(target_class, *args, **kwargs)


class CategoryFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a Category.
    """

    class Meta:
        model = Category

    title = factory.Sequence("Ma catégorie No{}".format)
    slug = factory.Sequence("category{}".format)
