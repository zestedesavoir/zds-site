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
    pubdate = indexes.DateTimeField(model_attr='pubdate', stored=True, indexed=False)

    # Groups authorized to read this topic.
    # If a group "public" is defined, the forum is public (and anyone can read it).
    permissions = indexes.MultiValueField()

    tags = indexes.MultiValueField()

    def get_model(self):
        return Topic

    def prepare_permissions(self, obj):
        return [group.name for group in obj.forum.group.all()] or "public"

    def prepare_tags(self, obj):
        return [tag.title for tag in obj.tags.all()] or None


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    """Indexes Post data"""
    text = indexes.CharField(document=True, use_template=True)
    txt = indexes.CharField(model_attr='text')
    author = indexes.CharField(model_attr='author')

    pubdate = indexes.DateTimeField(model_attr='pubdate', stored=True, indexed=False)
    topic_title = indexes.CharField(stored=True, indexed=False)
    topic_author = indexes.CharField(stored=True, indexed=False)
    topic_forum = indexes.CharField(stored=True, indexed=False)

    tags = indexes.MultiValueField()

    # Groups authorized to read this post. If no group is defined, the forum is public (and anyone can read it).
    permissions = indexes.MultiValueField()

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_visible=True, position__gt=1)

    def prepare_topic_title(self, obj):
        return obj.topic.title

    def prepare_topic_author(self, obj):
        return obj.topic.author

    def prepare_topic_forum(self, obj):
        return obj.topic.forum

    def prepare_tags(self, obj):
        return [tag.title for tag in obj.topic.tags.all()] or None

    def prepare_permissions(self, obj):
        return [group.name for group in obj.topic.forum.group.all()] or "public"