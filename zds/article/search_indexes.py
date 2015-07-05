# coding: utf-8

from haystack import indexes

from zds.article.models import Article


class ArticleIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    pubdate = indexes.DateTimeField(model_attr='pubdate')
    txt = indexes.CharField(model_attr='text')

    # Groups authorized to read this topic.
    # If a group "public" is defined, the forum is public (and anyone can read it).
    permissions = indexes.MultiValueField()

    def get_model(self):
        return Article

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects\
            .filter(sha_public__isnull=False)

    def prepare_permissions(self, obj):
        return "public"
