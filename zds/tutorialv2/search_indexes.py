# coding: utf-8
from haystack import indexes

from zds.tutorialv2.models.models_database import PublishableContent
from zds.tutorialv2.models.models_versioned import Extract


class ContentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    category = indexes.CharField(model_attr='subcategory')
    sha_public = indexes.CharField(model_attr='sha_public')

    def get_model(self):
        return PublishableContent

    def index_queryset(self, using=None):
        """Only tutorials online."""
        return self.get_model().objects.filter(sha_public__isnull=False)


class ContainerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')

    def get_model(self):
        return PublishableContent

    def index_queryset(self, using=None):
        """Only parts online."""
        return self.get_model().objects.filter(sha_public__isnull=False)

    def prepare_title(self):
        contents = self.index_queryset()
        part_titles = []
        for content in contents:
            versionned = content.load_verstion(None, True)
            part_titles += [p.title for p in versionned.traverse(True)]
        return part_titles


class ExtractIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title')
    url = indexes.CharField()
    txt = indexes.CharField(model_attr='text')

    def get_model(self):
        return Extract

    def index_queryset(self, using=None):
        """Only extracts online."""
        return PublishableContent.objects.filter(sha_public__isnull=False)

    def prepare_text(self):
        contents = self.index_queryset()
        extracts = []
        for content in contents:
            versionned = content.load_verstion(None, False)
            extracts += [p.get_text() for p in versionned.traverse() if isinstance(p, Extract)]
        return extracts

    def prepare_title(self):
        contents = self.index_queryset()
        extracts = []
        for content in contents:
            versionned = content.load_verstion(None, False)
            extracts += [p.title for p in versionned.traverse() if isinstance(p, Extract)]
        return extracts

    def prepare_url(self):
        contents = self.index_queryset()
        extracts = []
        for content in contents:
            versionned = content.load_verstion(None, False)
            extracts += [p.get_absolute_url_online() for p in versionned.traverse() if isinstance(p, Extract)]
        return extracts
