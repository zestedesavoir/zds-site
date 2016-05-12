# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.db.models import Count, F

from zds.utils.models import Tag


class PublishedContentManager(models.Manager):
    """
    Custom published content manager.
    """

    def last_contents_of_a_member_loaded(self, author, _type=None):
        """
        Get contents published by author depends on settings.ZDS_APP['content']['user_page_number']
        :param author:
        :param _type: subtype to filter request
        :return:
        :rtype: django.db.models.QuerySet
        """

        queryset = self.prefetch_related('content')\
            .prefetch_related('content__authors')\
            .prefetch_related('content__subcategory')\
            .filter(content__authors__in=[author])\
            .filter(must_redirect=False)

        if _type:
            queryset = queryset.filter(content_type=_type)

        public_contents = queryset.order_by("-publication_date").all()[:settings.ZDS_APP['content']['user_page_number']]
        return public_contents

    def last_tutorials_of_a_member_loaded(self, author):
        return self.last_contents_of_a_member_loaded(author, _type='TUTORIAL')

    def last_articles_of_a_member_loaded(self, author):
        return self.last_contents_of_a_member_loaded(author, _type='ARTICLE')

    def last_opinions_of_a_member_loaded(self, author):
        return self.last_contents_of_a_member_loaded(author, _type='OPINION')

    def get_contents_count(self):
        """
        :rtype: int
        """
        return self.filter(must_redirect=False)\
                   .count()

    def get_top_tags(self, displayed_types, limit=-1):
        published = self.filter(
            must_redirect=False,
            content__type__in=displayed_types).values('content__tags').distinct()
        tags_pk = [tag['content__tags'] for tag in published]
        queryset = Tag.objects\
            .filter(pk__in=tags_pk, publishablecontent__public_version__isnull=False,
                    publishablecontent__type__in=displayed_types)\
            .annotate(num_content=Count('publishablecontent'))\
            .order_by('-num_content', 'title')
        if limit > 0:
            queryset = queryset[:limit]
        return queryset


class PublishableContentManager(models.Manager):
    """..."""

    def get_last_tutorials(self):
        """
        This depends on settings.ZDS_APP['tutorial']['home_number'] parameter
        :return: lit of last published content
        :rtype: list
        """
        home_number = settings.ZDS_APP['tutorial']['home_number']
        all_contents = self.filter(type="TUTORIAL")\
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

    def get_last_articles(self):
        """
        ..attention:
            this one use a raw subquery for historical reasons. Il will hopefully be replaced one day by an
            ORM primitive.

        :return: list of last articles expended with "count_note" property that prefetch number of comments
        :rtype:list
        """
        sub_query = "SELECT COUNT(*) FROM {} WHERE {}={}"
        sub_query = sub_query.format(
            "tutorialv2_contentreaction",
            "tutorialv2_contentreaction.related_content_id",
            "tutorialv2_publishedcontent.content_pk"
        )
        home_number = settings.ZDS_APP['article']['home_number']
        all_contents = self.filter(type="ARTICLE")\
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

    def get_last_opinions(self):
        """
        This depends on settings.ZDS_APP['opinions']['home_number'] parameter.
        Displey only published, approuved and with a +n vote ratio opinions
        (where n = settings.ZDS_APP['opinions']['home_ratio']).

        :return: lit of last opinions
        :rtype: list
        """
        home_number = settings.ZDS_APP['opinions']['home_number']
        # TODO : add votes filter when available in this query
        all_contents = self.filter(type="OPINION") \
                           .filter(public_version__isnull=False, sha_approved=F('sha_public')) \
                           .prefetch_related("authors") \
                           .prefetch_related("authors__profile") \
                           .select_related("last_note") \
                           .select_related("public_version") \
                           .prefetch_related("subcategory") \
                           .order_by('-public_version__publication_date')[:home_number]
        published = []
        for content in all_contents:
            content.public_version.content = content
            published.append(content.public_version)
        return published
