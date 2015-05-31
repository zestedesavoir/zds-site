# coding: utf-8

"""
This package contains classes and methods to allow forums to be indexed
"""

from haystack import indexes

from zds.forum.models import Topic, Post


class TopicIndex(indexes.SearchIndex, indexes.Indexable):
    """Indexes topic data"""
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    subtitle = indexes.CharField(model_attr='subtitle')
    author = indexes.CharField(model_attr='author')
    pubdate = indexes.DateTimeField(model_attr='pubdate')

    tags = indexes.MultiValueField()

    def get_model(self):
        return Topic

    def prepare_tags(self, obj):
        return obj.tags.values_list('title', flat=True).all()


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    """Indexes Post data"""
    text = indexes.CharField(document=True, use_template=True)
    txt = indexes.CharField(model_attr='text')
    author = indexes.CharField(model_attr='author')
    pubdate = indexes.DateTimeField(model_attr='pubdate')

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_visible=True)
