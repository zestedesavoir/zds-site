from zds import settings
from zds.tutorialv2.models.models_database import PublishableContent


def get_last_articles():
    n = settings.ZDS_APP['article']['home_number']
    return PublishableContent.objects.filter(type="ARTICLE").all()\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:n]


def get_last_tutorials():
    n = settings.ZDS_APP['tutorial']['home_number']
    tutorials = PublishableContent.objects.filter(type="TUTORIAL").all()\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:n]

    return tutorials


def get_tutorials_count():
    return PublishableContent.objects.filter(type="TUTORIAL").exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .count()