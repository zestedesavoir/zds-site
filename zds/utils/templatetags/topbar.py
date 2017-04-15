# coding: utf-8

from collections import defaultdict, OrderedDict
from django import template
from django.conf import settings

from zds.forum.models import Forum
from zds.tutorialv2.models.models_database import PublishedContent
from zds.utils.models import CategorySubCategory, Tag
from django.db.models import Count

register = template.Library()


@register.filter('top_categories')
def top_categories(user):
    max_tags = settings.ZDS_APP['forum']['top_tag_max']

    forums_pub = Forum.objects.filter(groups__isnull=True).select_related('category').distinct().all()
    if user and user.is_authenticated():
        forums_private = Forum\
            .objects\
            .filter(groups__isnull=False, groups__in=user.groups.all())\
            .select_related('category').distinct().all()
        forums = list(forums_pub | forums_private)
    else:
        forums = list(forums_pub)

    cats = defaultdict(list)
    forums_pk = []
    for forum in forums:
        forums_pk.append(forum.pk)
        cats[forum.category.position].append(forum)

    tags_by_popularity = list(
        Tag.objects
        .filter(topic__forum__in=forums)
        .annotate(count_topic=Count('topic'))
        .order_by('-count_topic')
    )

    topbar_cats = []
    sorted_cats = sorted(cats)
    for cat in sorted_cats:
        forums = cats[cat]
        title = forums[0].category.title
        topbar_cats.append((title, forums))

    tags = [tag for tag in tags_by_popularity if tag.title not in settings.ZDS_APP['forum']['top_tag_exclu']][:max_tags]

    return {'tags': tags, 'categories': topbar_cats}


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

    # get tags from PublishedContent
    if _type:
        tags = PublishedContent.objects.get_top_tags([_type], limit=settings.ZDS_APP['forum']['top_tag_max'])
    else:
        tags = PublishedContent.objects.get_top_tags(['TUTORIAL', 'ARTICLE', 'OPINION'],
                                                     limit=settings.ZDS_APP['forum']['top_tag_max'])

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

    return {'tags': tags, 'categories': cats}


@register.filter('auth_forum')
def auth_forum(forum, user):
    return forum.can_read(user)
