from collections import OrderedDict, defaultdict

from django import template
from django.conf import settings
from django.db.models import Count, Q

from zds.forum.models import Forum
from zds.tutorialv2.models.database import PublishedContent
from zds.utils.models import CategorySubCategory, Tag

register = template.Library()


@register.filter("topbar_forum_categories")
def topbar_forum_categories(user):
    max_tags = settings.ZDS_APP["forum"]["top_tag_max"]
    forums = (
        Forum.objects.filter(Q(groups__isnull=True) | Q(groups__isnull=False, groups__in=user.groups.all()))
        .select_related("category")
        .distinct()
        .all()
    )

    cats = defaultdict(list)
    for forum in forums:
        cats[forum.category.position].append(forum)

    sorted_cats = sorted(cats)
    topbar_cats = [(cats[cat][0].category.title, cats[cat][0].category.slug, cats[cat]) for cat in sorted_cats]

    excluded_tags = settings.ZDS_APP["forum"]["top_tag_exclu"]
    tags_by_popularity = (
        Tag.objects.filter(topic__forum__in=forums)
        .annotate(count_topic=Count("topic"))
        .exclude(title__in=excluded_tags)
        .order_by("-count_topic")
        .all()[:max_tags]
    )
    return {"tags": tags_by_popularity, "categories": topbar_cats}


@register.filter("topbar_publication_categories")
def topbar_publication_categories(_type):
    """Get all the categories and their related subcategories associated with existing publications.
    The result is sorted by alphabetic order.

    :param _type: type of the publication
    :type _type: str
    :return: a dictionary, with the title being the name of the category and the publication a list of subcategories,
    Each of these are stored in a tuple of the form ``title, slug``.
    :rtype: OrderedDict
    """

    _type = _type if isinstance(_type, list) else [_type]
    tags = PublishedContent.objects.get_top_tags(_type, limit=settings.ZDS_APP["forum"]["top_tag_max"])

    subcategories_contents = (
        PublishedContent.objects.filter(must_redirect=False)
        .filter(content_type__in=_type)
        .values("content__subcategory")
        .all()
    )

    # get parent categories of subcategories from PublishedContent
    categories_from_subcategories = (
        CategorySubCategory.objects.filter(is_main=True)
        .filter(subcategory__in=subcategories_contents)
        .order_by("category__position", "subcategory__position", "subcategory__title")
        .values("category__title", "category__slug", "subcategory__title", "subcategory__slug")
        .all()
    )

    # store all categories in a dict with only title and slug, parent slug
    cats = OrderedDict()
    for csc in categories_from_subcategories:
        key = csc["category__title"]

        if key in cats:
            cats[key].append((csc["subcategory__title"], csc["subcategory__slug"], csc["category__slug"]))
        else:
            cats[key] = [(csc["subcategory__title"], csc["subcategory__slug"], csc["category__slug"])]

    return {"tags": tags, "categories": cats}
