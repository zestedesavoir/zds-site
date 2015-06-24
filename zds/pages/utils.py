from zds import settings
from zds.tutorialv2.models.models_database import PublishedContent


def get_last_articles():
    n = settings.ZDS_APP['article']['home_number']
    return PublishedContent.objects\
                                .prefetch_related("authors")\
                                .prefetch_related("authors__profile")\
                                .select_related("last_note")\
                                .prefetch_related("subcategory")\
                                .filter(content_type="ARTICLE").all()\
        .order_by('-publication_date')[:n]


def get_last_tutorials():
    n = settings.ZDS_APP['tutorial']['home_number']
    tutorials = PublishedContent.objects\
                                .prefetch_related("authors")\
                                .prefetch_related("authors__profile")\
                                .select_related("last_note")\
                                .prefetch_related("subcategory")\
                                .filter(content_type="TUTORIAL")\
                                .all()\
                                .order_by('-publication_date')[:n]

    return tutorials


def get_tutorials_count():
    return PublishedContent.objects.filter(content_type="TUTORIAL")\
        .count()
