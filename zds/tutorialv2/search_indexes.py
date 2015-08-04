# coding: utf-8
from haystack import indexes

from zds.search.models import SearchIndexContainer, SearchIndexContent, SearchIndexExtract


class ContentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    # Search criteria
    pubdate = indexes.DateTimeField(model_attr='pub_date', stored=True)
    updatedate = indexes.DateTimeField(model_attr='update_date', stored=True)

    licence = indexes.CharField(model_attr='licence', stored=True)

    tags = indexes.MultiValueField()
    authors = indexes.MultiValueField()

    # Field needed for display purpose
    urlimage = indexes.CharField(model_attr='url_image', stored=True, null=True)
    url_to_redirect = indexes.CharField(model_attr='url_to_redirect', stored=True)
    introduction = indexes.CharField(model_attr='introduction', stored=True, null=True)
    conclusion = indexes.CharField(model_attr='conclusion', stored=True, null=True)
    type = indexes.CharField(model_attr='type', stored=True)

    permissions = indexes.MultiValueField()

    def get_model(self):
        return SearchIndexContent

    def get_updated_field(self):
        return "update_date"

    def index_queryset(self, using=None):
        return self.get_model().objects.select_related()

    def prepare_tags(self, obj):
        return [tag.title for tag in obj.tags.all()] or None

    def prepare_authors(self, obj):
        return [author.username for author in obj.authors.all()] or None

    def prepare_permissions(self, obj):
        return "public"


class ContainerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    # Search criteria
    pubdate = indexes.DateTimeField(stored=True)
    updatedate = indexes.DateTimeField(stored=True)

    licence = indexes.CharField(stored=True)

    tags = indexes.MultiValueField()
    authors = indexes.MultiValueField()

    # Field needed for display purpose
    urlimage = indexes.CharField(stored=True, null=True)
    url_to_redirect = indexes.CharField(model_attr='url_to_redirect', stored=True)
    introduction = indexes.CharField(model_attr='introduction', stored=True, null=True)
    conclusion = indexes.CharField(model_attr='conclusion', stored=True, null=True)

    type = indexes.CharField(stored=True)
    level = indexes.CharField(stored=True)

    permissions = indexes.MultiValueField()

    def get_model(self):
        return SearchIndexContainer

    def get_updated_field(self):
        return "update_date"

    def index_queryset(self, using=None):
        return self.get_model().objects.select_related()

    def prepare_tags(self, obj):
        return [tag.title for tag in obj.search_index_content.tags.all()] or None

    def prepare_authors(self, obj):
        return [author.username for author in obj.search_index_content.authors.all()] or None

    def prepare_licence(self, obj):
        return obj.search_index_content.licence

    def prepare_pubdate(self, obj):
        return obj.search_index_content.pub_date

    def prepare_updatedate(self, obj):
        return obj.search_index_content.update_date

    def prepare_urlimage(self, obj):
        return obj.search_index_content.url_image

    def prepare_type(self, obj):
        return obj.search_index_content.type

    def prepare_level(self, obj):
        return obj.level

    def prepare_permissions(self, obj):
        return "public"


class ExtractIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    # Search criteria
    pubdate = indexes.DateTimeField(stored=True)
    updatedate = indexes.DateTimeField(stored=True)

    licence = indexes.CharField(stored=True)

    tags = indexes.MultiValueField()
    authors = indexes.MultiValueField()

    # Field needed for display purpose
    urlimage = indexes.CharField(stored=True, null=True)
    url_to_redirect = indexes.CharField(model_attr='url_to_redirect', stored=True, null=True)
    content = indexes.CharField(model_attr='extract_content', stored=True, null=True)

    type = indexes.CharField(stored=True)

    permissions = indexes.MultiValueField()

    def get_model(self):
        return SearchIndexExtract

    def get_updated_field(self):
        return "update_date"

    def index_queryset(self, using=None):
        return self.get_model().objects.select_related()

    def prepare_tags(self, obj):
        return [tag.title for tag in obj.search_index_content.tags.all()] or None

    def prepare_authors(self, obj):
        return [author.username for author in obj.search_index_content.authors.all()] or None

    def prepare_licence(self, obj):
        return obj.search_index_content.licence

    def prepare_pubdate(self, obj):
        return obj.search_index_content.pub_date

    def prepare_updatedate(self, obj):
        return obj.search_index_content.update_date

    def prepare_urlimage(self, obj):
        return obj.search_index_content.url_image

    def prepare_type(self, obj):
        return obj.search_index_content.type

    def prepare_permissions(self, obj):
        return "public"
