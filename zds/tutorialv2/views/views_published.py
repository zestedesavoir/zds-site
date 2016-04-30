# coding: utf-8
from datetime import datetime
import json as json_writer
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponsePermanentRedirect, StreamingHttpResponse, HttpResponse
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, FormView, ListView

from zds.member.decorator import LoggedWithReadWriteHability, LoginRequiredMixin, PermissionRequiredMixin
from zds.member.views import get_client_ip
from zds.notification import signals
from zds.notification.models import ContentReactionAnswerSubscription, NewPublicationSubscription
from zds.tutorialv2.forms import RevokeValidationForm, WarnTypoForm, NoteForm, NoteEditForm, UnpublicationForm
from zds.tutorialv2.mixins import SingleOnlineContentDetailViewMixin, SingleOnlineContentViewMixin, DownloadViewMixin, \
    ContentTypeMixin, SingleOnlineContentFormViewMixin, MustRedirect
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent, ContentReaction
from zds.tutorialv2.utils import search_container_or_404, last_participation_is_old, mark_read
from zds.utils.models import CommentVote, SubCategory, Alert, Tag
from zds.utils.paginator import make_pagination, ZdSPagingListView
from zds.utils.templatetags.topbar import top_categories_content

logger = logging.getLogger('zds.tutorialv2')


class RedirectContentSEO(RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        """Redirects the user to the new url"""
        obj = get_object_or_404(PublishableContent, old_pk=int(kwargs.get('pk')), type='TUTORIAL')
        if not obj.in_public():
            raise Http404(u"Aucun contenu public n'est disponible avec cet identifiant.")
        kwargs['parent_container_slug'] = str(kwargs['p2']) + '_' + kwargs['parent_container_slug']
        kwargs['container_slug'] = str(kwargs['p3']) + '_' + kwargs['container_slug']
        obj = search_container_or_404(obj.load_version(public=True), kwargs)

        return obj.get_absolute_url_online()


class DisplayOnlineContent(SingleOnlineContentDetailViewMixin):
    """Base class that can show any online content"""

    model = PublishedContent
    template_name = 'tutorialv2/view/content_online.html'

    current_content_type = ''
    verbose_type_name = _(u'contenu')
    verbose_type_name_plural = _(u'contenus')

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super(DisplayOnlineContent, self).get_context_data(**kwargs)

        if context['is_staff']:
            context['formRevokeValidation'] = RevokeValidationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})
            context['formUnpublication'] = UnpublicationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})

        context['formWarnTypo'] = WarnTypoForm(self.versioned_object, self.versioned_object)

        queryset_reactions = ContentReaction.objects\
            .select_related('author')\
            .select_related('author__profile')\
            .select_related('editor')\
            .prefetch_related('alerts')\
            .prefetch_related('alerts__author')\
            .filter(related_content__pk=self.object.pk)\
            .order_by('pubdate')

        # pagination of articles
        context['paginate_articles'] = False

        if self.object.type == 'ARTICLE':
            # fetch all articles in order to find the previous and the next one
            all_articles = \
                [a for a in PublishedContent.objects
                    .filter(content_type='ARTICLE', must_redirect=False)
                    .order_by('publication_date')
                    .all()]
            articles_count = len(all_articles)

            try:
                position = all_articles.index(self.public_content_object)
            except ValueError:
                pass  # for an unknown reason, the article is not in the list. This should not happen
            else:
                context['paginate_articles'] = True
                context['previous_article'] = None
                context['next_article'] = None

                if position > 0:
                    context['previous_article'] = all_articles[position - 1]
                if position < articles_count - 1:
                    context['next_article'] = all_articles[position + 1]

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

        context['isantispam'] = self.object.antispam()
        context['pm_link'] = self.object.get_absolute_contact_url(_(u'À propos de'))
        context['subscriber_count'] = ContentReactionAnswerSubscription.objects.get_subscriptions(self.object).count()
        # We need reading time expressed in minutes
        try:
            context['reading_time'] = (self.object.public_version.char_count /
                                       settings.ZDS_APP['content']['sec_per_minute'])
        except ZeroDivisionError as e:
            logger.warning('could not compute reading time : setting sec_per_minute is set to zero (error=%s)', e)

        if self.request.user.is_authenticated():
            for reaction in context['reactions']:
                signals.content_read.send(sender=reaction.__class__, instance=reaction, user=self.request.user)
            signals.content_read.send(
                sender=self.object.__class__, instance=self.object, user=self.request.user, target=PublishableContent)
        if last_participation_is_old(self.object, self.request.user):
            mark_read(self.object, self.request.user)

        return context


class DisplayOnlineArticle(DisplayOnlineContent):
    """Displays the list of published articles"""

    current_content_type = 'ARTICLE'
    verbose_type_name = _(u'article')
    verbose_type_name_plural = _(u'articles')


class DisplayOnlineTutorial(DisplayOnlineContent):
    """Displays the list of published tutorials"""

    current_content_type = 'TUTORIAL'
    verbose_type_name = _(u'tutoriel')
    verbose_type_name_plural = _(u'tutoriels')


class DisplayOnlineOpinion(DisplayOnlineContent):
    """Displays the list of published articles"""

    current_content_type = "OPINION"
    verbose_type_name = _(u'billet')
    verbose_type_name_plural = _(u'billets')


class DownloadOnlineContent(SingleOnlineContentViewMixin, DownloadViewMixin):
    """ Views that allow users to download 'extra contents' of the public version
    """

    requested_file = None
    allowed_types = ['md', 'html', 'pdf', 'epub', 'zip']

    mimetypes = {'html': 'text/html',
                 'md': 'text/plain',
                 'pdf': 'application/pdf',
                 'epub': 'application/epub+zip',
                 'zip': 'application/zip'}

    def get_redirect_url(self, public_version):
        return public_version.content.public_version.get_absolute_url_to_extra_content(self.requested_file)

    def get(self, context, **response_kwargs):

        # fill the variables
        try:
            self.public_content_object = self.get_public_object()
        except MustRedirect as redirect_url:
            return HttpResponsePermanentRedirect(redirect_url)

        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()

        # check that type is ok
        if self.requested_file not in self.allowed_types:
            raise Http404(u"Le type du fichier n'est pas permis.")

        # check existence
        if not self.public_content_object.have_type(self.requested_file):
            raise Http404(u"Le type n'existe pas.")

        if self.requested_file == 'md' and not self.is_author and not self.is_staff:
            # download markdown is only for staff and author
            raise Http404(u"Seul le staff et l'auteur peuvent télécharger la version Markdown du contenu.")

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
        except IOError:
            raise Http404(u"Le fichier n'existe pas.")

        return response


class DownloadOnlineArticle(DownloadOnlineContent):

    current_content_type = 'ARTICLE'


class DownloadOnlineTutorial(DownloadOnlineContent):

    current_content_type = 'TUTORIAL'


class DownloadOnlineOpinion(DownloadOnlineContent):

    current_content_type = "OPINION"


class DisplayOnlineContainer(SingleOnlineContentDetailViewMixin):
    """Base class that can show any content in any state"""

    template_name = 'tutorialv2/view/container_online.html'
    current_content_type = 'TUTORIAL'  # obviously, an article cannot have container !

    def get_context_data(self, **kwargs):
        context = super(DisplayOnlineContainer, self).get_context_data(**kwargs)
        container = search_container_or_404(self.versioned_object, self.kwargs)

        context['container'] = container
        context['pm_link'] = self.object.get_absolute_contact_url(_(u'À propos de'))

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
    template_name = 'tutorialv2/index_online.html'
    category = None
    tag = None
    current_content_type = None

    def get_queryset(self):
        """Filter the contents to obtain the list of given type.
        If category parameter is provided, only contents which have this category will be listed.

        :return: list of contents with the good type
        :rtype: list of zds.tutorialv2.models.models_database.PublishedContent
        """
        sub_query = 'SELECT COUNT(*) FROM {} WHERE {}={}'
        sub_query = sub_query.format(
            'tutorialv2_contentreaction',
            'tutorialv2_contentreaction.related_content_id',
            r'`tutorialv2_publishablecontent`.`id`'
        )
        queryset = PublishedContent.objects.filter(must_redirect=False)
        if self.current_content_type:
            queryset = queryset.filter(content_type=self.current_content_type)

        # prefetch:
        queryset = queryset\
            .prefetch_related('content')\
            .prefetch_related('content__subcategory')\
            .prefetch_related('content__authors')\
            .select_related('content__licence')\
            .select_related('content__image')\
            .select_related('content__last_note')\
            .select_related('content__last_note__related_content')\
            .select_related('content__last_note__related_content__public_version')\
            .filter(pk=F('content__public_version__pk'))

        if 'category' in self.request.GET:
            self.category = get_object_or_404(SubCategory, slug=self.request.GET.get('category'))
            queryset = queryset.filter(content__subcategory__in=[self.category])
        if 'tag' in self.request.GET:
            self.tag = get_object_or_404(Tag, title=self.request.GET.get('tag').lower().strip())
            queryset = queryset.filter(content__tags__in=[self.tag])  # different tags can have same
            # slug such as C/C#/C++, as a first version we get all of them
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
        context['tag'] = self.tag
        context['top_categories'] = top_categories_content(self.current_content_type)

        return context


class ListArticles(ListOnlineContents):
    """Displays the list of published articles"""

    current_content_type = 'ARTICLE'


class ListTutorials(ListOnlineContents):
    """Displays the list of published tutorials"""

    current_content_type = 'TUTORIAL'


class ListOpinions(ListOnlineContents):
    """Displays the list of published opinions"""

    current_content_type = "OPINION"


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
            .select_related('author')\
            .select_related('author__profile')\
            .select_related('editor')\
            .prefetch_related('alerts')\
            .prefetch_related('alerts__author')\
            .filter(related_content=self.object)\
            .order_by('-pubdate')[:settings.ZDS_APP['content']['notes_per_page']]

        return context

    def get(self, request, *args, **kwargs):

        # handle quoting case
        if 'cite' in self.request.GET:
            try:
                cited_pk = int(self.request.GET['cite'])
            except ValueError:
                raise Http404(u'L\'argument `cite` doit être un entier.')

            reaction = ContentReaction.objects.filter(pk=cited_pk).first()

            if reaction:
                if not reaction.is_visible:
                    raise PermissionDenied

                text = '\n'.join('> ' + line for line in reaction.text.split('\n'))
                text += '\nSource: [{}]({})'.format(reaction.author.username, reaction.get_absolute_url())

                if self.request.is_ajax():
                    return StreamingHttpResponse(json_writer.dumps({'text': text}, ensure_ascii=False))
                else:
                    self.quoted_reaction_text = text
        try:
            return super(SendNoteFormView, self).get(request, *args, **kwargs)
        except MustRedirect:  # if someone changed the pk arguments, and reached a 'must redirect' public
            # object
            raise Http404(u"Aucun contenu public trouvé avec l'identifiant " + str(self.request.GET.get('pk', 0)))

    def post(self, request, *args, **kwargs):

        if 'preview' in request.POST and request.is_ajax():  # preview
            content = render_to_response('misc/previsualization.part.html', {'text': request.POST['text']})
            return StreamingHttpResponse(content)
        else:
            return super(SendNoteFormView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        if self.check_as and self.object.antispam(self.request.user):
            raise PermissionDenied

        if 'preview' in self.request.POST:  # previewing
            return self.form_invalid(form)

        is_new = False

        if self.reaction:  # it's an edition
            self.reaction.update = datetime.now()
            self.reaction.editor = self.request.user

        else:
            self.reaction = ContentReaction()
            self.reaction.pubdate = datetime.now()
            self.reaction.author = self.request.user
            self.reaction.position = self.object.get_note_count() + 1
            self.reaction.related_content = self.object

            is_new = True

        # also treat alerts if editor is a moderator
        if self.request.user != self.reaction.author and not is_new:
            alerts = Alert.objects.filter(comment__pk=self.reaction.pk, solved=False)
            for alert in alerts:
                alert.solve(self.reaction, self.request.user, _(u'Résolu par édition.'))

        self.reaction.update_content(form.cleaned_data['text'])
        self.reaction.ip_address = get_client_ip(self.request)
        self.reaction.save()

        if is_new:  # we first need to save the reaction
            self.object.last_note = self.reaction
            self.object.save(update_date=False)

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
                .prefetch_related('author')\
                .filter(pk=int(self.request.GET['message']))\
                .first()
            if not self.reaction:
                raise Http404(u'Aucun commentaire : ' + self.request.GET['message'])
            if self.reaction.author.pk != self.request.user.pk and not self.is_staff:
                raise PermissionDenied()

            kwargs['reaction'] = self.reaction
        else:
            raise Http404(u"Le paramètre 'message' doit être un digit.")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UpdateNoteView, self).get_context_data(**kwargs)

        if self.reaction and self.reaction.author != self.request.user:
            messages.add_message(
                self.request, messages.WARNING,
                _(u'Vous éditez ce message en tant que modérateur (auteur : {}).'
                  u' Ne faites pas de bêtise !')
                .format(self.reaction.author.username))

            # show alert, if any
            alerts = Alert.objects.filter(comment__pk=self.reaction.pk, solved=False)
            if alerts.count():
                msg_alert = _(u'Attention, en éditant ce message, vous résolvez également les alertes suivantes : {}')\
                    .format(', '.join([u'« {} » (signalé par {})'.format(a.text, a.author.username) for a in alerts]))
                messages.warning(self.request, msg_alert)

        return context

    def form_valid(self, form):
        if 'message' in self.request.GET and self.request.GET['message'].isdigit():
            self.reaction = ContentReaction.objects\
                .filter(pk=int(self.request.GET['message']))\
                .prefetch_related('author')\
                .first()
            if self.reaction is None:
                raise Http404(u"Il n'y a aucun commentaire.")
            if self.reaction.author != self.request.user:
                if not self.request.user.has_perm('tutorialv2.change_contentreaction'):
                    raise PermissionDenied
        else:
            messages.error(self.request, _(u'Oh non ! Une erreur est survenue dans la requête !'))
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
                text = self.request.POST['text_hidden'][:80]  # Todo: Make it less static
            reaction = get_object_or_404(ContentReaction, pk=pk)
            if not self.request.user.has_perm('tutorialv2.change_contentreaction') and \
                    not self.request.user.pk == reaction.author.pk:
                raise PermissionDenied
            reaction.hide_comment_by_user(self.request.user, text)
            return redirect(reaction.get_absolute_url())
        except (IndexError, ValueError, MultiValueDictKeyError):
            raise Http404(u'Vous ne pouvez pas cacher cette réaction.')


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
            raise Http404(u'Aucune réaction trouvée.')


class SendNoteAlert(FormView, LoginRequiredMixin):
    http_method_names = ['post']

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(SendNoteAlert, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            note_pk = int(self.kwargs['pk'])
        except (KeyError, ValueError):
            raise Http404(u"Impossible de convertir l'identifiant en entier.")
        note = get_object_or_404(ContentReaction, pk=note_pk)
        alert = Alert()
        alert.author = request.user
        alert.comment = note
        alert.scope = Alert.SCOPE_CHOICES_DICT[note.related_content.type]
        alert.text = request.POST['signal_text']
        alert.pubdate = datetime.now()
        alert.save()

        messages.success(self.request, _(u'Ce commentaire a bien été signalé aux modérateurs.'))
        return redirect(note.get_absolute_url())


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
            raise Http404(u"L'alerte n'existe pas.")

        resolve_reason = ''
        msg_title = ''
        msg_content = ''
        if 'text' in request.POST and request.POST['text']:
            resolve_reason = request.POST['text']
            msg_title = _(u"Résolution d'alerte : {0}").format(note.related_content.title)
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
        alert.solve(note, request.user, resolve_reason, msg_title, msg_content)

        messages.success(self.request, _(u"L'alerte a bien été résolue."))
        return redirect(note.get_absolute_url())


class FollowContentReaction(LoggedWithReadWriteHability, SingleOnlineContentViewMixin, FormView):

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
            return HttpResponse(json_writer.dumps(response), content_type='application/json')
        return redirect(self.get_object().get_absolute_url())


class FollowNewContent(LoggedWithReadWriteHability, FormView):

    @staticmethod
    def perform_follow(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user).is_active

    @staticmethod
    def perform_follow_by_email(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user, True).is_active

    @method_decorator(transaction.atomic)
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

        if 'follow' in request.POST:
            response['follow'] = self.perform_follow(user_to_follow, request.user)
            response['subscriberCount'] = NewPublicationSubscription.objects.get_subscriptions(user_to_follow).count()
        elif 'email' in request.POST:
            response['email'] = self.perform_follow_by_email(user_to_follow, request.user)

        if request.is_ajax():
            return HttpResponse(json_writer.dumps(response), content_type='application/json')
        return redirect(request.META.get('HTTP_REFERER'))


class TagsListView(ListView):

    model = Tag
    template_name = 'tutorialv2/view/tags.html'
    context_object_name = 'tags'
    displayed_types = ['TUTORIAL', 'ARTICLE']

    def get_queryset(self):
        return PublishedContent.objects.get_top_tags(self.displayed_types)
