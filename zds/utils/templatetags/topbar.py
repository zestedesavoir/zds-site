# coding: utf-8

from collections import OrderedDict

from django import template
from django.conf import settings

from zds.article.models import Article
from zds.forum.models import Forum, Topic
from zds.tutorial.models import Tutorial
from zds.utils.models import CategorySubCategory, Tag
from django.db.models.aggregates import Count

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

    tags = (
        Tag.objects.annotate(num_topic=Count('topic'))
                   .order_by('-num_topic')
                   .filter(topic__not_in=Topic.objects.filter(forum__in=forums).all())
                   .exclude(title__in=settings.ZDS_APP['forum']['top_tag_exclu'])
        [:settings.ZDS_APP['forum']['top_tag_max']]
    )

    return {"tags": tags, "categories": cats}


@register.filter('top_categories_tuto')
def top_categories_tuto(user):
    """
        Get all the categories and their related subcategories
        associed with an existing tutorial. The result is sorted
        by alphabetic order.
    """

    # Ordered dict is use to keep order
    cats = OrderedDict()

    subcats_tutos = Tutorial.objects.values('subcategory').filter(sha_public__isnull=False).all()
    catsubcats = CategorySubCategory.objects \
        .filter(is_main=True)\
        .filter(subcategory__in=subcats_tutos)\
        .order_by('category__position', 'subcategory__title')\
        .select_related('subcategory', 'category')\
        .values('category__title', 'subcategory__title', 'subcategory__slug')\
        .all()

    for csc in catsubcats:
        key = csc['category__title']

        if key in cats:
            cats[key].append((csc['subcategory__title'], csc['subcategory__slug']))
        else:
            cats[key] = [(csc['subcategory__title'], csc['subcategory__slug'])]

    return cats


@register.filter('top_categories_article')
def top_categories_article(user):
    """
        Get all the categories and their related subcategories
        associed with an existing articles. The result is sorted
        by alphabetic order.
    """

    # Ordered dict is use to keep order
    cats = OrderedDict()

    subcats_articles = Article.objects.values('subcategory').filter(sha_public__isnull=False).all()
    catsubcats = CategorySubCategory.objects \
        .filter(is_main=True)\
        .filter(subcategory__in=subcats_articles)\
        .order_by('category__position', 'subcategory__title')\
        .select_related('subcategory', 'category')\
        .values('category__title', 'subcategory__title', 'subcategory__slug')\
        .all()

    for csc in catsubcats:
        key = csc['category__title']

        if key in cats:
            cats[key].append((csc['subcategory__title'], csc['subcategory__slug']))
        else:
            cats[key] = [(csc['subcategory__title'], csc['subcategory__slug'])]

    return cats


@register.filter('auth_forum')
def auth_forum(forum, user):
    return forum.can_read(user)
