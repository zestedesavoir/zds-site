from django.conf import settings
from django.core import validators

from zds.utils import VALID_SLUG, old_slugify
from zds.utils.uuslug_wrapper import slugify


def with_svg_validator(value):
    """
    allows all PIL extensions and svg, if you want to add svgz here you will also need to configure
    THUMBNAIL_PRESERVE_EXTENSIONS setting
    Such a function is used as reference in fields ``validators=[with_svg_validator]
    :param value: value to validate
    :return: the validated value
    """
    return validators.FileExtensionValidator(allowed_extensions=validators.get_available_image_extensions() + ["svg"])(
        value
    )


def slugify_raise_on_invalid(title, use_old_slugify=False):
    """
    use uuslug to generate a slug but if the title is incorrect (only special chars or slug is empty), an exception
    is raised.

    :param title: to be slugified title
    :type title: str
    :param use_old_slugify: use the function `slugify()` defined in zds.utils instead of the one in uuslug. Usefull \
    for retro-compatibility with the old article/tutorial module, SHOULD NOT be used for the new one !
    :type use_old_slugify: bool
    :raise InvalidSlugError: on incorrect slug
    :return: the slugified title
    :rtype: str
    """

    if not isinstance(title, str):
        raise InvalidSlugError("", source=title)
    if not use_old_slugify:
        slug = slugify(title)
    else:
        slug = old_slugify(title)

    if not check_slug(slug):
        raise InvalidSlugError(slug, source=title)

    return slug


class InvalidSlugError(ValueError):
    """Error raised when a slug is invalid. Argument is the slug that cause the error.

    ``source`` can also be provided, being the sentence from witch the slug was generated, if any.
    ``had_source`` is set to ``True`` if the source is provided.

    """

    def __init__(self, *args, **kwargs):
        self.source = ""
        self.had_source = False

        if "source" in kwargs:
            self.source = kwargs.pop("source")
            self.had_source = True

        super().__init__(*args, **kwargs)


def check_slug(slug):
    """
    If the title is incorrect (only special chars so slug is empty).

    :param slug: slug to test
    :type slug: str
    :return: `True` if slug is valid, false otherwise
    :rtype: bool
    """

    if not VALID_SLUG.match(slug):
        return False

    if not slug.replace("-", "").replace("_", ""):
        return False

    if len(slug) > settings.ZDS_APP["content"]["maximum_slug_size"]:
        return False

    return True
