from datetime import datetime, date, timedelta
from collections import defaultdict, OrderedDict
from zds import json_handler
from uuslug import slugify
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import Http404, HttpResponsePermanentRedirect, StreamingHttpResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, FormView, ListView, TemplateView
from django.db.models import F, Q

from apiclient.discovery import build
from httplib2 import Http, ServerNotFoundError
from oauth2client.service_account import ServiceAccountCredentials
import googleapiclient

from zds.forum.models import Forum
from zds.featured.mixins import FeatureableMixin
from zds.member.decorator import LoggedWithReadWriteHability, LoginRequiredMixin, PermissionRequiredMixin
from zds.member.views import get_client_ip
from zds.notification import signals
from zds.notification.models import ContentReactionAnswerSubscription, NewPublicationSubscription
from zds.tutorialv2.forms import RevokeValidationForm, WarnTypoForm, NoteForm, NoteEditForm, UnpublicationForm, \
    PickOpinionForm, PromoteOpinionToArticleForm, UnpickOpinionForm, ContentCompareStatsURLForm, SearchSuggestionForm, \
    EditContentTagsForm
from zds.tutorialv2.mixins import SingleOnlineContentDetailViewMixin, SingleOnlineContentViewMixin, DownloadViewMixin, \
    ContentTypeMixin, SingleOnlineContentFormViewMixin, MustRedirect
from zds.tutorialv2.models import TYPE_CHOICES_DICT, CONTENT_TYPE_LIST
from zds.tutorialv2.models.database import PublishableContent, PublishedContent, ContentReaction, ContentContribution, \
    ContentSuggestion
from zds.tutorialv2.utils import search_container_or_404, last_participation_is_old, mark_read, NamedUrl
from zds.utils.models import Alert, CommentVote, Tag, Category, CommentEdit, SubCategory, get_hat_from_request, \
    CategorySubCategory
from zds.utils.paginator import make_pagination, ZdSPagingListView
from zds.utils.templatetags.topbar import topbar_publication_categories

logger = logging.getLogger(__name__)


class RedirectContentSEO(RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        """Redirects the user to the new url"""
        obj = get_object_or_404(PublishableContent, old_pk=int(kwargs.get('pk')), type='TUTORIAL')
        if not obj.in_public():
            raise Http404("Aucun contenu public n'est disponible avec cet identifiant.")
        kwargs['parent_container_slug'] = str(kwargs['p2']) + '_' + kwargs['parent_container_slug']
        kwargs['container_slug'] = str(kwargs['p3']) + '_' + kwargs['container_slug']
        obj = search_container_or_404(obj.load_version(public=True), kwargs)

        return obj.get_absolute_url_online()


class DisplayOnlineContent(FeatureableMixin, SingleOnlineContentDetailViewMixin):
    """Base class that can show any online content"""

    model = PublishedContent
    template_name = 'tutorialv2/view/content_online.html'

    current_content_type = ''
    verbose_type_name = _('contenu')
    verbose_type_name_plural = _('contenus')

    def featured_request_allowed(self):
        """Featured request is not allowed on obsolete content and opinions
        """
        return self.object.type != 'OPINION' and not self.object.is_obsolete

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super(DisplayOnlineContent, self).get_context_data(**kwargs)

        if context['is_staff']:
            if self.current_content_type == 'OPINION':
                context['alerts'] = self.object.alerts_on_this_content.all()
            context['formRevokeValidation'] = RevokeValidationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})
            context['formUnpublication'] = UnpublicationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})

        context['formWarnTypo'] = WarnTypoForm(self.versioned_object, self.versioned_object)

        queryset_reactions = ContentReaction.objects\
            .select_related('author') \
            .select_related('author__profile') \
            .select_related('hat') \
            .select_related('editor') \
            .prefetch_related('alerts_on_this_comment') \
            .prefetch_related('alerts_on_this_comment__author') \
            .filter(related_content__pk=self.object.pk) \
            .order_by('pubdate')

        # pagination of articles and opinions
        context['previous_content'] = None
        context['next_content'] = None

        if self.current_content_type in ('ARTICLE', 'OPINION'):
            queryset_pagination = PublishedContent.objects.filter(content_type=self.current_content_type,
                                                                  must_redirect=False)

            context['previous_content'] = queryset_pagination \
                .filter(publication_date__lt=self.public_content_object.publication_date) \
                .order_by('-publication_date').first()
            context['next_content'] = queryset_pagination \
                .filter(publication_date__gt=self.public_content_object.publication_date) \
                .order_by('publication_date').first()

        if self.versioned_object.type == 'OPINION':
            context['formPickOpinion'] = PickOpinionForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})
            context['formUnpickOpinion'] = UnpickOpinionForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})
            context['formConvertOpinion'] = PromoteOpinionToArticleForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})
        else:
            context['content_suggestions'] = ContentSuggestion \
                .objects \
                .filter(publication=self.object)
            excluded_for_search = [str(x.suggestion.pk) for x in context['content_suggestions']]
            excluded_for_search.append(str(self.object.pk))
            context['formAddSuggestion'] = SearchSuggestionForm(content=self.object,
                                                                initial={'excluded_pk': ','.join(excluded_for_search)})

        initial_tags_field = ', '.join(self.object.tags.values_list('title', flat=True))
        context['form_edit_tags'] = EditContentTagsForm(self.versioned_object, initial={'tags': initial_tags_field})

        # pagination of comments
        make_pagination(context,
                        self.request,
                        queryset_reactions,
                        settings.ZDS_APP['content']['notes_per_page'],
                        context_list_name='reactions',
                        with_previous_item=True)

        # is JS activated ?
        context['is_js'] = True
        if not self.object.js_support:
            context['is_js'] = False

        # optimize requests:
        votes = CommentVote.objects.filter(user_id=self.request.user.id, comment__in=queryset_reactions).all()
        context['user_like'] = [vote.comment_id for vote in votes if vote.positive]
        context['user_dislike'] = [vote.comment_id for vote in votes if not vote.positive]

        if self.request.user.has_perm('tutorialv2.change_contentreaction'):
            context['user_can_modify'] = [reaction.pk for reaction in queryset_reactions]
        else:
            context['user_can_modify'] = [reaction.pk for reaction in queryset_reactions
                                          if reaction.author == self.request.user]

        context['is_antispam'] = self.object.antispam()
        context['pm_link'] = self.object.get_absolute_contact_url(_('À propos de'))
        context['subscriber_count'] = ContentReactionAnswerSubscription.objects.get_subscriptions(self.object).count()
        # We need reading time expressed in minutes
        try:
            char_count = self.object.public_version.char_count
            if char_count:
                context['reading_time'] = int(
                    self.versioned_object.get_tree_level() * char_count /
                    settings.ZDS_APP['content']['characters_per_minute']
                )
        except ZeroDivisionError as e:
            logger.warning('could not compute reading time: setting characters_per_minute is set to zero (error=%s)', e)

        if self.request.user.is_authenticated:
            for reaction in context['reactions']:
                signals.content_read.send(sender=reaction.__class__, instance=reaction, user=self.request.user)
            signals.content_read.send(
                sender=self.object.__class__, instance=self.object, user=self.request.user, target=PublishableContent)
        if last_participation_is_old(self.object, self.request.user):
            mark_read(self.object, self.request.user)

        context['contributions'] = ContentContribution\
            .objects\
            .filter(content=self.object)\
            .order_by('contribution_role__position')
        context['content_suggestions_random'] = ContentSuggestion \
            .objects \
            .filter(publication=self.object) \
            .order_by('?')[:settings.ZDS_APP['content']['suggestions_per_page']]

        return context


class DisplayOnlineArticle(DisplayOnlineContent):
    """Displays the list of published articles"""

    current_content_type = 'ARTICLE'
    verbose_type_name = _('article')
    verbose_type_name_plural = _('articles')


class DisplayOnlineTutorial(DisplayOnlineContent):
    """Displays the list of published tutorials"""

    current_content_type = 'TUTORIAL'
    verbose_type_name = _('tutoriel')
    verbose_type_name_plural = _('tutoriels')


class DisplayOnlineOpinion(DisplayOnlineContent):
    """Displays the list of published articles"""

    current_content_type = 'OPINION'
    verbose_type_name = _('billet')
    verbose_type_name_plural = _('billets')


class DownloadOnlineContent(SingleOnlineContentViewMixin, DownloadViewMixin):
    """ Views that allow users to download 'extra contents' of the public version
    """

    requested_file = None
    allowed_types = ['md', 'html', 'pdf', 'epub', 'zip', 'tex']

    mimetypes = {'html': 'text/html',
                 'md': 'text/plain',
                 'pdf': 'application/pdf',
                 'epub': 'application/epub+zip',
                 'zip': 'application/zip',
                 'tex': 'application/x-latex'}

    def get_redirect_url(self, public_version):
        return public_version.content.public_version.get_absolute_url_to_extra_content(self.requested_file)

    def get(self, context, **response_kwargs):

        # fill the variables
        try:
            self.public_content_object = self.get_public_object()
        except MustRedirect as redirect_url:
            return HttpResponsePermanentRedirect(redirect_url.url)

        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()

        # check that type is ok
        if self.requested_file not in self.allowed_types:
            raise Http404("Le type du fichier n'est pas permis.")

        # check existence
        if not self.public_content_object.has_type(self.requested_file):
            raise Http404("Le type n'existe pas.")

        if self.requested_file == 'md' and not self.is_author and not self.is_staff:
            # download markdown is only for staff and author
            raise Http404("Seul le staff et l'auteur peuvent télécharger la version Markdown du contenu.")

        # set mimetype accordingly
        self.mimetype = self.mimetypes[self.requested_file]

        # set UTF-8 response for markdown
        if self.requested_file == 'md':
            self.mimetype += '; charset=utf-8'

        return super(DownloadOnlineContent, self).get(context, **response_kwargs)

    def get_filename(self):
        return self.public_content_object.content_public_slug + '.' + self.requested_file

    def get_contents(self):
        path = os.path.join(self.public_content_object.get_extra_contents_directory(), self.get_filename())
        try:
            response = open(path, 'rb').read()
        except OSError:
            raise Http404("Le fichier n'existe pas.")

        return response


class DownloadOnlineArticle(DownloadOnlineContent):

    current_content_type = 'ARTICLE'


class DownloadOnlineTutorial(DownloadOnlineContent):

    current_content_type = 'TUTORIAL'


class DownloadOnlineOpinion(DownloadOnlineContent):

    current_content_type = 'OPINION'


class DisplayOnlineContainer(SingleOnlineContentDetailViewMixin):
    """Base class that can show any content in any state"""

    template_name = 'tutorialv2/view/container_online.html'
    current_content_type = 'TUTORIAL'  # obviously, an article cannot have container !

    def get_context_data(self, **kwargs):
        context = super(DisplayOnlineContainer, self).get_context_data(**kwargs)
        container = search_container_or_404(self.versioned_object, self.kwargs)

        context['container'] = container
        context['pm_link'] = self.object.get_absolute_contact_url(_('À propos de'))

        context['formWarnTypo'] = WarnTypoForm(
            self.versioned_object, container, initial={'target': container.get_path(relative=True)})

        # pagination: search for `previous` and `next`, if available
        if not self.versioned_object.has_extracts():
            chapters = self.versioned_object.get_list_of_chapters()
            try:
                position = chapters.index(container)
            except ValueError:
                pass  # this is not (yet?) a chapter
            else:
                context['has_pagination'] = True
                context['previous'] = None
                context['next'] = None
                if position == 0:
                    context['previous'] = container.parent
                if position > 0:
                    previous_chapter = chapters[position - 1]
                    if previous_chapter.parent == container.parent:
                        context['previous'] = previous_chapter
                    else:
                        context['previous'] = container.parent
                if position < len(chapters) - 1:
                    next_chapter = chapters[position + 1]
                    if next_chapter.parent == container.parent:
                        context['next'] = next_chapter
                    else:
                        context['next'] = next_chapter.parent

        return context


class ListOnlineContents(ContentTypeMixin, ZdSPagingListView):
    """Displays the list of published contents"""

    context_object_name = 'public_contents'
    paginate_by = settings.ZDS_APP['content']['content_per_page']
    template_name = 'tutorialv2/index_online_contents.html'
    category = None
    subcategory = None
    tag = None
    current_content_type = None

    def get_queryset(self):
        """Filter the contents to obtain the list of contents of given type.
        If category parameter is provided, only contents which have this category will be listed.
        :return: list of contents with the right type
        :rtype: list of zds.tutorialv2.models.database.PublishedContent
        """
        sub_query = 'SELECT COUNT(*) FROM {} WHERE {}={}'.format(
            'tutorialv2_contentreaction',
            'tutorialv2_contentreaction.related_content_id',
            'tutorialv2_publishablecontent.id'
        )
        queryset = PublishedContent.objects \
            .filter(must_redirect=False)
        # this condition got more complexe with development of zep13
        # if we do filter by content_type, then every published content can be
        # displayed. Othewise, we have to be sure the content was expressly chosen by
        # someone with staff authorization. Another way to say it "it has to be a
        # validated content (article, tutorial), `ContentWithoutValidation` live their
        # own life in their own page.
        if self.current_content_type:
            queryset = queryset.filter(content_type=self.current_content_type)
        else:
            queryset = queryset.filter(~Q(content_type='OPINION'))
        # prefetch:
        queryset = queryset\
            .prefetch_related('content') \
            .prefetch_related('content__subcategory') \
            .prefetch_related('content__authors') \
            .select_related('content__licence') \
            .select_related('content__image') \
            .select_related('content__last_note') \
            .select_related('content__last_note__related_content') \
            .select_related('content__last_note__related_content__public_version') \
            .filter(pk=F('content__public_version__pk'))

        if 'category' in self.request.GET:
            self.subcategory = get_object_or_404(SubCategory, slug=self.request.GET.get('category'))
            queryset = queryset.filter(content__subcategory__in=[self.subcategory])

        if 'tag' in self.request.GET:
            self.tag = get_object_or_404(Tag, title=self.request.GET.get('tag').lower().strip())
            # TODO: fix me
            # different tags can have same slug such as C/C#/C++, as a first version we get all of them
            queryset = queryset.filter(content__tags__in=[self.tag])
        queryset = queryset.extra(select={'count_note': sub_query})
        return queryset.order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super(ListOnlineContents, self).get_context_data(**kwargs)
        for public_content in context['public_contents']:
            if public_content.content.last_note is not None:
                public_content.content.last_note.related_content = public_content.content
                public_content.content.public_version = public_content
                public_content.content.count_note = public_content.count_note

        context['category'] = self.category
        context['subcategory'] = self.subcategory
        context['tag'] = self.tag
        context['topbar_publication_categories'] = topbar_publication_categories(self.current_content_type)

        return context


class ListOpinions(ListOnlineContents):
    """Displays the list of published opinions"""

    current_content_type = 'OPINION'


class ViewPublications(TemplateView):
    templates = {
        1: 'tutorialv2/view/categories.html',
        2: 'tutorialv2/view/category.html',
        3: 'tutorialv2/view/subcategory.html',
        4: 'tutorialv2/view/browse.html',
    }
    handle_types = ['TUTORIAL', 'ARTICLE']

    level = 1
    max_last_contents = settings.ZDS_APP['content']['max_last_publications_level_1']
    template_name = templates[level]

    @staticmethod
    def categories_with_contents_count(handle_types):
        """Select categories with subcategories and contents count in two queries"""

        queryset_category = Category.objects.order_by('position')\
            .filter(categorysubcategory__subcategory__publishablecontent__publishedcontent__must_redirect=False)\
            .filter(categorysubcategory__subcategory__publishablecontent__type__in=handle_types)\
            .annotate(contents_count=Count('categorysubcategory__subcategory__publishablecontent__publishedcontent',
                                           distinct=True))\
            .distinct()

        queryset_subcategory = CategorySubCategory.objects.prefetch_related('subcategory', 'category')\
            .filter(is_main=True)\
            .order_by('category__id', 'subcategory__title')\
            .annotate(sub_contents_count=Count('subcategory__publishablecontent__publishedcontent', distinct=True))\
            .all()

        subcategories_sorted = defaultdict(list)
        for category_to_sub_category in queryset_subcategory:
            if category_to_sub_category.sub_contents_count:
                subcategories_sorted[category_to_sub_category.category.id].append(category_to_sub_category.subcategory)

        categories = queryset_category
        for category in categories:
            category.subcategories = subcategories_sorted[category.id]

        return categories

    @staticmethod
    def subcategories_with_contents_count(category, handle_types):
        """Rewritten to give the number of contents at the same time as the subcategories (in one query)"""

        # TODO: check if we can use ORM to do that
        sub_query = """
          SELECT COUNT(*) FROM `tutorialv2_publishedcontent`
          INNER JOIN `tutorialv2_publishablecontent`
            ON (`tutorialv2_publishedcontent`.`content_id` = `tutorialv2_publishablecontent`.`id`)
          INNER JOIN `tutorialv2_publishablecontent_subcategory`
            ON (`tutorialv2_publishablecontent`.`id` =
              `tutorialv2_publishablecontent_subcategory`.`publishablecontent_id`)
          WHERE (
            `tutorialv2_publishedcontent`.`must_redirect` = 0
            AND `tutorialv2_publishablecontent`.`type` IN ({})
            AND `tutorialv2_publishablecontent_subcategory`.`subcategory_id` =
              `utils_categorysubcategory`.`subcategory_id`)
        """.format(', '.join('\'{}\''.format(t) for t in handle_types))

        queryset = CategorySubCategory.objects \
            .filter(is_main=True, category=category) \
            .prefetch_related('subcategory')\
            .order_by('subcategory__title')\
            .extra(select={'contents_count': sub_query})

        subcategories = []

        for category_to_subcategory in queryset:
            subcategory = category_to_subcategory.subcategory
            subcategory.contents_count = category_to_subcategory.contents_count
            subcategories.append(subcategory)

        return subcategories

    def get_context_data(self, **kwargs):
        context = super(ViewPublications, self).get_context_data(**kwargs)

        if self.kwargs.get('slug', False):
            self.level = 2
            self.max_last_contents = settings.ZDS_APP['content']['max_last_publications_level_2']
        if self.kwargs.get('slug_category', False):
            self.level = 3
            self.max_last_contents = settings.ZDS_APP['content']['max_last_publications_level_3']
        if self.request.GET.get('category', False) or \
                self.request.GET.get('subcategory', False) or \
                self.request.GET.get('type', False) or \
                self.request.GET.get('tag', False):
            self.level = 4
            self.max_last_contents = 50

        self.template_name = self.templates[self.level]
        recent_kwargs = {}

        if self.level == 1:
            # get categories and subcategories
            categories = ViewPublications.categories_with_contents_count(self.handle_types)

            context['categories'] = categories
            context['content_count'] = PublishedContent.objects \
                .last_contents(content_type=self.handle_types, with_comments_count=False) \
                .count()

        elif self.level == 2:
            context['category'] = get_object_or_404(Category, slug=self.kwargs.get('slug'))
            context['subcategories'] = ViewPublications.subcategories_with_contents_count(
                context['category'], self.handle_types)
            recent_kwargs['subcategories'] = context['subcategories']

        elif self.level == 3:
            subcategory = get_object_or_404(SubCategory, slug=self.kwargs.get('slug'))
            context['category'] = subcategory.get_parent_category()

            if context['category'].slug != self.kwargs.get('slug_category'):
                raise Http404('wrong slug for category ({} != {})'.format(
                    context['category'].slug, self.kwargs.get('slug_category')))

            context['subcategory'] = subcategory
            recent_kwargs['subcategories'] = [subcategory]

        elif self.level == 4:
            category = self.request.GET.get('category', None)
            subcategory = self.request.GET.get('subcategory', None)
            subcategories = None
            if category is not None:
                context['category'] = get_object_or_404(Category, slug=category)
                subcategories = context['category'].get_subcategories()
            elif subcategory is not None:
                subcategory = get_object_or_404(SubCategory, slug=self.request.GET.get('subcategory'))
                context['category'] = subcategory.get_parent_category()
                context['subcategory'] = subcategory
                subcategories = [subcategory]

            content_type = self.handle_types
            context['type'] = None
            if 'type' in self.request.GET:
                _type = self.request.GET.get('type', '').upper()
                if _type in self.handle_types:
                    content_type = _type
                    context['type'] = TYPE_CHOICES_DICT[_type]
                else:
                    raise Http404('wrong type {}'.format(_type))

            tag = self.request.GET.get('tag', None)
            tags = None
            if tag is not None:
                tags = [get_object_or_404(Tag, slug=slugify(tag))]
                context['tag'] = tags[0]

            contents_queryset = PublishedContent.objects.last_contents(
                subcategories=subcategories,
                tags=tags,
                content_type=content_type)
            items_per_page = settings.ZDS_APP['content']['content_per_page']
            make_pagination(
                context,
                self.request,
                contents_queryset,
                items_per_page,
                context_list_name='filtered_contents',
                with_previous_item=False)

        if self.level < 4:
            last_articles = PublishedContent.objects.last_contents(
                **dict(content_type='ARTICLE', **recent_kwargs))
            context['last_articles'] = last_articles[:self.max_last_contents]
            context['more_articles'] = last_articles.count() > self.max_last_contents

            last_tutorials = PublishedContent.objects.last_contents(
                **dict(content_type='TUTORIAL', **recent_kwargs))
            context['last_tutorials'] = last_tutorials[:self.max_last_contents]
            context['more_tutorials'] = last_tutorials.count() > self.max_last_contents

            context['beta_forum'] = Forum.objects\
                .prefetch_related('category')\
                .filter(pk=settings.ZDS_APP['forum']['beta_forum_id'])\
                .last()

        context['level'] = self.level
        return context


class SendNoteFormView(LoggedWithReadWriteHability, SingleOnlineContentFormViewMixin):

    denied_if_lock = True
    form_class = NoteForm
    check_as = True
    reaction = None
    template_name = 'tutorialv2/comment/new.html'

    quoted_reaction_text = ''
    new_note = False

    def get_form_kwargs(self):
        kwargs = super(SendNoteFormView, self).get_form_kwargs()
        kwargs['content'] = self.object
        kwargs['reaction'] = None

        # handle the case when another user have post something in between
        if 'last_note' in self.request.POST and self.request.POST['last_note'].strip() != '':
            try:
                last_note = int(self.request.POST['last_note'])
            except ValueError:
                pass
            else:
                if self.object.last_note and last_note != self.object.last_note.pk:
                    self.new_note = True
                    kwargs['last_note'] = self.object.last_note.pk

        return kwargs

    def get_initial(self):
        initial = super(SendNoteFormView, self).get_initial()

        if self.quoted_reaction_text:
            initial['text'] = self.quoted_reaction_text

        return initial

    def get_context_data(self, **kwargs):
        context = super(SendNoteFormView, self).get_context_data(**kwargs)

        # handle the case were there is a new message in the discussion
        if self.new_note:
            context['newnote'] = True

        # last few messages
        context['notes'] = ContentReaction.objects\
            .select_related('author') \
            .select_related('author__profile') \
            .select_related('hat') \
            .select_related('editor') \
            .prefetch_related('alerts_on_this_comment') \
            .prefetch_related('alerts_on_this_comment__author') \
            .filter(related_content=self.object) \
            .order_by('-pubdate')[:settings.ZDS_APP['content']['notes_per_page']]

        return context

    def get(self, request, *args, **kwargs):

        # handle quoting case
        if 'cite' in self.request.GET:
            try:
                cited_pk = int(self.request.GET['cite'])
            except ValueError:
                raise Http404('L\'argument `cite` doit être un entier.')

            reaction = ContentReaction.objects.filter(pk=cited_pk).first()

            if reaction:
                if not reaction.is_visible:
                    raise PermissionDenied

                text = '\n'.join('> ' + line for line in reaction.text.split('\n'))
                text += '\nSource: [{}]({})'.format(reaction.author.username, reaction.get_absolute_url())

                if self.request.is_ajax():
                    return StreamingHttpResponse(json_handler.dumps({'text': text}, ensure_ascii=False))
                else:
                    self.quoted_reaction_text = text
        try:
            return super(SendNoteFormView, self).get(request, *args, **kwargs)
        except MustRedirect:
            # if someone changed the pk argument, and reached a 'must redirect' public object
            raise Http404(
                "Aucun contenu public trouvé avec l'identifiant {}".format(str(self.request.GET.get('pk', 0))))

    def post(self, request, *args, **kwargs):

        if 'preview' in request.POST and request.is_ajax():
            content = render_to_response('misc/preview.part.html', {'text': request.POST['text']})
            return StreamingHttpResponse(content)
        else:
            return super(SendNoteFormView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        if self.check_as and self.object.antispam(self.request.user):
            raise PermissionDenied

        if 'preview' in self.request.POST:
            return self.form_invalid(form)

        is_new = False

        if self.reaction:  # it's an edition
            edit = CommentEdit()
            edit.comment = self.reaction
            edit.editor = self.request.user
            edit.original_text = self.reaction.text
            edit.save()

            self.reaction.update = datetime.now()
            self.reaction.editor = self.request.user
            self.reaction.hat = get_hat_from_request(self.request, self.reaction.author)

        else:
            self.reaction = ContentReaction()
            self.reaction.pubdate = datetime.now()
            self.reaction.author = self.request.user
            self.reaction.position = self.object.get_note_count() + 1
            self.reaction.related_content = self.object
            self.reaction.hat = get_hat_from_request(self.request)

            is_new = True

        # also treat alerts if editor is a moderator
        if self.request.user != self.reaction.author and not is_new:
            alerts = Alert.objects.filter(comment__pk=self.reaction.pk, solved=False)
            for alert in alerts:
                alert.solve(self.request.user, _('Le message a été modéré.'))

        self.reaction.update_content(
            form.cleaned_data['text'],
            on_error=lambda m: messages.error(
                self.request,
                _('Erreur du serveur Markdown: {}').format(
                    '\n- '.join(m))))
        self.reaction.ip_address = get_client_ip(self.request)
        self.reaction.save()

        if is_new:  # we first need to save the reaction
            self.object.last_note = self.reaction
            self.object.save(update_date=False, force_slug_update=False)

        self.success_url = self.reaction.get_absolute_url()
        return super(SendNoteFormView, self).form_valid(form)


class UpdateNoteView(SendNoteFormView):
    check_as = False
    template_name = 'tutorialv2/comment/edit.html'
    form_class = NoteEditForm

    def get_form_kwargs(self):
        kwargs = super(UpdateNoteView, self).get_form_kwargs()
        if 'message' in self.request.GET and self.request.GET['message'].isdigit():
            self.reaction = ContentReaction.objects\
                .prefetch_related('author') \
                .filter(pk=int(self.request.GET['message'])) \
                .first()
            if not self.reaction:
                raise Http404('Aucun commentaire : ' + self.request.GET['message'])
            if self.reaction.author.pk != self.request.user.pk and not self.is_staff:
                raise PermissionDenied()

            kwargs['reaction'] = self.reaction
        else:
            raise Http404("Le paramètre 'message' doit être un nombre entier positif.")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UpdateNoteView, self).get_context_data(**kwargs)

        if self.reaction:
            context['reaction'] = self.reaction

            if self.reaction.author != self.request.user:
                messages.add_message(
                    self.request, messages.WARNING,
                    _('Vous éditez ce message en tant que modérateur (auteur : {}).'
                      ' Ne faites pas de bêtise !')
                    .format(self.reaction.author.username))

                # show alert, if any
                alerts = Alert.objects.filter(comment__pk=self.reaction.pk, solved=False)
                if alerts.count():
                    msg_alert = _('Attention, en éditant ce message vous résolvez également '
                                  'les alertes suivantes : {}') \
                        .format(', '.join(
                            ['« {} » (signalé par {})'.format(a.text, a.author.username) for a in alerts]
                        ))
                    messages.warning(self.request, msg_alert)

        return context

    def form_valid(self, form):
        if 'message' in self.request.GET and self.request.GET['message'].isdigit():
            self.reaction = ContentReaction.objects\
                .filter(pk=int(self.request.GET['message'])) \
                .prefetch_related('author') \
                .first()
            if self.reaction is None:
                raise Http404("Il n'y a aucun commentaire.")
            if self.reaction.author != self.request.user:
                if not self.request.user.has_perm('tutorialv2.change_contentreaction'):
                    raise PermissionDenied
        else:
            messages.error(self.request, _('Oh non ! Une erreur est survenue dans la requête !'))
            return self.form_invalid(form)

        return super(UpdateNoteView, self).form_valid(form)


class HideReaction(FormView, LoginRequiredMixin):
    http_method_names = ['post']

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(HideReaction, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            pk = int(self.kwargs['pk'])
            text = ''
            if 'text_hidden' in self.request.POST:
                text = self.request.POST['text_hidden'][:80]  # TODO: Make it less static
            reaction = get_object_or_404(ContentReaction, pk=pk)
            if not self.request.user.has_perm('tutorialv2.change_contentreaction') and \
                    not self.request.user.pk == reaction.author.pk:
                raise PermissionDenied
            reaction.hide_comment_by_user(self.request.user, text)
            return redirect(reaction.get_absolute_url())
        except (IndexError, ValueError, MultiValueDictKeyError):
            raise Http404('Vous ne pouvez pas cacher cette réaction.')


class ShowReaction(FormView, LoggedWithReadWriteHability, PermissionRequiredMixin):

    permissions = ['tutorialv2.change_contentreaction']
    http_method_names = ['post']

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(ShowReaction, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            pk = int(self.kwargs['pk'])
            reaction = get_object_or_404(ContentReaction, pk=pk)
            reaction.is_visible = True
            reaction.save()

            return redirect(reaction.get_absolute_url())

        except (IndexError, ValueError, MultiValueDictKeyError):
            raise Http404('Aucune réaction trouvée.')


class SendContentAlert(FormView, LoginRequiredMixin):
    http_method_names = ['post']

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(SendContentAlert, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            content_pk = int(self.kwargs['pk'])
        except (KeyError, ValueError):
            raise Http404('Identifiant manquant ou conversion en entier impossible.')
        content = get_object_or_404(PublishableContent, pk=content_pk)

        if len(request.POST['signal_text'].strip()) == 0:
            messages.error(request, _('La raison du signalement ne peut pas être vide.'))
        else:
            alert = Alert(
                author=request.user,
                content=content,
                scope='CONTENT',
                text=request.POST['signal_text'],
                pubdate=datetime.now())
            alert.save()

            human_content_type = TYPE_CHOICES_DICT[content.type].lower()
            messages.success(
                self.request,
                _('Ce {} a bien été signalé aux modérateurs.').format(human_content_type))

        return redirect(content.get_absolute_url_online())


class SolveContentAlert(FormView, LoginRequiredMixin):

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(SolveContentAlert, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm('tutorialv2.change_contentreaction'):
            raise PermissionDenied
        try:
            alert = get_object_or_404(Alert, pk=int(request.POST['alert_pk']))
            content = PublishableContent.objects.get(pk=alert.content.id)
        except (KeyError, ValueError):
            raise Http404("L'alerte n'existe pas.")

        resolve_reason = ''
        msg_title = ''
        msg_content = ''
        if 'text' in request.POST and request.POST['text']:
            resolve_reason = request.POST['text']
            authors = alert.content.authors.values_list('username', flat=True)
            authors = ', '.join(authors)
            msg_title = _("Résolution d'alerte : {0}").format(content.title)
            msg_content = render_to_string(
                'tutorialv2/messages/resolve_alert.md', {
                    'content': content,
                    'url': content.get_absolute_url_online(),
                    'name': alert.author.username,
                    'target_name': authors,
                    'modo_name': request.user.username,
                    'message': '\n'.join(['> ' + line for line in resolve_reason.split('\n')]),
                    'alert_text': '\n'.join(['> ' + line for line in alert.text.split('\n')])
                })
        alert.solve(request.user, resolve_reason, msg_title, msg_content)

        messages.success(self.request, _("L'alerte a bien été résolue."))
        return redirect(content.get_absolute_url_online())


class SendNoteAlert(FormView, LoginRequiredMixin):
    http_method_names = ['post']

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(SendNoteAlert, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            reaction_pk = int(self.kwargs['pk'])
        except (KeyError, ValueError):
            raise Http404("Impossible de convertir l'identifiant en entier.")
        reaction = get_object_or_404(ContentReaction, pk=reaction_pk)

        if len(request.POST['signal_text'].strip()) == 0:
            messages.error(request, _('La raison du signalement ne peut pas être vide.'))
        else:
            alert = Alert(
                author=request.user,
                comment=reaction,
                scope=reaction.related_content.type,
                text=request.POST['signal_text'],
                pubdate=datetime.now())
            alert.save()

            messages.success(self.request, _('Ce commentaire a bien été signalé aux modérateurs.'))

        return redirect(reaction.get_absolute_url())


class SolveNoteAlert(FormView, LoginRequiredMixin):

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(SolveNoteAlert, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm('tutorialv2.change_contentreaction'):
            raise PermissionDenied
        try:
            alert = get_object_or_404(Alert, pk=int(request.POST['alert_pk']))
            note = ContentReaction.objects.get(pk=alert.comment.id)
        except (KeyError, ValueError):
            raise Http404("L'alerte n'existe pas.")

        resolve_reason = ''
        msg_title = ''
        msg_content = ''
        if 'text' in request.POST and request.POST['text']:
            resolve_reason = request.POST['text']
            msg_title = _("Résolution d'alerte : {0}").format(note.related_content.title)
            msg_content = render_to_string(
                'tutorialv2/messages/resolve_alert.md', {
                    'content': note.related_content,
                    'url': note.related_content.get_absolute_url_online(),
                    'name': alert.author.username,
                    'target_name': note.author.username,
                    'modo_name': request.user.username,
                    'message': '\n'.join(['> ' + line for line in resolve_reason.split('\n')]),
                    'alert_text': '\n'.join(['> ' + line for line in alert.text.split('\n')])
                })
        alert.solve(request.user, resolve_reason, msg_title, msg_content)

        messages.success(self.request, _("L'alerte a bien été résolue."))
        return redirect(note.get_absolute_url())


class FollowContentReaction(LoggedWithReadWriteHability, SingleOnlineContentViewMixin, FormView):
    redirection_is_needed = False

    def post(self, request, *args, **kwargs):
        response = {}
        self.public_content_object = self.get_public_object()
        if 'follow' in request.POST:
            response['follow'] = ContentReactionAnswerSubscription.objects\
                .toggle_follow(self.get_object(), self.request.user).is_active
            response['subscriberCount'] = ContentReactionAnswerSubscription\
                .objects.get_subscriptions(self.get_object()).count()
        elif 'email' in request.POST:
            response['follow'] = ContentReactionAnswerSubscription.objects\
                .toggle_follow(self.get_object(), self.request.user, True).is_active
        if self.request.is_ajax():
            return HttpResponse(json_handler.dumps(response), content_type='application/json')
        return redirect(self.get_object().get_absolute_url())


class RequestFeaturedContent(LoggedWithReadWriteHability, FeatureableMixin, SingleOnlineContentViewMixin, FormView):
    redirection_is_needed = False

    def featured_request_allowed(self):
        """Featured request is not allowed on obsolete content and opinions
        """
        return self.object.type != 'OPINION' and not self.object.is_obsolete

    def post(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()

        response = dict()
        response['requesting'], response['newCount'] = self.toogle_featured_request(request.user)
        if self.request.is_ajax():
            return HttpResponse(json_handler.dumps(response), content_type='application/json')
        return redirect(self.public_content_object.get_absolute_url_online())


class FollowNewContent(LoggedWithReadWriteHability, FormView):

    @staticmethod
    def perform_follow(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user).is_active

    @staticmethod
    def perform_follow_by_email(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user, True).is_active

    def post(self, request, *args, **kwargs):
        response = {}

        # get user to follow
        try:
            user_to_follow = User.objects.get(pk=kwargs['pk'])
        except User.DoesNotExist:
            raise Http404

        # follow content if user != user_to_follow only
        if user_to_follow == request.user:
            raise PermissionDenied

        with transaction.atomic():
            if 'follow' in request.POST:
                response['follow'] = self.perform_follow(user_to_follow, request.user)
                response['subscriberCount'] = NewPublicationSubscription.objects \
                    .get_subscriptions(user_to_follow).count()
            elif 'email' in request.POST:
                response['email'] = self.perform_follow_by_email(user_to_follow, request.user)

        if request.is_ajax():
            return HttpResponse(json_handler.dumps(response), content_type='application/json')
        return redirect(request.META.get('HTTP_REFERER'))


class TagsListView(ListView):

    model = Tag
    template_name = 'tutorialv2/view/tags.html'
    context_object_name = 'tags'
    displayed_types = ['TUTORIAL', 'ARTICLE']

    def get_queryset(self):
        if 'type' in self.request.GET:
            t = self.request.GET.get('type').upper()
            if t not in CONTENT_TYPE_LIST:
                raise Http404('type {} unknown'.format(t))
            self.displayed_types = [t]

        return PublishedContent.objects.get_top_tags(self.displayed_types)

    def get_context_data(self, **kwargs):
        context = super(TagsListView, self).get_context_data(**kwargs)

        context['tags_to_display'] = 'publications'

        if len(self.displayed_types) == 1:
            context['tags_to_display'] = self.displayed_types[0]

        return context


class ContentStatisticsView(SingleOnlineContentDetailViewMixin, FormView):
    template_name = 'tutorialv2/stats/index.html'
    form_class = ContentCompareStatsURLForm
    urls = []
    CACHE_PATH = str(settings.BASE_DIR / '.ga-api-cache')
    SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
    DISCOVERY_URI = 'https://analyticsreporting.googleapis.com/$discovery/rest'
    CLIENT_SECRETS_PATH = str(settings.BASE_DIR / 'api_analytics_secrets.json')
    VIEW_ID = settings.ZDS_APP['stats_ga_viewid']

    def post(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['urls'] = [(named_url.url, named_url.name) for named_url in self.get_urls_to_render()]
        return kwargs

    def form_valid(self, form):
        self.urls = form.cleaned_data['urls']
        return super().get(self.request)

    def get_urls_to_render(self):
        all_named_urls = self.get_content_urls()
        base_list = self.request.GET.getlist('urls', None) or self.urls
        if base_list:
            return [named_url for named_url in all_named_urls if named_url.url in base_list]
        else:
            return all_named_urls

    def get_content_urls(self):
        content = self.versioned_object
        urls = [NamedUrl(content.title, content.get_absolute_url_online(), 0)]
        if content.has_extracts():
            return urls
        for child in content.children:
            urls.append(NamedUrl(child.title, child.get_absolute_url_online(), 1))
            if not child.has_extracts():
                for subchild in child.children:
                    urls.append(NamedUrl(subchild.title, subchild.get_absolute_url_online(), 2))
        return urls

    def config_ga_credentials(self):
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CLIENT_SECRETS_PATH, self.SCOPES)
            http = credentials.authorize(Http(cache=self.CACHE_PATH))
            analytics = build('analytics',
                              'v4',
                              http=http,
                              discoveryServiceUrl=self.DISCOVERY_URI,
                              cache_discovery=False)
            return analytics
        except (ValueError, FileNotFoundError, ServerNotFoundError) as e:
            messages.error(self.request, _("Erreur de configuration de l'API Analytics. "
                                           "Merci de contacter l'équipe des développeurs. « {} »").format(str(e)))
            return None

    @staticmethod
    def get_ga_filters_from_urls(urls):
        filters = [{'operator': 'EXACT',
                    'dimensionName': 'ga:pagePath',
                    'expressions': u.url}
                   for u in urls]
        return filters

    def get_cumulative_stats_by_url(self, urls, report):
        # Build an array of type arr[url] = {'pageviews': X, 'avgTimeOnPage': y}
        try:
            rows = report['data']['rows']
        except KeyError:
            messages.error(self.request, _("Aucune donnée de statistiques cumulées n'est disponible"))
            return []

        # Backfill data with zeroes
        data = {url.url: defaultdict(int) for url in urls}
        for r in rows:
            url = r['dimensions'][0]
            # avgTimeOnPage is convert to float then int to remove useless decimal part
            data[url] = {'pageviews': r['metrics'][0]['values'][0],
                         'avgTimeOnPage': int(float(r['metrics'][0]['values'][1])),
                         'users': r['metrics'][0]['values'][2],
                         'newUsers': r['metrics'][0]['values'][3],
                         'sessions': r['metrics'][0]['values'][4]}

        # Build the response array by matching NamedUrl and data[url]
        api_raw = [{'url': url,
                    'pageviews': data[url.url].get('pageviews', 0),
                    'avgTimeOnPage': data[url.url].get('avgTimeOnPage', 0),
                    'users': data[url.url].get('users', 0),
                    'newUsers': data[url.url].get('newUsers', 0),
                    'sessions': data[url.url].get('sessions', 0)} for url in urls]
        return api_raw

    def get_stats(self, urls, report, display_mode, start, end):
        try:
            rows = report['data']['rows']
        except KeyError:
            messages.error(self.request, _("Aucune donnée de statistiques détaillées n'est disponible"))
            return []

        api_raw = []
        metrics = [r['name'][3:] for r in report['columnHeader']['metricHeader']['metricHeaderEntries']]

        period = (end - start).days

        data = {}
        if display_mode in ('global', 'details'):
            # Prepare empty val list (backfill with zeros for missing dates)
            for i in range(period + 1):
                day = (start + timedelta(days=i)).strftime('%Y-%m-%d')
                data[day] = {m: 0 for m in metrics}
            # Fill in data
            for r in rows:
                data_date = r['dimensions'][0]
                data_date = '{}-{}-{}'.format(data_date[0:4], data_date[4:6], data_date[6:8])
                for i, m in enumerate(metrics):
                    data[data_date][m] = r['metrics'][0]['values'][i]

            stats = {}
            for i, m in enumerate(metrics):
                stats[m] = []
                for d in data:
                    stats[m].append({'date': d, m: data[d][m]})
                stats[m] = sorted(stats[m], key=lambda k: k['date'])
            api_raw = [{'label': _('Global'),
                        'stats': stats}]
        else:

            data = {}

            for url in urls:
                data[url.url] = {'stats': {}}
                # Prepare empty val list (backfill with zeros for missing dates)
                for i in range(period + 1):
                    day = (start + timedelta(days=i)).strftime('%Y-%m-%d')
                    data[url.url]['stats'][day] = defaultdict(int)

            for r in rows:
                url = r['dimensions'][1]
                data_date = r['dimensions'][0]
                data_date = '{}-{}-{}'.format(data_date[0:4], data_date[4:6], data_date[6:8])

                for i, m in enumerate(metrics):
                    data[url]['stats'][data_date][m] = r['metrics'][0]['values'][i]

            for url in urls:
                stats = {}
                for i, m in enumerate(metrics):
                    stats[m] = []
                    for d in data[url.url]['stats']:
                        stats[m].append({'date': d, m: data[url.url]['stats'][d].get(m, 0)})
                    stats[m] = sorted(stats[m], key=lambda k: k['date'])
                element = {'label': url.name, 'stats': stats}
                api_raw.append(element)

        return api_raw

    def get_simple_stat(self, report, info):
        try:
            rows = report['data']['rows']
        except KeyError:
            messages.error(self.request, _("Aucune donnée n'est disponible (métrique « {} »)").format(info))
            return []
        api_raw = OrderedDict()
        for r in rows:
            api_raw[r['dimensions'][0]] = r['metrics'][0]['values'][0]
        return api_raw

    def get_referrer_stats(self, report):
        return self.get_simple_stat(report, 'referrer')

    def get_keyword_stats(self, report):
        return self.get_simple_stat(report, 'keyword')

    def get_all_stats(self, urls, start, end, display_mode):
        # nb_days = (end - start).days
        analytics = self.config_ga_credentials()
        if not analytics:
            return ([], [], [], [])

        # Filters to get all needed pages only
        filters = self.get_ga_filters_from_urls(urls)
        date_ranges = {'startDate': start.strftime('%Y-%m-%d'),
                       'endDate': end.strftime('%Y-%m-%d')}

        metrics = [{'expression': 'ga:pageviews'},
                   {'expression': 'ga:avgTimeOnPage'},
                   {'expression': 'ga:users'},
                   {'expression': 'ga:newUsers'},
                   {'expression': 'ga:sessions'}]

        table_data_report = {
            'viewId': self.VIEW_ID,
            'dateRanges': date_ranges,
            'metrics': metrics,
            'dimensions': [{'name': 'ga:pagePath'}],
            'dimensionFilterClauses': [{'filters': filters}],
        }

        referrer_report = {
            'viewId': self.VIEW_ID,
            'dateRanges': date_ranges,
            'metrics': [{'expression': 'ga:visits'}],
            'dimensions': [{'name': 'ga:fullReferrer'}],
            'orderBys': [{'fieldName': 'ga:visits', 'sortOrder': 'DESCENDING'}],
            'dimensionFilterClauses': [{'filters': filters}],
        }

        keyword_report = {
            'viewId': self.VIEW_ID,
            'dateRanges': date_ranges,
            'metrics': [{'expression': 'ga:visits'}],
            'dimensions': [{'name': 'ga:keyword'}],
            'orderBys': [{'fieldName': 'ga:visits', 'sortOrder': 'DESCENDING'}],
            'dimensionFilterClauses': [{'filters': filters}],
        }

        if display_mode in ('global', 'details'):
            # Find level 0 url
            if display_mode == 'global':
                target_url = [u for u in urls if u.level == 0]
                filters = [{'operator': 'BEGINS_WITH',
                            'dimensionName': 'ga:pagePath',
                            'expressions': target_url[0].url}]
            else:
                target_url = [urls[0]]
                filters = self.get_ga_filters_from_urls(target_url)

        dimensions = [{'name': 'ga:date'}]
        if display_mode == 'comparison':
            dimensions.append({'name': 'ga:pagePath'})
        graphs_data_report = {
            'viewId': self.VIEW_ID,
            'dateRanges': date_ranges,
            'metrics': metrics,
            'dimensions': dimensions,
            'dimensionFilterClauses': [{'filters': filters}]
        }

        try:
            response = analytics.reports().batchGet(
                body={'reportRequests': [graphs_data_report, table_data_report, referrer_report, keyword_report]}
            ).execute()
        except googleapiclient.errors.HttpError as e:
            messages.error(self.request,
                           _("Un problème a eu lieu lors de la requête vers l'API Google Analytics. « {} »").format(e))
            return ([], [], [], [])

        return (
            self.get_stats(urls, response['reports'][0], display_mode, start, end),
            self.get_cumulative_stats_by_url(urls, response['reports'][1]),
            self.get_referrer_stats(response['reports'][2]),
            self.get_keyword_stats(response['reports'][3])
        )

    def get_start_and_end_dates(self):
        end_date = self.request.GET.get('end_date', None)
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except TypeError:
            end_date = date.today()
        except ValueError:
            end_date = date.today()
            messages.error(self.request, _('La date de fin fournie est invalide.'))

        start_date = self.request.GET.get('start_date', None)
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except TypeError:
            start_date = end_date - timedelta(days=7)
        except ValueError:
            start_date = end_date - timedelta(days=7)
            messages.error(self.request, _('La date de début fournie est invalide.'))

        if start_date > end_date:
            end_date, start_date = start_date, end_date

        return start_date, end_date

    def get_display_mode(self, urls):
        # TODO make display_mode an enum ?
        # Good idea, but not straightforward for the template integration
        if len(urls) == 1:
            return 'details'
        if len(urls) == len(self.get_content_urls()):
            return 'global'
        return 'comparison'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not (self.is_author or self.is_staff):
            raise PermissionDenied

        urls = self.get_urls_to_render()
        start_date, end_date = self.get_start_and_end_dates()
        display_mode = self.get_display_mode(urls)
        all_stats = self.get_all_stats(urls, start_date, end_date, display_mode)

        context.update({
            'display': display_mode,
            'urls': urls,
            'stats': all_stats[0],  # Graph
            'cumulative_stats_by_url': all_stats[1],  # Table data
            'referrers': all_stats[2],
            'keywords': all_stats[3],
        })
        return context
