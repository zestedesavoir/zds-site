# coding: utf-8

from haystack import indexes

from zds.forum.models import Topic, Post


class TopicIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    subtitle = indexes.CharField(model_attr='subtitle')
    author = indexes.CharField(model_attr='author')
    pubdate = indexes.DateTimeField(model_attr='pubdate')

    def get_model(self):
        return Topic

    def index_queryset(self, using=None):
        # Index only public topics
        return self.get_model().objects.filter(forum__group=None)


class PostIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    txt = indexes.CharField(model_attr='text')
    author = indexes.CharField(model_attr='author')
    pubdate = indexes.DateTimeField(model_attr='pubdate')

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        # Index only public posts
        return self.get_model().objects.filter(topic__forum__group=None)
