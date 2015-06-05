# coding: utf-8

"""
This package contains classes and methods to allow forums to be indexed
"""

from haystack import indexes

from zds.forum.models import Topic, Post
from django.conf import settings


class TopicIndex(indexes.SearchIndex, indexes.Indexable):
    """Indexes topic data"""
    text = indexes.CharField(document=True, use_template=True)

    title = indexes.CharField(model_attr='title', boost=1 + settings.ZDS_APP['forum']['boost_topic_title'])
    subtitle = indexes.CharField(model_attr='subtitle', boost=1 + settings.ZDS_APP['forum']['boost_topic_subtitle'])

    author = indexes.CharField(model_attr='author')
    pubdate = indexes.DateTimeField(model_attr='pubdate', stored=True, indexed=False)

    def get_model(self):
        return Topic

    def prepare(self, obj):
        data = super(TopicIndex, self).prepare(obj)

        data['boost'] = 1
        if obj.is_solved:
            data['boost'] += settings.ZDS_APP['forum']['boost_topic_solved']

        if obj.is_locked:
            data['boost'] -= settings.ZDS_APP['forum']['boost_topic_locked']

        if obj.is_sticky:
            data['boost'] += settings.ZDS_APP['forum']['boost_topic_sticky']

        return data


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    """Indexes Post data"""
    text = indexes.CharField(document=True, use_template=True)
    txt = indexes.CharField(model_attr='text')
    author = indexes.CharField(model_attr='author')
    pubdate = indexes.DateTimeField(model_attr='pubdate')

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_visible=True, position__gt=1)

    def prepare(self, obj):
        data = super(PostIndex, self).prepare(obj)

        if obj.is_useful:
            data['boost'] = 1 + settings.ZDS_APP['forum']['boost_post_useful']

        return data