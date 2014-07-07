# coding: utf-8

from django import template

from zds.forum.models import Category as fCategory, Forum
from zds.tutorial.models import Tutorial
from zds.utils.models import Category, SubCategory, CategorySubCategory


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
        forums = list(forums_pub|forums_prv)
    else :
        forums = list(forums_pub)
    
    for forum in forums:
        key = forum.category.title
        if cats.has_key(key):
            cats[key].append(forum)
        else:
            cats[key] = [forum]
    
    return cats


@register.filter('top_categories_tuto')
def top_categories_tuto(user):
    
    cats = {}
    subcats_tutos = Tutorial.objects.values('subcategory').filter(sha_public__isnull=False).all()
    catsubcats = CategorySubCategory.objects \
            .filter(is_main=True)\
            .filter(subcategory__in=subcats_tutos)\
            .select_related('subcategory','category')\
            .all()

    cscs = list(catsubcats.all())
    
    for csc in cscs:
        key = csc.category.title
        if cats.has_key(key):
            cats[key].append(csc.subcategory)
        else:
            cats[key] = [csc.subcategory]
    return cats
