from haystack import indexes

from lbp.forum.models import Topic


class TopicIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    subtitle = indexes.CharField(model_attr='subtitle')
    author = indexes.CharField(model_attr='author')
    last_message = indexes.CharField(model_attr='last_message')
    pubdate = indexes.DateTimeField(model_attr='pubdate')

    def get_model(self):
        return Topic
