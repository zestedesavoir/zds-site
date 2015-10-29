from zds import settings
from zds.tutorialv2.models.models_database import PublishedContent, PublishableContent


def get_last_articles():
    sub_query = "SELECT COUNT(*) FROM {} WHERE {}={}"
    sub_query = sub_query.format(
        "tutorialv2_contentreaction",
        "tutorialv2_contentreaction.related_content_id",
        "tutorialv2_publishedcontent.content_pk"
    )
    home_number = settings.ZDS_APP['article']['home_number']
    all_contents = PublishableContent.objects.filter(type="ARTICLE")\
                                     .filter(public_version__isnull=False)\
                                     .prefetch_related("authors")\
                                     .prefetch_related("authors__profile")\
                                     .select_related("last_note")\
                                     .select_related("public_version")\
                                     .prefetch_related("subcategory")\
                                     .extra(select={"count_note": sub_query})\
                                     .order_by('-public_version__publication_date')[:home_number]
    published = []
    for content in all_contents:
        content.public_version.content = content
        published.append(content.public_version)
    return published


def get_last_tutorials():
    home_number = settings.ZDS_APP['tutorial']['home_number']
    all_contents = PublishableContent.objects.filter(type="TUTORIAL")\
                                     .filter(public_version__isnull=False)\
                                     .prefetch_related("authors")\
                                     .prefetch_related("authors__profile")\
                                     .select_related("last_note")\
                                     .select_related("public_version")\
                                     .prefetch_related("subcategory")\
                                     .order_by('-public_version__publication_date')[:home_number]
    published = []
    for content in all_contents:
        content.public_version.content = content
        published.append(content.public_version)
    return published


def get_tutorials_count():
    return PublishedContent.objects\
        .filter(content_type="TUTORIAL", must_redirect=False)\
        .count()
