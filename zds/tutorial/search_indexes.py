# coding: utf-8

from django.db.models import Q

from haystack import indexes

from zds.tutorial.models import Tutorial, Part, Chapter, Extract
from zds.utils.tutorials import GetPublished


class TutorialIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    subcategory = indexes.MultiValueField()
    sha_public = indexes.CharField(model_attr='sha_public')

    def get_model(self):
        return Tutorial

    def index_queryset(self, using=None):
        """Only tutorials online."""
        return self.get_model().objects.filter(sha_public__isnull=False)

    def prepare_subcategory(self, obj):
        return obj.subcategory.values_list('title', flat=True).all() or None


class PartIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    tutorial = indexes.CharField(model_attr='tutorial')

    def get_model(self):
        return Part

    def index_queryset(self, using=None):

        published_content = GetPublished().get_published_content()

        return self.get_model().objects.filter(tutorial__sha_public__isnull=False, id__in=published_content["parts"])


class ChapterIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    # A Chapter belongs to a Part (big-tuto) **or** a Tutorial (mini-tuto)
    part = indexes.CharField(model_attr='part', null=True)
    tutorial = indexes.CharField(model_attr='tutorial', null=True)

    def get_model(self):
        return Chapter

    def index_queryset(self, using=None):
        """Only chapters online."""
        published_content = GetPublished().get_published_content()

        return self.get_model().objects.filter(Q(tutorial__sha_public__isnull=False) |
                                               Q(part__tutorial__sha_public__isnull=False),
                                               id__in=published_content["chapters"])


class ExtractIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    chapter = indexes.CharField(model_attr='chapter')
    txt = indexes.CharField(model_attr='text')

    def get_model(self):
        return Extract

    def index_queryset(self, using=None):
        """Only extracts online."""

        published_content = GetPublished().get_published_content()

        return self.get_model() .objects.filter(Q(chapter__tutorial__sha_public__isnull=False) |
                                                Q(chapter__part__tutorial__sha_public__isnull=False),
                                                id__in=published_content["extracts"])
