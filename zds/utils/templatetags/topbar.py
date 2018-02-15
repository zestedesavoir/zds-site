from collections import defaultdict, OrderedDict
from django import template
from django.conf import settings

from zds.forum.models import Forum
from zds.tutorialv2.models.database import PublishedContent
from zds.utils.models import CategorySubCategory, Tag
from django.db.models import Count, Q

register = template.Library()


@register.filter('top_categories')
def top_categories(user):
    max_tags = settings.ZDS_APP['forum']['top_tag_max']
    forums = (Forum.objects
              .filter(Q(groups__isnull=True) | Q(groups__isnull=False, groups__in=user.groups.all()))
              .select_related('category')
              .distinct()
              .all())

    cats = defaultdict(list)
    for forum in forums:
        cats[forum.category.position].append(forum)

    sorted_cats = sorted(cats)
    topbar_cats = [(cats[cat][0].category.title, cats[cat]) for cat in sorted_cats]

    excluded_tags = settings.ZDS_APP['forum']['top_tag_exclu']
    tags_by_popularity = (
        Tag.objects
        .filter(topic__forum__in=forums)
        .annotate(count_topic=Count('topic'))
        .exclude(title__in=excluded_tags)
        .order_by('-count_topic').all()[:max_tags]
    )
    return {'tags': tags_by_popularity, 'categories': topbar_cats}


@register.filter('top_categories_content')
def top_categories_content(_type):
    """Get all the categories and their related subcategories associated with existing contents.
    The result is sorted by alphabetic order.

    :param _type: type of the content
    :type _type: str or list
    :return: a dictionary, with the title being the name of the category and the content a list of subcategories,
    Each of these are stored in a tuple of the form ``title, slug``.
    :rtype: OrderedDict
    """

    _type = _type if isinstance(_type, list) else [_type]
    tags = PublishedContent.objects.get_top_tags(_type, limit=settings.ZDS_APP['forum']['top_tag_max'])

    subcategories_contents = (PublishedContent.objects
                              .filter(must_redirect=False)
                              .filter(content_type__in=_type)
                              .values('content__subcategory')
                              .all())

    # get parent categories of subcategories from PublishedContent
    categories_from_subcategories = CategorySubCategory.objects\
        .filter(is_main=True)\
        .filter(subcategory__in=subcategories_contents)\
        .order_by('category__position', 'subcategory__position', 'subcategory__title')\
        .values('category__title', 'category__slug', 'subcategory__title', 'subcategory__slug')\
        .all()

    # store all categories in a dict with only title and slug, parent slug
    cats = OrderedDict()
    for csc in categories_from_subcategories:
        key = csc['category__title']

        if key in cats:
            cats[key].append((csc['subcategory__title'], csc['subcategory__slug'], csc['category__slug']))
        else:
            cats[key] = [(csc['subcategory__title'], csc['subcategory__slug'], csc['category__slug'])]

    return {'tags': tags, 'categories': cats}


@register.filter('auth_forum')
def auth_forum(forum, user):
    return forum.can_read(user)
