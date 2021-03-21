from django.core import validators


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
