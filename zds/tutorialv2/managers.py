# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models


class PublishedContentManager(models.Manager):
    """
    Custom published content manager.
    """

    def last_contents_of_a_member_loaded(self, author, _type=None):
        queryset = self.prefetch_related('content')\
            .prefetch_related('content__authors')\
            .filter(content__authors__in=[author])\
            .filter(must_redirect=False)

        if _type:
            queryset = queryset.filter(content_type=_type)

        public_contents = queryset.order_by("-publication_date").all()[:settings.ZDS_APP['content']['user_page_number']]
        contents_version = []
        for public_content in public_contents:
            contents_version.append(public_content.load_public_version())
        return contents_version

    def last_tutorials_of_a_member_loaded(self, author):
        return self.last_contents_of_a_member_loaded(author, _type='TUTORIAL')

    def last_articles_of_a_member_loaded(self, author):
        return self.last_contents_of_a_member_loaded(author, _type='ARTICLE')
