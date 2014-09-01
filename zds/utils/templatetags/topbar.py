# coding: utf-8

from django import template
from django.conf import settings
from django.db.models import Count
import itertools
from zds.forum.models import Category as fCategory, Forum, Topic
from zds.tutorial.models import Tutorial
from zds.utils.models import Category, SubCategory, CategorySubCategory, Tag


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
    
    topics = Topic.objects.filter(forum__in=forums)
    tgs = Topic.objects\
        .values('tags', 'pk')\
        .distinct()\
        .filter(forum__in=forums, tags__isnull=False)
    
    #for tg in tgs:
    #    print tg
    cts = {}
    for key, group in itertools.groupby(tgs, lambda item: item["tags"]):
        for thing in group:
            if key in cts: cts[key]+=1
            else: cts[key]=1

    cpt=0
    top_tag =[]
    sort_list = reversed(sorted(cts.iteritems(), key=lambda (k,v): (v,k)))
    for key, value in sort_list:
        top_tag.append(key)
        cpt+=1
        if cpt >=settings.TOP_TAG_MAX : break
    
    tags=Tag.objects.filter(pk__in=top_tag)
    
    return {"tags":tags, "categories":cats}

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


@register.filter('auth_forum')
def auth_forum(forum, user):
    return forum.can_read(user)

