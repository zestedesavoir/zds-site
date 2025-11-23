from django.utils.translation import gettext_lazy as _

CONTENT_TYPES = (
    # Configuration of content names
    # name                  Type ID (unique and uppercase)
    # verbose_name          User-friendly type name
    # verbose_name_plural   User-friendly pluralized type name
    # category_name         User-friendly category name which contains this content
    # requires_validation   Boolean; whether this content has to be validated before publication
    # beta                  Boolean; True if the content can be in beta
    {
        "name": "TUTORIAL",
        "verbose_name": "tutoriel",
        "verbose_name_plural": "tutoriels",
        "category_name": "tutoriel",
        "requires_validation": True,
        "beta": True,
    },
    {
        "name": "ARTICLE",
        "verbose_name": "article",
        "verbose_name_plural": "articles",
        "category_name": "article",
        "requires_validation": True,
        "beta": True,
    },
    {
        "name": "OPINION",
        "verbose_name": "billet",
        "verbose_name_plural": "billets",
        "category_name": "tribune",
        "requires_validation": False,
        "beta": False,
    },
)

PICK_OPERATIONS = (
    ("REJECT", _("Rejeté")),
    ("NO_PICK", _("Non choisi")),
    ("PICK", _("Choisi")),
    ("REMOVE_PUB", _("Dépublier définitivement")),
)

# a list of contents which have to be validated before publication
CONTENT_TYPES_REQUIRING_VALIDATION = [content["name"] for content in CONTENT_TYPES if content["requires_validation"]]

# a list of contents which can be in beta
CONTENT_TYPES_BETA = [content["name"] for content in CONTENT_TYPES if content["beta"]]

TYPE_CHOICES = [(content["name"], content["verbose_name"].capitalize()) for content in CONTENT_TYPES]

# a single list with all types
CONTENT_TYPE_LIST = [type_[0] for type_ in TYPE_CHOICES]

TYPE_CHOICES_DICT = dict(TYPE_CHOICES)

STATUS_CHOICES = (
    ("PENDING", _("En attente d'un validateur")),
    ("PENDING_V", _("En cours de validation")),
    ("ACCEPT", _("Publié")),
    ("REJECT", _("Rejeté")),
    ("CANCEL", _("Annulé")),
)
