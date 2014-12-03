# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models


class ArticleManager(models.Manager):
    """
    Custom article manager.
    """

    def last_articles_of_a_member_loaded(self, author):
        my_articles = self.filter(sha_public__isnull=False) \
                          .filter(authors__in=[author]) \
                          .order_by("-pubdate") \
                          .all()[:settings.ZDS_APP['article']['home_number']]
        my_article_versions = []
        for my_article in my_articles:
            article_version = my_article.load_json_for_public()
            my_article.load_dic(article_version)
            my_article_versions.append(article_version)
        return my_article_versions
