# coding: utf-8

from django import template
from django.conf import settings
import itertools
from zds.forum.models import Forum, Topic
from zds.tutorial.models import PubliableContent
from zds.utils.models import CategorySubCategory, Tag


register = template.Library()


@register.filter('top_categories')
def top_categories(user):
    cats = {}

    forums_pub = Forum.objects.filter(group__isnull=True).select_related("category").all()
    if user and user.is_authenticated():
        forums_prv = Forum\
            .objects\
            .filter(group__isnull=False, group__in=user.groups.all())\
            .select_related("category").all()
        forums = list(forums_pub | forums_prv)
    else:
        forums = list(forums_pub)

    for forum in forums:
        key = forum.category.title
        if key in cats:
            cats[key].append(forum)
        else:
            cats[key] = [forum]

    tgs = Topic.objects\
        .values('tags', 'pk')\
        .distinct()\
        .filter(forum__in=forums, tags__isnull=False)

    cts = {}
    for key, group in itertools.groupby(tgs, lambda item: item["tags"]):
        for thing in group:
            if key in cts:
                cts[key] += 1
            else:
                cts[key] = 1

    cpt = 0
    top_tag = []
    sort_list = reversed(sorted(cts.iteritems(), key=lambda k_v: (k_v[1], k_v[0])))
    for key, value in sort_list:
        top_tag.append(key)
        cpt += 1
        if cpt >= settings.ZDS_APP['forum']['top_tag_max']:
            break

    tags = Tag.objects.filter(pk__in=top_tag)

    return {"tags": tags, "categories": cats}


@register.filter('top_categories_tuto')
def top_categories_tuto(user):

    cats = {}
    subcats_tutos = PubliableContent.objects.values('subcategory').filter(sha_public__isnull=False).all()
    catsubcats = CategorySubCategory.objects \
        .filter(is_main=True)\
        .filter(subcategory__in=subcats_tutos)\
        .select_related('subcategory', 'category')\
        .all()

    cscs = list(catsubcats.all())

    for csc in cscs:
        key = csc.category.title
        if key in cats:
            cats[key].append(csc.subcategory)
        else:
            cats[key] = [csc.subcategory]
    return cats


@register.filter('auth_forum')
def auth_forum(forum, user):
    return forum.can_read(user)
