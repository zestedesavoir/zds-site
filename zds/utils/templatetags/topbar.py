# coding: utf-8

from collections import OrderedDict
from django import template
from django.conf import settings

from zds.forum.models import Forum, Topic
from zds.tutorialv2.models.models_database import PublishedContent
from zds.utils.models import CategorySubCategory, Tag
from django.db.models import Count

register = template.Library()


@register.filter('top_categories')
def top_categories(user):
    cats = {}

    forums_pub = Forum.objects.filter(group__isnull=True).select_related("category").distinct().all()
    if user and user.is_authenticated():
        forums_prv = Forum\
            .objects\
            .filter(group__isnull=False, group__in=user.groups.all())\
            .select_related("category").distinct().all()
        forums = list(forums_pub | forums_prv)
    else:
        forums = list(forums_pub)

    for forum in forums:
        key = forum.category.title
        if key in cats:
            cats[key].append(forum)
        else:
            cats[key] = [forum]

    tmp_tags = (Topic.objects
                .values_list('tags__pk', flat=True)
                .distinct()
                .filter(forum__in=forums, tags__isnull=False)
                .annotate(nb_tags=Count("tags"))
                .order_by("-nb_tags")
                [:settings.ZDS_APP['forum']['top_tag_max'] + len(settings.ZDS_APP['forum']['top_tag_exclu'])])

    tags_not_filtered = Tag.objects.filter(pk__in=[pk for pk in tmp_tags])

    # Select tags that are not in the excluded list
    tags = []
    for tag in tags_not_filtered:
        if tag.title not in settings.ZDS_APP['forum']['top_tag_exclu'] \
                and len(tags) <= settings.ZDS_APP['forum']['top_tag_max']:
            tags.append(tag)

    return {"tags": tags, "categories": cats}


@register.filter('top_categories_content')
def top_categories_content(_type):
    """Get all the categories and their related subcategories associated with existing contents.
    The result is sorted by alphabetic order.

    :param _type: type of the content
    :type _type: str
    :return: a dictionary, with the title being the name of the category and the content a list of subcategories,
    Each of these are stored in a tuple of the form ``title, slug``.
    :rtype: OrderedDict
    """
    # get subcategories from PublishedContent
    if _type:
        subcategories_contents = PublishedContent.objects\
            .filter(content_type=_type)\
            .values('content__subcategory').all()
    else:
        # used in page with all content types
        subcategories_contents = PublishedContent.objects\
            .values('content__subcategory').all()

    # get parent categories of subcategories from PublishedContent
    categories_from_subcategories = CategorySubCategory.objects\
        .filter(is_main=True)\
        .filter(subcategory__in=subcategories_contents)\
        .order_by('category__position', 'subcategory__title')\
        .select_related('subcategory', 'category')\
        .values('category__title', 'subcategory__title', 'subcategory__slug')\
        .all()

    # store all categories in a dict with only title and slug
    cats = OrderedDict()
    for csc in categories_from_subcategories:
        key = csc['category__title']

        if key in cats:
            cats[key].append((csc['subcategory__title'], csc['subcategory__slug']))
        else:
            cats[key] = [(csc['subcategory__title'], csc['subcategory__slug'])]

    return {"tags": PublishedContent.objects.get_top_tags(["TUTORIAL", "ARTICLE"],
                                                          limit=settings.ZDS_APP['forum']['top_tag_max']),
            "categories": cats}


@register.filter('auth_forum')
def auth_forum(forum, user):
    return forum.can_read(user)
