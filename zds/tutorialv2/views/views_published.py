# coding: utf-8
from collections import OrderedDict
from datetime import datetime
import json as json_writer
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import RedirectView, ListView, FormView
import os
from zds.member.decorator import LoggedWithReadWriteHability, LoginRequiredMixin
from zds.member.views import get_client_ip
from zds.tutorialv2.forms import RevokeValidationForm, WarnTypoForm, NoteForm
from zds.tutorialv2.mixins import SingleOnlineContentDetailViewMixin, SingleOnlineContentViewMixin, DownloadViewMixin, \
    ContentTypeMixin, SingleOnlineContentFormViewMixin
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent, ContentReaction, ContentRead
from zds.tutorialv2.utils import search_container_or_404
from zds.utils.models import CommentDislike, CommentLike, CategorySubCategory, SubCategory
from zds.utils.paginator import make_pagination


class RedirectContentSEO(RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        """Redirects the user to the new url"""
        obj = PublishableContent.objects.get(old_pk=kwargs["pk"])
        if obj is None or not obj.in_public():
            raise Http404

        obj = search_container_or_404(obj.load_version(public=True), kwargs)

        return obj.get_prod_path()


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
            .select_related('author').select_related('editor')\
            .prefetch_related('author__post_liked')\
            .prefetch_related('author__post_disliked')\
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
        user_votes = CommentDislike.objects\
            .select_related('note')\
            .filter(user__pk=self.request.user.pk, comments__pk__in=reaction_ids)\
            .all()
        context["user_dislike_dict"] = {reaction.pk: "dislike" for reaction in user_votes}
        user_votes = CommentLike.objects\
            .select_related('note')\
            .filter(user__pk=self.request.user.pk, comments__pk__in=reaction_ids)\
            .all()
        context["user_like_dict"] = {reaction.pk: "like" for reaction in user_votes}
        if self.request.user.has_perm('forum.change_post'):
            context["user_can_modify"] = reaction_ids
        else:
            context["user_can_modify"] = ContentReaction.objects\
                                                        .filter(author__pk=self.request.user.pk,
                                                                related_content__pk=self.object.pk)\
                                                        .values('pk')
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
    allowed_types = ['md', 'html', 'pdf', 'epub']

    mimetypes = {'html': 'text/html', 'md': 'text/plain', 'pdf': 'application/pdf', 'epub': 'application/epub+zip'}

    def get(self, context, **response_kwargs):

        # fill the variables
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()

        # check that type is ok
        if self.requested_file not in self.allowed_types:
            raise Http404

        # check existence
        if not self.public_content_object.have_type(self.requested_file):
            raise Http404

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
            raise Http404

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


class ListOnlineContents(ContentTypeMixin, ListView):
    """Displays the list of published contents"""

    context_object_name = 'public_contents'
    paginate_by = settings.ZDS_APP['content']['content_per_page']
    template_name = 'tutorialv2/index_online.html'
    tag = None

    def top_categories(self):
        """Get all the categories and their related subcategories associated with existing contents.
        The result is sorted by alphabetic order."""

        # TODO: since this is gonna be reused, it should go in zds/utils/tutorialsv2.py (and in topbar.py)

        subcategories_contents = PublishedContent.objects\
            .filter(content_type=self.current_content_type)\
            .values('content__subcategory').all()

        categories_from_subcategories = CategorySubCategory.objects\
            .filter(is_main=True)\
            .filter(subcategory__in=subcategories_contents)\
            .order_by('category__position', 'subcategory__title')\
            .select_related('subcategory', 'category')\
            .values('category__title', 'subcategory__title', 'subcategory__slug')\
            .all()

        categories = OrderedDict()

        for csc in categories_from_subcategories:
            key = csc['category__title']

            if key in categories:
                categories[key].append((csc['subcategory__title'], csc['subcategory__slug']))
            else:
                categories[key] = [(csc['subcategory__title'], csc['subcategory__slug'])]

        return categories

    def get_queryset(self):
        """Filter the contents to obtain the list of given type.
        If tag parameter is provided, only contents which have this category will be listed.

        :return: list of contents with the good type
        :rtype: list of zds.tutorialv2.models.models_database.PublishedContent
        """

        query_set = PublishedContent.objects\
            .prefetch_related("content")\
            .prefetch_related("content__subcategory")\
            .prefetch_related("content__authors")\
            .filter(content_type=self.current_content_type)

        if 'tag' in self.request.GET:
            self.tag = get_object_or_404(SubCategory, slug=self.request.GET.get('tag'))
            query_set = query_set.filter(content__subcategory__in=[self.tag])

        return query_set.order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super(ListOnlineContents, self).get_context_data(**kwargs)

        context['tag'] = self.tag
        context['top_categories'] = self.top_categories()

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

    def get_public_object(self):
        """redefine this function in order to get the object from `pk` in request.GET"""
        pk = self.request.GET.get('pk', None)
        if pk is None:
            raise Http404
        obj = PublishedContent.objects\
            .filter(content_pk=int(pk))\
            .prefetch_related('content')\
            .first()

        if obj is None:
            raise Http404

        return obj

    def get_form_kwargs(self):
        kwargs = super(SendNoteFormView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['content'] = self.object

        return kwargs

    def form_valid(self, form):

        if self.check_as and self.object.antispam(self.request.user):
            raise PermissionDenied
        if "message" in self.request.GET:

            if not self.request.GET["message"].isdigit():
                raise Http404
            reaction = ContentReaction.objects\
                .filter(pk=int(self.request.GET["message"]), author=self.request.user)
            if reaction is None:
                raise Http404
        elif self.reaction is None:
            self.reaction = ContentReaction()
        self.reaction.related_content = self.object
        self.reaction.update_content(form.cleaned_data["text"])
        self.reaction.pubdate = datetime.now()
        self.reaction.position = self.object.get_note_count() + 1
        self.reaction.ip_address = get_client_ip(self.request)
        self.reaction.author = self.request.user

        self.reaction.save()
        self.object.last_note = self.reaction
        self.object.save()
        read_note = ContentRead.objects\
            .filter(user__pk=self.request.user.pk, content__pk=self.object.pk)\
            .first()
        if read_note is None:
            read_note = ContentRead()
        read_note.content = self.object
        read_note.user = self.request.user
        read_note.note = self.reaction
        read_note.save()
        self.success_url = self.reaction.get_absolute_url()
        return super(SendNoteFormView, self).form_valid(form)


class UpdateNoteView(SendNoteFormView):
    check_as = False

    def form_valid(self, form):
        if "note_pk" in self.request.POST and self.request.POST["note_pk"].isdigit():
            self.reaction = ContentReaction.objects\
                .filter(pk=int(self.request.POST["note_pk"]), user__pk=self.request.user)\
                .first()
            if self.reaction is None:
                raise Http404
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
            raise Http404
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
        if request.is_ajax():
            return HttpResponse(json_writer.dumps(resp))
        else:
            return redirect(note.get_absolute_url())


class DownvoteReaction(UpvoteReaction):
    add_class = CommentDislike
    remove_class = CommentLike
    add_like = 0
    add_dislike = 1
