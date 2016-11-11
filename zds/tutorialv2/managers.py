# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from zds.utils.models import Tag
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _


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

    def transfert_paternity(self, unsubscribed_user, external):
        for published in self.filter(authors__in=[unsubscribed_user]):
            if published.authors.count() == 1:
                published.authors.add(external)
            published.authors.remove(unsubscribed_user)
            published.save()


class PublishableContentManager(models.Manager):
    """..."""

    def transfert_paternity(self, unsubscribed_user, external, gallery_class):
        for content in unsubscribed_user.profile.get_contents():
            # we delete content only if not published with only one author
            if not content.in_public() and content.authors.count() == 1:
                if content.in_beta() and content.beta_topic:
                    beta_topic = content.beta_topic
                    beta_topic.is_locked = True
                    beta_topic.save()
                    first_post = beta_topic.first_post()
                    first_post.update_content(_(u"# Le tutoriel présenté par ce topic n\'existe plus."))
                    first_post.save()
                content.delete()
            else:
                if content.authors.count() == 1:
                    content.authors.add(external)
                    external_gallery = gallery_class()
                    external_gallery.user = external
                    external_gallery.gallery = content.gallery
                    external_gallery.mode = 'W'
                    external_gallery.save()
                    gallery_class.objects.filter(user=unsubscribed_user).filter(gallery=content.gallery).delete()

                    content.authors.remove(unsubscribed_user)
                    # we say in introduction that the content was written by a former member.
                    versioned = content.load_version()
                    title = versioned.title
                    introduction = u'[[i]]\n|Ce contenu a été rédigé par {} qui a quitté le site.'\
                        .format(unsubscribed_user.username) + versioned.get_introduction()
                    conclusion = versioned.get_conclusion()
                    sha = versioned.repo_pdate(title, introduction, conclusion,
                                               commit_message='Author unsubscribed',
                                               do_commit=True, update_slug=True)
                    content.sha_draft = sha
                    content.save()

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
