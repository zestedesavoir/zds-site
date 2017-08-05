# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.db.models import Count, F
from django.utils.translation import ugettext_lazy as _

from zds.utils.models import Tag, Category


class PublishedContentManager(models.Manager):

    def published_contents(self, _type=None, categories=[], subcategories=[]):
        """
        Get contents published ordered by date

        :return:
        :rtype: django.db.models.QuerySet
        """
        queryset = self.prefetch_related('content') \
            .prefetch_related('content__authors') \
            .prefetch_related('content__subcategory') \
            .filter(must_redirect=False) \
            .order_by('-publication_date')

        if _type:
            queryset = queryset.filter(content_type=_type)

        if categories:
            if isinstance(categories[0], int):
                cats = Category.objects.filter(pk__in=categories)
            else:
                cats = Category.objects.filter(slug__in=categories)

            for cat in cats:
                subcats = cat.get_subcategories()
                for subcat in subcats:
                    subcategories.append(subcat)

            subcategories = list(set(subcategories))

        if subcategories:
            if isinstance(subcategories[0], int):
                queryset = queryset.filter(content__subcategory__in=subcategories)
            else:
                queryset = queryset.filter(content__subcategory__slug__in=subcategories)

        return queryset

    def last_contents_of_a_member_loaded(self, author, _type=None):
        """
        Get contents published by author depends on settings.ZDS_APP['content']['user_page_number']

        :param author:
        :param _type: subtype to filter request
        :return:
        :rtype: django.db.models.QuerySet
        """
        queryset = self.published_contents(_type) \
            .filter(authors__in=[author])

        public_contents = queryset.all()[:settings.ZDS_APP['content']['user_page_number']]
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
        return self.filter(must_redirect=False) \
                   .count()

    def get_top_tags(self, displayed_types, limit=-1):
        """
        Retrieve all most rated tags.

        :param displayed_types:
        :param limit: if ``-1`` or ``0`` => no limit. Else just takes the provided number of elements.
        :return:
        """
        published = self.filter(
            must_redirect=False,
            content__type__in=displayed_types).values('content__tags').distinct()
        tags_pk = [tag['content__tags'] for tag in published]
        queryset = Tag.objects\
            .filter(pk__in=tags_pk, publishablecontent__public_version__isnull=False,
                    publishablecontent__type__in=displayed_types) \
            .annotate(num_content=Count('publishablecontent')) \
            .order_by('-num_content', 'title')
        if limit > 0:
            queryset = queryset[:limit]
        return queryset

    def transfer_paternity(self, unsubscribed_user, replacement_author):
        """
        erase or transfer the paternity of all published content owned by a user.
        if a content has more than one author, the unregistering author just leave its redaction\
        else just mark ``replacement_author`` as the new author

        """
        for published in self.filter(authors__in=[unsubscribed_user]):
            if published.authors.count() == 1:
                published.authors.add(replacement_author)
            published.authors.remove(unsubscribed_user)
            published.save()

    def get_recent_list(self, subcategories=[], tags=[], content_type=[]):
        queryset = self.__get_list(
            subcategories=subcategories,
            tags=tags,
            content_type=content_type)
        return queryset.order_by('-publication_date')

    def get_most_commented_list(self, subcategories=[], tags=[], content_type=[]):
        queryset = self.__get_list(
            subcategories=subcategories,
            tags=tags,
            content_type=content_type)
        return queryset.order_by('-count_note')

    def get_browse_list(self, subcategories=[], tags=[], content_type=[], order_fields=[]):
        queryset = self.__get_list(
            subcategories=subcategories,
            tags=tags,
            content_type=content_type)
        if order_fields:
            queryset.order_by(*order_fields)
        return queryset

    def get_featured(self, nb=2):
        return self.__get_list().order_by('-publication_date')[:nb]

    def __get_list(self, subcategories=[], tags=[], content_type=[]):
        """
        :param subcategories: subcategories
        :type subcategories: list of SubCategory
        :param tags: tags
        :type tags: list of Tag
        :param content_type: type of content
        :type content_type: str
        :return: queryset
        :rtype: django.db.models.QuerySet
        """
        if isinstance(content_type, str):
            content_type = [content_type]

        sub_query = """
            SELECT COUNT(*)
            FROM tutorialv2_contentreaction
            WHERE tutorialv2_contentreaction.related_content_id=`tutorialv2_publishablecontent`.`id`
        """
        queryset = self.filter(must_redirect=False)
        if content_type:
            queryset = queryset.filter(content_type__in=list(map(lambda c: c.upper(), content_type)))

        # prefetch:
        queryset = queryset \
            .prefetch_related('content') \
            .prefetch_related('content__subcategory') \
            .prefetch_related('content__authors') \
            .select_related('content__licence') \
            .select_related('content__image') \
            .select_related('content__last_note') \
            .select_related('content__last_note__related_content') \
            .select_related('content__last_note__related_content__public_version') \
            .filter(pk=F('content__public_version__pk'))
        if subcategories:
            queryset = queryset.filter(content__subcategory__in=subcategories)
            # TODO: this is incorrect because it's AND, should be OR
        if tags:
            queryset = queryset.filter(content__tags__in=tags)
        queryset = queryset.extra(select={'count_note': sub_query})
        print queryset.query
        return queryset


class PublishableContentManager(models.Manager):
    """..."""

    def transfer_paternity(self, unregistered_user, replacement_author, gallery_class):
        """
        Erases or transfers the paternity of all publishable content owned by a user. \
        If a content has more than one author, the unregistering author simply leaves its author list, \
        otherwise their published content are sent to ``replacement_author``, \
        unpublished content are deleted and their beta topics closed.

        :param unregistered_user: the user to be unregistered
        :param replacement_author: the new author
        :param gallery_class: the class to link tutorial with gallery (perhaps overkill :p)
        """
        for content in self.filter(authors__in=[unregistered_user]):
            # we delete content only if not published with only one author
            if not content.in_public() and content.authors.count() == 1:
                if content.in_beta() and content.beta_topic:
                    beta_topic = content.beta_topic
                    beta_topic.is_locked = True
                    beta_topic.save()
                    first_post = beta_topic.first_post()
                    first_post.update_content(_(u"# Le tutoriel présenté par ce topic n'existe plus."))
                    first_post.save()
                content.delete()
            else:
                if content.authors.count() == 1:
                    content.authors.add(replacement_author)
                    external_gallery = gallery_class()
                    external_gallery.user = replacement_author
                    external_gallery.gallery = content.gallery
                    external_gallery.mode = 'W'
                    external_gallery.save()
                    gallery_class.objects.filter(user=unregistered_user).filter(gallery=content.gallery).delete()

                    content.authors.remove(unregistered_user)
                    # we add a sentence to the content's introduction stating it was written by a former member.
                    versioned = content.load_version()
                    title = versioned.title
                    introduction = _('[[i]]\n|Ce contenu a été rédigé par {} qui a quitté le site.\n\n')\
                        .format(unregistered_user.username) + versioned.get_introduction()
                    conclusion = versioned.get_conclusion()
                    sha = versioned.repo_update(title, introduction, conclusion,
                                                commit_message='Author unsubscribed',
                                                do_commit=True, update_slug=True)
                    content.sha_draft = sha
                    content.save()

    def get_last_tutorials(self, number=0):
        """
        get list of last published tutorial

        :param number: number of tutorial you want. By default it is interpreted as \
        ``settings.ZDS_APP['tutorial']['home_number']``
        :return: list of last published content
        :rtype: list
        """
        number = number or settings.ZDS_APP['tutorial']['home_number']
        all_contents = self.filter(type='TUTORIAL') \
                           .filter(public_version__isnull=False) \
                           .prefetch_related('authors') \
                           .prefetch_related('authors__profile') \
                           .select_related('last_note') \
                           .select_related('public_version') \
                           .prefetch_related('subcategory') \
                           .prefetch_related('tags') \
                           .order_by('-public_version__publication_date')[:number]
        published = []
        for content in all_contents:
            content.public_version.content = content
            published.append(content.public_version)
        return published

    def get_last_articles(self, number=0):
        """
        ..attention:
            this one uses a raw subquery for historical reasons. It will hopefully be replaced one day by an
            ORM primitive.

        :return: list of last articles expanded with 'count_note' property that prefetches number of comments
        :rtype: list
        """
        sub_query = 'SELECT COUNT(*) FROM {} WHERE {}={}'.format(
            'tutorialv2_contentreaction',
            'tutorialv2_contentreaction.related_content_id',
            'tutorialv2_publishedcontent.content_pk',
        )
        number = number or settings.ZDS_APP['article']['home_number']
        all_contents = self.filter(type='ARTICLE') \
                           .filter(public_version__isnull=False) \
                           .prefetch_related('authors') \
                           .prefetch_related('authors__profile') \
                           .select_related('last_note') \
                           .select_related('public_version') \
                           .prefetch_related('subcategory') \
                           .prefetch_related('tags') \
                           .extra(select={'count_note': sub_query}) \
                           .order_by('-public_version__publication_date')[:number]
        published = []
        for content in all_contents:
            content.public_version.content = content
            published.append(content.public_version)
        return published

    def get_last_opinions(self):
        """
        This depends on settings.ZDS_APP['opinions']['home_number'] parameter.

        :return: list of last opinions
        :rtype: list
        """
        home_number = settings.ZDS_APP['opinions']['home_number']
        all_contents = self.filter(type='OPINION') \
                           .filter(public_version__isnull=False, sha_picked=F('sha_public')) \
                           .prefetch_related('authors') \
                           .prefetch_related('authors__profile') \
                           .select_related('last_note') \
                           .select_related('public_version') \
                           .prefetch_related('subcategory') \
                           .prefetch_related('tags') \
                           .order_by('-picked_date')[:home_number]
        published = []
        for content in all_contents:
            content.public_version.content = content
            published.append(content.public_version)
        return published
