# coding: utf-8
from datetime import datetime
import json as json_writer
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponsePermanentRedirect, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template.loader import render_to_string
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, FormView
from django.views.generic.detail import BaseDetailView
import os
from zds.member.decorator import LoggedWithReadWriteHability, LoginRequiredMixin, PermissionRequiredMixin
from zds.member.views import get_client_ip
from zds.tutorialv2.forms import RevokeValidationForm, WarnTypoForm, NoteForm, NoteEditForm
from zds.tutorialv2.mixins import SingleOnlineContentDetailViewMixin, SingleOnlineContentViewMixin, DownloadViewMixin, \
    ContentTypeMixin, SingleOnlineContentFormViewMixin, MustRedirect
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent, ContentReaction
from zds.tutorialv2.utils import search_container_or_404, mark_read
from zds.utils.models import CommentDislike, CommentLike, SubCategory, Alert
from zds.utils.mps import send_mp
from zds.utils.paginator import make_pagination, ZdSPagingListView
from zds.utils.templatetags.topbar import top_categories_content


class RedirectContentSEO(RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        """Redirects the user to the new url"""
        obj = PublishableContent.objects.get(old_pk=kwargs["pk"])
        if obj is None or not obj.in_public():
            raise Http404("No public object has this pk.")
        kwargs["parent_container_slug"] = str(kwargs["p2"]) + "_" + kwargs["parent_container_slug"]
        kwargs["container_slug"] = str(kwargs["p3"]) + "_" + kwargs["container_slug"]
        obj = search_container_or_404(obj.load_version(public=True), kwargs)

        return obj.get_absolute_url_online()


class DisplayOnlineContent(SingleOnlineContentDetailViewMixin):
    """Base class that can show any online content"""

    model = PublishedContent
    template_name = 'tutorialv2/view/content_online.html'

    current_content_type = ""
    verbose_type_name = _(u'contenu')
    verbose_type_name_plural = _(u'contenus')

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super(DisplayOnlineContent, self).get_context_data(**kwargs)

        # TODO: deal with messaging and stuff like this !!

        if context['is_staff']:
            context['formRevokeValidation'] = RevokeValidationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})

        context['formWarnTypo'] = WarnTypoForm(self.versioned_object, self.versioned_object)

        queryset_reactions = ContentReaction.objects\
            .select_related('author')\
            .select_related('author__profile')\
            .select_related('editor')\
            .prefetch_related('author__post_liked')\
            .prefetch_related('author__post_disliked')\
            .prefetch_related('alerts')\
            .prefetch_related('alerts__author')\
            .filter(related_content=self.object)\
            .order_by("pubdate")

        # pagination:
        make_pagination(context,
                        self.request,
                        queryset_reactions,
                        settings.ZDS_APP['content']['notes_per_page'],
                        context_list_name='reactions',
                        with_previous_item=True)

        # is JS activated ?
        context["is_js"] = True
        if not self.object.js_support:
            context["is_js"] = False

        # optimize requests:
        reaction_ids = [reaction.pk for reaction in queryset_reactions]
        context["user_dislike"] = CommentDislike.objects\
            .select_related('note')\
            .filter(user__pk=self.request.user.pk, comments__pk__in=reaction_ids)\
            .values_list('pk', flat=True)
        context["user_like"] = CommentLike.objects\
            .select_related('note')\
            .filter(user__pk=self.request.user.pk, comments__pk__in=reaction_ids)\
            .values_list('pk', flat=True)

        if self.request.user.has_perm('forum.change_post'):
            context["user_can_modify"] = reaction_ids
        else:
            queryset_reactions_user = ContentReaction.objects\
                .filter(author__pk=self.request.user.pk, related_content__pk=self.object.pk)\
                .values_list('id', flat=True)
            context["user_can_modify"] = queryset_reactions_user

        context['isantispam'] = self.object.antispam()

        return context


class DisplayOnlineArticle(DisplayOnlineContent):
    """Displays the list of published articles"""

    current_content_type = "ARTICLE"
    verbose_type_name = _(u'article')
    verbose_type_name_plural = _(u'articles')


class DisplayOnlineTutorial(DisplayOnlineContent):
    """Displays the list of published tutorials"""

    current_content_type = "TUTORIAL"
    verbose_type_name = _(u'tutoriel')
    verbose_type_name_plural = _(u'tutoriels')


class DownloadOnlineContent(SingleOnlineContentViewMixin, DownloadViewMixin):
    """ Views that allow users to download "extra contents" of the public version
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
            raise Http404("The type of the file is not allowed.")

        # check existence
        if not self.public_content_object.have_type(self.requested_file):
            raise Http404("The type does not exist.")

        if self.requested_file == 'md' and not self.is_author and not self.is_staff:
            # download markdown is only for staff and author
            raise Http404("Only staff and author can download Markdown.")

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
            raise Http404("The file does not exist.")

        return response


class DownloadOnlineArticle(DownloadOnlineContent):

    current_content_type = "ARTICLE"


class DownloadOnlineTutorial(DownloadOnlineContent):

    current_content_type = "TUTORIAL"


class DisplayOnlineContainer(SingleOnlineContentDetailViewMixin):
    """Base class that can show any content in any state"""

    template_name = 'tutorialv2/view/container_online.html'
    current_content_type = "TUTORIAL"  # obviously, an article cannot have container !

    def get_context_data(self, **kwargs):
        context = super(DisplayOnlineContainer, self).get_context_data(**kwargs)
        container = search_container_or_404(self.versioned_object, self.kwargs)

        context['container'] = container

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
                if position > 0:
                    context['previous'] = chapters[position - 1]
                if position < len(chapters) - 1:
                    context['next'] = chapters[position + 1]

        return context


class ListOnlineContents(ContentTypeMixin, ZdSPagingListView):
    """Displays the list of published contents"""

    context_object_name = 'public_contents'
    paginate_by = settings.ZDS_APP['content']['content_per_page']
    template_name = 'tutorialv2/index_online.html'
    tag = None

    def get_queryset(self):
        """Filter the contents to obtain the list of given type.
        If tag parameter is provided, only contents which have this category will be listed.

        :return: list of contents with the good type
        :rtype: list of zds.tutorialv2.models.models_database.PublishedContent
        """
        sub_query = "SELECT COUNT(*) FROM {} WHERE {}={}"
        sub_query = sub_query.format(
            "tutorialv2_contentreaction",
            "tutorialv2_contentreaction.related_content_id",
            r"`tutorialv2_publishablecontent`.`id`"
        )
        queryset = PublishedContent.objects.filter(content_type=self.current_content_type, must_redirect=False)

        # prefetch:
        queryset = queryset\
            .prefetch_related("content")\
            .prefetch_related("content__subcategory")\
            .prefetch_related("content__authors")\
            .select_related('content__licence')\
            .select_related('content__image')\
            .select_related('content__last_note')\
            .select_related('content__last_note__related_content')\
            .select_related('content__last_note__related_content__public_version')

        if 'tag' in self.request.GET:
            self.tag = get_object_or_404(SubCategory, slug=self.request.GET.get('tag'))
            queryset = queryset.filter(content__subcategory__in=[self.tag])
        queryset = queryset.extra(select={"count_note": sub_query})
        return queryset.order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super(ListOnlineContents, self).get_context_data(**kwargs)
        for public_content in context["public_contents"]:
            if public_content.content.last_note is not None:
                public_content.content.last_note.related_content = public_content.content
                public_content.content.public_version = public_content
        context['tag'] = self.tag
        context['top_categories'] = top_categories_content(self.current_content_type)

        return context


class ListArticles(ListOnlineContents):
    """Displays the list of published articles"""

    current_content_type = "ARTICLE"


class ListTutorials(ListOnlineContents):
    """Displays the list of published tutorials"""

    current_content_type = "TUTORIAL"


class SendNoteFormView(LoggedWithReadWriteHability, SingleOnlineContentFormViewMixin):

    denied_if_lock = True
    form_class = NoteForm
    check_as = True
    reaction = None
    template_name = "tutorialv2/comment/new.html"

    def get_form_kwargs(self):
        kwargs = super(SendNoteFormView, self).get_form_kwargs()
        kwargs['content'] = self.object
        kwargs['reaction'] = None
        return kwargs

    def post(self, request, *args, **kwargs):

        if 'preview' in request.POST and request.is_ajax():  # preview
            content = render_to_response('misc/previsualization.part.html', {'text': request.POST['text']})
            return StreamingHttpResponse(content)
        else:
            return super(SendNoteFormView, self).post(request, *args, **kwargs)

    def form_valid(self, form):

        if self.check_as and self.object.antispam(self.request.user):
            raise PermissionDenied

        is_new = False

        if self.reaction:  # it's an edition
            self.reaction.update = datetime.now()

            if self.reaction.author != self.request.user:  # made by an admin
                self.reaction.editor = self.request.user

        else:
            self.reaction = ContentReaction()
            self.reaction.pubdate = datetime.now()
            self.reaction.author = self.request.user
            self.reaction.position = self.object.get_note_count() + 1
            self.reaction.related_content = self.object

            is_new = True

        self.reaction.update_content(form.cleaned_data["text"])
        self.reaction.ip_address = get_client_ip(self.request)
        self.reaction.save()

        if is_new:  # we first need to save the reaction
            self.object.last_note = self.reaction
            self.object.save()
            mark_read(self.object)

        self.success_url = self.reaction.get_absolute_url()
        return super(SendNoteFormView, self).form_valid(form)


class UpdateNoteView(SendNoteFormView):
    check_as = False
    template_name = "tutorialv2/comment/edit.html"
    form_class = NoteEditForm

    def get_form_kwargs(self):
        kwargs = super(UpdateNoteView, self).get_form_kwargs()
        if "message" in self.request.GET and self.request.GET["message"].isdigit():
            self.reaction = ContentReaction.objects\
                .prefetch_related("author")\
                .filter(pk=int(self.request.GET["message"]))\
                .first()
            kwargs['reaction'] = self.reaction
        else:
            raise Http404("The 'message' parameter must be a digit.")

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(UpdateNoteView, self).get_context_data(**kwargs)

        if self.reaction and self.reaction.author != self.request.user:
            messages.add_message(
                self.request, messages.WARNING,
                u'Vous éditez ce message en tant que modérateur (auteur : {}).'
                u' Ne faites pas de bêtise !'
                .format(self.reaction.author.username))

        return context

    def form_valid(self, form):
        if "message" in self.request.GET and self.request.GET["message"].isdigit():
            self.reaction = ContentReaction.objects\
                .prefetch_related("author")\
                .filter(pk=int(self.request.GET["message"]))\
                .first()
            if self.reaction is None:
                raise Http404("There is no reaction.")
            if self.reaction.author != self.request.user:
                if not self.request.user.has_perm('forum.change_post'):
                    raise PermissionDenied
        else:
            messages.error(self.request, 'Oh non ! Une erreur est survenue dans la requête !')
            return self.form_invalid(form)

        return super(UpdateNoteView, self).form_valid(form)


class UpvoteReaction(LoginRequiredMixin, FormView):

    add_class = CommentLike
    """
    :var add_class: The model class where the vote will be added
    """

    remove_class = CommentDislike
    """
    :var remove_class: The model class where the vote will be removed if exists
    """

    add_like = 1
    """
    :var add_like: The value that will be added to like total
    """

    add_dislike = 0
    """
    :var add_dislike: The value that will be added to the dislike total
    """

    def post(self, request, *args, **kwargs):
        if "message" not in self.request.GET or not self.request.GET["message"].isdigit():
            raise Http404("The 'message' parameter must be a digit.")
        note_pk = int(self.request.GET["message"])
        note = get_object_or_404(ContentReaction, pk=note_pk)
        resp = {}
        user = self.request.user
        if note.author.pk != user.pk:

            # Making sure the user is allowed to do that

            if self.add_class.objects.filter(user__pk=user.pk,
                                             comments__pk=note_pk).count() == 0:
                like = self.add_class()
                like.user = user
                like.comments = note
                note.like += self.add_like
                note.dislike += self.add_dislike
                note.save()
                like.save()
                if self.remove_class.objects.filter(user__pk=user.pk,
                                                    comments__pk=note_pk).count() > 0:
                    self.remove_class.objects.filter(
                        user__pk=user.pk,
                        comments__pk=note_pk).all().delete()
                    note.dislike = note.dislike - self.add_like
                    note.like = note.like - self.add_dislike
                    note.save()
            else:
                self.add_class.objects.filter(user__pk=user.pk,
                                              comments__pk=note_pk).all().delete()
                note.like = note.like - self.add_like
                note.dislike = note.dislike - self.add_dislike
                note.save()
        resp["upvotes"] = note.like
        resp["downvotes"] = note.dislike
        if self.request.is_ajax():
            return StreamingHttpResponse(json_writer.dumps(resp))
        return redirect(note.get_absolute_url())


class DownvoteReaction(UpvoteReaction):
    add_class = CommentDislike
    remove_class = CommentLike
    add_like = 0
    add_dislike = 1


class GetReaction(BaseDetailView):
    model = ContentReaction

    def get_queryset(self):
        return ContentReaction.objects.filter(pk=int(self.kwargs["pk"]))

    def render_to_response(self, context):

        reaction = self.get_queryset().first()
        if reaction is not None:
            text = '\n'.join('> ' + line for line in reaction.text.split('\n'))
            text += "\nSource: " + reaction.author.username
            string = json_writer.dumps({"text": text}, ensure_ascii=False)
        else:
            string = u'{"text":""}'
        return StreamingHttpResponse(string)


class HideReaction(FormView, LoginRequiredMixin):
    http_method_names = ["post"]

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(HideReaction, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):

        try:
            pk = int(self.kwargs["pk"])
            text = ''
            if 'text_hidden' in self.request.POST:
                text = self.request.POST["text_hidden"][:80]  # Todo: Make it less static
            reaction = get_object_or_404(ContentReaction, pk=pk)
            if not self.request.user.has_perm('forum.change_post') and not self.request.user.pk == reaction.author.pk:
                raise PermissionDenied
            reaction.hide_comment_by_user(self.request.user, text)
            return redirect(reaction.get_absolute_url())
        except (IndexError, ValueError, MultiValueDictKeyError):
            raise Http404("You cannot hide this.")


class ShowReaction(FormView, LoggedWithReadWriteHability, PermissionRequiredMixin):

    permissions = ["tutorial.change_post"]
    http_method_names = ['post']

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(ShowReaction, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            pk = int(self.kwargs["pk"])
            reaction = get_object_or_404(ContentReaction, pk=pk)
            reaction.is_visible = True
            reaction.save()

            return redirect(reaction.get_absolute_url())

        except (IndexError, ValueError, MultiValueDictKeyError):
            raise Http404("No such thing to show.")


class SendNoteAlert(FormView, LoginRequiredMixin):
    http_method_names = ["post"]

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(SendNoteAlert, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            note_pk = int(self.kwargs["pk"])
        except (KeyError, ValueError):
            raise Http404("Cannot convert the pk into int.")
        note = get_object_or_404(ContentReaction, pk=note_pk)
        alert = Alert()
        alert.author = request.user
        alert.comment = note
        alert.scope = Alert.CONTENT
        alert.text = request.POST["signal_text"]
        alert.pubdate = datetime.now()
        alert.save()

        return redirect(note.get_absolute_url())


class SolveNoteAlert(FormView, LoginRequiredMixin):

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(SolveNoteAlert, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.has_perm("tutorialv2.change_contentreaction"):
            raise PermissionDenied
        try:
            alert = get_object_or_404(Alert, pk=int(request.POST["alert_pk"]))
            note = ContentReaction.objects.get(pk=alert.comment.id)
            content = note.related_content
            if "text" in request.POST and request.POST["text"] != "":
                bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                msg = render_to_string(
                    'tutorialv2/messages/resolve_alert.md',
                    {
                        'content': content,
                        'url': content.get_absolute_url_online(),
                        'name': alert.author.username,
                        'target_name': note.author.username,
                        'modo_name': self.request.user.username,
                        'message': '\n'.join(['> ' + line for line in self.request.POST["text"].split('\n')]),
                        'alert_text': '\n'.join(['> ' + line for line in alert.text.split('\n')])
                    })
                send_mp(
                    bot,
                    [alert.author],
                    _(u"Résolution d'alerte"),
                    note.related_content.title,
                    msg,
                    False,
                )
            alert.delete()
            messages.success(self.request, _(u"L'alerte a bien été résolue."))
            return redirect(note.get_absolute_url())
        except (KeyError, ValueError):
            raise Http404("The alert does not exist.")
