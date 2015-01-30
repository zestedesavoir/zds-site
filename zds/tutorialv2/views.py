#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import datetime
from operator import attrgetter
from urllib import urlretrieve
from django.contrib.humanize.templatetags.humanize import naturaltime
from urlparse import urlparse, parse_qs
try:
    import ujson as json_reader
except ImportError:
    try:
        import simplejson as json_reader
    except ImportError:
        import json as json_reader
import json
import json as json_writer
import shutil
import re
import zipfile
import os
import glob
import tempfile

from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q, Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import smart_str
from django.views.decorators.http import require_POST
from git import Repo, Actor
from lxml import etree

from forms import ContentForm, PartForm, ChapterForm, EmbdedChapterForm, \
    ExtractForm, ImportForm, ImportArchiveForm, NoteForm, AskValidationForm, ValidForm, RejectForm, ActivJsForm
from models import PublishableContent, Container, Extract, Validation, ContentReaction, init_new_repo
from utils import never_read, mark_read
from zds.gallery.models import Gallery, UserGallery, Image
from zds.member.decorator import can_write_and_read_now
from zds.member.models import get_info_old_tuto, Profile
from zds.member.views import get_client_ip
from zds.forum.models import Forum, Topic
from zds.utils import slugify
from zds.utils.models import Alert
from zds.utils.models import Category, Licence, CommentLike, CommentDislike, \
    SubCategory, HelpWriting
from zds.utils.mps import send_mp
from zds.utils.forums import create_topic, send_post, lock_topic, unlock_topic
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move, get_sep, get_text_is_empty, import_archive
from zds.utils.misc import compute_hash, content_has_changed
from django.utils.translation import ugettext as _
from django.views.generic import ListView, DetailView, FormView, DeleteView
# until we completely get rid of these, import them :
from zds.tutorial.models import Tutorial, Chapter, Part
from zds.tutorial.forms import TutorialForm


class ListContent(ListView):
    """
    Displays the list of offline contents (written by user)
    """
    context_object_name = 'contents'
    template_name = 'tutorialv2/index.html'

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        """rewrite this method to ensure decoration"""
        return super(ListContent, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """
        Filter the content to obtain the list of content written by current user
        :return: list of articles
        """
        query_set = PublishableContent.objects.all().filter(authors__in=[self.request.user])
        return query_set

    def get_context_data(self, **kwargs):
        """Separate articles and tutorials"""
        context = super(ListContent, self).get_context_data(**kwargs)
        context['articles'] = []
        context['tutorials'] = []
        for content in self.get_queryset():
            versioned = content.load_version()
            if content.type == 'ARTICLE':
                context['articles'].append(versioned)
            else:
                context['tutorials'].append(versioned)
        return context


class CreateContent(FormView):
    template_name = 'tutorialv2/create/content.html'
    model = PublishableContent
    form_class = ContentForm
    content = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(CreateContent, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        # create the object:
        self.content = PublishableContent()
        self.content.title = form.cleaned_data['title']
        self.content.description = form.cleaned_data["description"]
        self.content.type = form.cleaned_data["type"]
        self.content.licence = form.cleaned_data["licence"]

        self.content.creation_date = datetime.now()

        # Creating the gallery
        gal = Gallery()
        gal.title = form.cleaned_data["title"]
        gal.slug = slugify(form.cleaned_data["title"])
        gal.pubdate = datetime.now()
        gal.save()

        # Attach user to gallery
        userg = UserGallery()
        userg.gallery = gal
        userg.mode = "W"  # write mode
        userg.user = self.request.user
        userg.save()
        self.content.gallery = gal

        # create image:
        if "image" in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES["image"]
            img.gallery = gal
            img.title = self.request.FILES["image"]
            img.slug = slugify(self.request.FILES["image"])
            img.pubdate = datetime.now()
            img.save()
            self.content.image = img

        self.content.save()

        # We need to save the tutorial before changing its author list since it's a many-to-many relationship
        self.content.authors.add(self.request.user)

        # Add subcategories on tutorial
        for subcat in form.cleaned_data["subcategory"]:
            self.content.subcategory.add(subcat)

        # Add helps if needed
        for helpwriting in form.cleaned_data["helps"]:
            self.content.helps.add(helpwriting)

        self.content.save()

        # create a new repo :
        init_new_repo(self.content,
                      form.cleaned_data['introduction'],
                      form.cleaned_data['conclusion'],
                      form.cleaned_data['msg_commit'])

        return super(CreateContent, self).form_valid(form)

    def get_success_url(self):
        if self.content:
            return reverse('content:view', args=[self.content.pk, self.content.slug])
        else:
            return reverse('content:index')


class DisplayContent(DetailView):
    """Base class that can show any content in any state"""

    model = PublishableContent
    template_name = 'tutorialv2/view/content.html'
    online = False
    sha = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DisplayContent, self).dispatch(*args, **kwargs)

    def get_forms(self, context, content):
        """get all the auxiliary forms about validation, js fiddle..."""
        validation = Validation.objects.filter(content__pk=content.pk)\
            .order_by("-date_proposition")\
            .first()
        form_js = ActivJsForm(initial={"js_support": content.js_support})

        if content.source:
            form_ask_validation = AskValidationForm(initial={"source": content.source})
            form_valid = ValidForm(initial={"source": content.source})
        else:
            form_ask_validation = AskValidationForm()
            form_valid = ValidForm()
        form_reject = RejectForm()

        context["validation"] = validation
        context["formAskValidation"] = form_ask_validation
        context["formJs"] = form_js
        context["formValid"] = form_valid
        context["formReject"] = form_reject

    def get_object(self, queryset=None):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""

        context = super(DisplayContent, self).get_context_data(**kwargs)
        content = context['object']

        # Retrieve sha given by the user. This sha must to be exist. If it doesn't
        # exist, we take draft version of the content.
        try:
            sha = self.request.GET["version"]
        except KeyError:
            if self.sha is not None:
                sha = self.sha
            else:
                sha = content.sha_draft

        # check that if we ask for beta, we also ask for the sha version
        is_beta = content.is_beta(sha)

        if self.request.user not in content.authors.all() and not is_beta:
            # if we are not author of this content or if we did not ask for beta
            # the only members that can display and modify the tutorial are validators
            if not self.request.user.has_perm("tutorial.change_tutorial"):
                raise PermissionDenied

        # load versioned file
        versioned_tutorial = content.load_version(sha)

        # check whether this tuto support js fiddle
        if content.js_support:
            is_js = "js"
        else:
            is_js = ""
        context["is_js"] = is_js
        context["content"] = versioned_tutorial
        context["version"] = sha
        self.get_forms(context, content)

        return context


class EditContent(FormView):
    template_name = 'tutorialv2/edit/content.html'
    model = PublishableContent
    form_class = ContentForm
    content = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        """rewrite this method to ensure decoration"""
        return super(EditContent, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_initial(self):
        """rewrite function to pre-populate form"""
        context = self.get_context_data()
        versioned = context['content']
        initial = super(EditContent, self).get_initial()

        initial['title'] = versioned.title
        initial['description'] = versioned.description
        initial['type'] = versioned.type
        initial['introduction'] = versioned.get_introduction()
        initial['conclusion'] = versioned.get_conclusion()
        initial['licence'] = versioned.licence
        initial['subcategory'] = self.content.subcategory.all()
        initial['helps'] = self.content.helps.all()

        return initial

    def get_context_data(self, **kwargs):
        self.content = self.get_object()
        context = super(EditContent, self).get_context_data(**kwargs)
        context['content'] = self.content.load_version()

        return context

    def form_valid(self, form):
        # TODO: tutorial <-> article
        context = self.get_context_data()
        versioned = context['content']

        # first, update DB (in order to get a new slug if needed)
        self.content.title = form.cleaned_data['title']
        self.content.description = form.cleaned_data["description"]
        self.content.licence = form.cleaned_data["licence"]

        self.content.update_date = datetime.now()

        # update gallery and image:
        gal = Gallery.objects.filter(pk=self.content.gallery.pk)
        gal.update(title=self.content.title)
        gal.update(slug=slugify(self.content.title))
        gal.update(update=datetime.now())

        if "image" in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES["image"]
            img.gallery = self.content.gallery
            img.title = self.request.FILES["image"]
            img.slug = slugify(self.request.FILES["image"])
            img.pubdate = datetime.now()
            img.save()
            self.content.image = img

        self.content.save()

        # now, update the versioned information
        versioned.description = form.cleaned_data['description']
        versioned.licence = form.cleaned_data['licence']

        sha = versioned.repo_update_top_container(form.cleaned_data['title'],
                                                  self.content.slug,
                                                  form.cleaned_data['introduction'],
                                                  form.cleaned_data['conclusion'],
                                                  form.cleaned_data['msg_commit'])

        # update relationships :
        self.content.sha_draft = sha

        self.content.subcategory.clear()
        for subcat in form.cleaned_data["subcategory"]:
            self.content.subcategory.add(subcat)

        self.content.helps.clear()
        for help in form.cleaned_data["helps"]:
            self.content.helps.add(help)

        self.content.save()

        return super(EditContent, self).form_valid(form)

    def get_success_url(self):
        return reverse('content:view', args=[self.content.pk, self.content.slug])


class DeleteContent(DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = [u'delete', u'post']
    object = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        """rewrite this method to ensure decoration"""
        return super(DeleteContent, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def delete(self, request, *args, **kwargs):
        """rewrite delete() function to ensure repository deletion"""
        self.object = self.get_object()
        self.object.repo_delete()

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('content:index')


class ArticleList(ListView):
    """
    Displays the list of published articles.
    """
    context_object_name = 'articles'
    paginate_by = settings.ZDS_APP['tutorial']['content_per_page']
    type = "ARTICLE"
    template_name = 'article/index.html'
    tag = None

    def get_queryset(self):
        """
        Filter the content to obtain the list of only articles. If tag parameter is provided, only articles
        which have this category will be listed.
        :return: list of articles
        """
        if self.request.GET.get('tag') is not None:
            self.tag = get_object_or_404(SubCategory, title=self.request.GET.get('tag'))
        query_set = PublishableContent.objects.filter(type=self.type).filter(sha_public__isnull=False)\
            .exclude(sha_public='')
        if self.tag is not None:
            query_set = query_set.filter(subcategory__in=[self.tag])
        return query_set.order_by('-pubdate')

    def get_context_data(self, **kwargs):
        context = super(ArticleList, self).get_context_data(**kwargs)
        context['tag'] = self.tag
        # TODO in database, the information concern the draft, so we have to make stuff here !
        return context


class TutorialList(ArticleList):
    """Displays the list of published tutorials."""

    context_object_name = 'tutorials'
    type = "TUTORIAL"
    template_name = 'tutorialv2/index.html'


class TutorialWithHelp(TutorialList):
    """List all tutorial that needs help, i.e registered as needing at least one HelpWriting or is in beta
    for more documentation, have a look to ZEP 03 specification (fr)"""
    context_object_name = 'tutorials'
    template_name = 'tutorialv2/help.html'

    def get_queryset(self):
        """get only tutorial that need help and handle filtering if asked"""
        query_set = PublishableContent.objects\
            .annotate(total=Count('helps'), shasize=Count('sha_beta')) \
            .filter((Q(sha_beta__isnull=False) & Q(shasize__gt=0)) | Q(total__gt=0)) \
            .all()
        try:
            type_filter = self.request.GET.get('type')
            query_set = query_set.filter(helps_title__in=[type_filter])
        except KeyError:
            # if no filter, no need to change
            pass
        return query_set

    def get_context_data(self, **kwargs):
        """Add all HelpWriting objects registered to the context so that the template can use it"""
        context = super(TutorialWithHelp, self).get_context_data(**kwargs)
        context['helps'] = HelpWriting.objects.all()
        return context

# TODO ArticleWithHelp


class DisplayDiff(DetailView):
    """Display the difference between two version of a content.
    Reference is always HEAD and compared version is a GET query parameter named sha
    this class has no reason to be adapted to any content type"""
    model = PublishableContent
    template_name = "tutorial/diff.html"
    context_object_name = "tutorial"

    def get_object(self, queryset=None):
        return get_object_or_404(PublishableContent, pk=self.kwargs['content_pk'])

    def get_context_data(self, **kwargs):

        context = super(DisplayDiff, self).get_context_data(**kwargs)

        try:
            sha = self.request.GET.get("sha")
        except KeyError:
            sha = self.get_object().sha_draft

        if self.request.user not in context[self.context_object_name].authors.all():
            if not self.request.user.has_perm("tutorial.change_tutorial"):
                raise PermissionDenied
        # open git repo and find diff between displayed version and head
        repo = Repo(context[self.context_object_name].get_repo_path())
        current_version_commit = repo.commit(sha)
        diff_with_head = current_version_commit.diff("HEAD~1")
        context["path_add"] = diff_with_head.iter_change_type("A")
        context["path_ren"] = diff_with_head.iter_change_type("R")
        context["path_del"] = diff_with_head.iter_change_type("D")
        context["path_maj"] = diff_with_head.iter_change_type("M")
        return context


class DisplayOnlineContent(DisplayContent):
    """Display online tutorial"""
    type = "TUTORIAL"
    template_name = "tutorial/view_online.html"

    def get_forms(self, context, content):

        # Build form to send a note for the current tutorial.
        context['form'] = NoteForm(content, self.request.user)

    def compatibility_parts(self, content, repo, sha, dictionary, cpt_p):
        dictionary["tutorial"] = content
        dictionary["path"] = content.get_repo_path()
        dictionary["slug"] = slugify(dictionary["title"])
        dictionary["position_in_tutorial"] = cpt_p

        cpt_c = 1
        for chapter in dictionary["chapters"]:
            chapter["part"] = dictionary
            chapter["slug"] = slugify(chapter["title"])
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            self.compatibility_chapter(content, repo, sha, chapter)
            cpt_c += 1

    def compatibility_chapter(self, content, repo, sha, dictionary):
        """enable compatibility with old version of mini tutorial and chapter implementations"""
        dictionary["path"] = content.get_prod_path()
        dictionary["type"] = self.type
        dictionary["pk"] = Container.objects.get(parent=content).pk  # TODO : find better name
        dictionary["intro"] = open(os.path.join(content.get_prod_path(), "introduction.md" + ".html"), "r")
        dictionary["conclu"] = open(os.path.join(content.get_prod_path(), "conclusion.md" + ".html"), "r")
        # load extracts
        cpt = 1
        for ext in dictionary["extracts"]:
            ext["position_in_chapter"] = cpt
            ext["path"] = content.get_prod_path()
            text = open(os.path.join(content.get_prod_path(), ext["text"] + ".html"), "r")
            ext["txt"] = text.read()
            cpt += 1

    def get_context_data(self, **kwargs):
        content = self.get_object()
        # If the tutorial isn't online, we raise 404 error.
        if not content.in_public():
            raise Http404
        self.sha = content.sha_public
        context = super(DisplayOnlineContent, self).get_context_data(**kwargs)

        context["tutorial"]["update"] = content.update
        context["tutorial"]["get_note_count"] = content.get_note_count()

        if self.request.user.is_authenticated():
            # If the user is authenticated, he may want to tell the world how cool the content is
            # We check if he can post a not or not with
            # antispam filter.
            context['tutorial']['antispam'] = content.antispam()

            # If the user has never read this before, we mark this tutorial read.
            if never_read(content):
                mark_read(content)

        # Find all notes of the tutorial.

        notes = ContentReaction.objects.filter(related_content__pk=content.pk).order_by("position").all()

        # Retrieve pk of the last note. If there aren't notes for the tutorial, we
        # initialize this last note at 0.

        last_note_pk = 0
        if content.last_note:
            last_note_pk = content.last_note.pk

        # Handle pagination

        paginator = Paginator(notes, settings.ZDS_APP['forum']['posts_per_page'])
        try:
            page_nbr = int(self.request.GET.get("page"))
        except KeyError:
            page_nbr = 1
        except ValueError:
            raise Http404

        try:
            notes = paginator.page(page_nbr)
        except PageNotAnInteger:
            notes = paginator.page(1)
        except EmptyPage:
            raise Http404

        res = []
        if page_nbr != 1:

            # Show the last note of the previous page

            last_page = paginator.page(page_nbr - 1).object_list
            last_note = last_page[len(last_page) - 1]
            res.append(last_note)
        for note in notes:
            res.append(note)

        context['notes'] = res
        context['last_note_pk'] = last_note_pk
        context['pages'] = paginator_range(page_nbr, paginator.num_pages)
        context['nb'] = page_nbr


class DisplayOnlineArticle(DisplayOnlineContent):
    type = "ARTICLE"


def render_chapter_form(chapter):
    if chapter.part:
        return ChapterForm({"title": chapter.title,
                            "introduction": chapter.get_introduction(),
                            "conclusion": chapter.get_conclusion()})
    else:

        return \
            EmbdedChapterForm({"introduction": chapter.get_introduction(),
                               "conclusion": chapter.get_conclusion()})


# Staff actions.


@permission_required("tutorial.change_tutorial", raise_exception=True)
@login_required
def list_validation(request):
    """Display tutorials list in validation."""

    # Retrieve type of the validation. Default value is all validations.

    try:
        type = request.GET["type"]
    except KeyError:
        type = None

    # Get subcategory to filter validations.

    try:
        subcategory = get_object_or_404(Category, pk=request.GET["subcategory"])
    except (KeyError, Http404):
        subcategory = None

    # Orphan validation. There aren't validator attached to the validations.

    if type == "orphan":
        if subcategory is None:
            validations = Validation.objects.filter(
                validator__isnull=True,
                status="PENDING").order_by("date_proposition").all()
        else:
            validations = Validation.objects.filter(validator__isnull=True,
                                                    status="PENDING",
                                                    tutorial__subcategory__in=[subcategory]) \
                .order_by("date_proposition") \
                .all()
    elif type == "reserved":

        # Reserved validation. There are a validator attached to the
        # validations.

        if subcategory is None:
            validations = Validation.objects.filter(
                validator__isnull=False,
                status="PENDING_V").order_by("date_proposition").all()
        else:
            validations = Validation.objects.filter(validator__isnull=False,
                                                    status="PENDING_V",
                                                    tutorial__subcategory__in=[subcategory]) \
                .order_by("date_proposition") \
                .all()
    else:

        # Default, we display all validations.

        if subcategory is None:
            validations = Validation.objects.filter(
                Q(status="PENDING") | Q(status="PENDING_V")).order_by("date_proposition").all()
        else:
            validations = Validation.objects.filter(Q(status="PENDING")
                                                    | Q(status="PENDING_V"
                                                        )).filter(tutorial__subcategory__in=[subcategory]) \
                .order_by("date_proposition")\
                .all()
    return render(request, "tutorial/validation/index.html",
                           {"validations": validations})


@permission_required("tutorial.change_tutorial", raise_exception=True)
@login_required
@require_POST
def reservation(request, validation_pk):
    """Display tutorials list in validation."""

    validation = get_object_or_404(Validation, pk=validation_pk)
    if validation.validator:
        validation.validator = None
        validation.date_reserve = None
        validation.status = "PENDING"
        validation.save()
        messages.info(request, _(u"Le tutoriel n'est plus sous réserve."))
        return redirect(reverse("zds.tutorial.views.list_validation"))
    else:
        validation.validator = request.user
        validation.date_reserve = datetime.now()
        validation.status = "PENDING_V"
        validation.save()
        messages.info(request,
                      _(u"Le tutoriel a bien été \
                      réservé par {0}.").format(request.user.username))
        return redirect(
            validation.content.get_absolute_url() +
            "?version=" + validation.version
        )


@login_required
def history(request, tutorial_pk, tutorial_slug):
    """History of the tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    repo = Repo(tutorial.get_repo_path())
    logs = repo.head.reference.log()
    logs = sorted(logs, key=attrgetter("time"), reverse=True)
    return render(request, "tutorial/tutorial/history.html",
                           {"tutorial": tutorial, "logs": logs})


@login_required
@permission_required("tutorial.change_tutorial", raise_exception=True)
def history_validation(request, tutorial_pk):
    """History of the validation of a tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    # Get subcategory to filter validations.

    try:
        subcategory = get_object_or_404(Category, pk=request.GET["subcategory"])
    except (KeyError, Http404):
        subcategory = None
    if subcategory is None:
        validations = \
            Validation.objects.filter(tutorial__pk=tutorial_pk) \
            .order_by("date_proposition"
                      ).all()
    else:
        validations = Validation.objects.filter(tutorial__pk=tutorial_pk,
                                                tutorial__subcategory__in=[subcategory]) \
            .order_by("date_proposition"
                      ).all()
    return render(request, "tutorial/validation/history.html",
                           {"validations": validations, "tutorial": tutorial})


@can_write_and_read_now
@login_required
@require_POST
@permission_required("tutorial.change_tutorial", raise_exception=True)
def reject_tutorial(request):
    """Staff reject tutorial of an author."""

    # Retrieve current tutorial;

    try:
        tutorial_pk = request.POST["tutorial"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    validation = Validation.objects.filter(
        tutorial__pk=tutorial_pk,
        version=tutorial.sha_validation).latest("date_proposition")

    if request.user == validation.validator:
        validation.comment_validator = request.POST["text"]
        validation.status = "REJECT"
        validation.date_validation = datetime.now()
        validation.save()

        # Remove sha_validation because we rejected this version of the tutorial.

        tutorial.sha_validation = None
        tutorial.pubdate = None
        tutorial.save()
        messages.info(request, _(u"Le tutoriel a bien été refusé."))
        comment_reject = '\n'.join(['> '+line for line in validation.comment_validator.split('\n')])
        # send feedback
        msg = (
            _(u'Désolé, le zeste **{0}** n\'a malheureusement '
              u'pas passé l’étape de validation. Mais ne désespère pas, '
              u'certaines corrections peuvent surement être faite pour '
              u'l’améliorer et repasser la validation plus tard. '
              u'Voici le message que [{1}]({2}), ton validateur t\'a laissé:\n\n`{3}`\n\n'
              u'N\'hésite pas a lui envoyer un petit message pour discuter '
              u'de la décision ou demander plus de détail si tout cela te '
              u'semble injuste ou manque de clarté.')
            .format(tutorial.title,
                    validation.validator.username,
                    settings.ZDS_APP['site']['url'] + validation.validator.profile.get_absolute_url(),
                    comment_reject))
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            tutorial.authors.all(),
            _(u"Refus de Validation : {0}").format(tutorial.title),
            "",
            msg,
            True,
            direct=False,
        )
        return redirect(tutorial.get_absolute_url() + "?version="
                        + validation.version)
    else:
        messages.error(request,
                       _(u"Vous devez avoir réservé ce tutoriel "
                         u"pour pouvoir le refuser."))
        return redirect(tutorial.get_absolute_url() + "?version="
                        + validation.version)


@can_write_and_read_now
@login_required
@require_POST
@permission_required("tutorial.change_tutorial", raise_exception=True)
def valid_tutorial(request):
    """Staff valid tutorial of an author."""

    # Retrieve current tutorial;

    try:
        tutorial_pk = request.POST["tutorial"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    validation = Validation.objects.filter(
        tutorial__pk=tutorial_pk,
        version=tutorial.sha_validation).latest("date_proposition")

    if request.user == validation.validator:
        (output, err) = mep(tutorial, tutorial.sha_validation)
        messages.info(request, output)
        messages.error(request, err)
        validation.comment_validator = request.POST["text"]
        validation.status = "ACCEPT"
        validation.date_validation = datetime.now()
        validation.save()

        # Update sha_public with the sha of validation. We don't update sha_draft.
        # So, the user can continue to edit his tutorial in offline.

        if request.POST.get('is_major', False) or tutorial.sha_public is None or tutorial.sha_public == '':
            tutorial.pubdate = datetime.now()
        tutorial.sha_public = validation.version
        tutorial.source = request.POST["source"]
        tutorial.sha_validation = None
        tutorial.save()
        messages.success(request, _(u"Le tutoriel a bien été validé."))

        # send feedback

        msg = (
            _(u'Félicitations ! Le zeste [{0}]({1}) '
              u'a été publié par [{2}]({3}) ! Les lecteurs du monde entier '
              u'peuvent venir l\'éplucher et réagir a son sujet. '
              u'Je te conseille de rester a leur écoute afin '
              u'd\'apporter des corrections/compléments.'
              u'Un Tutoriel vivant et a jour est bien plus lu '
              u'qu\'un sujet abandonné !')
            .format(tutorial.title,
                    settings.ZDS_APP['site']['url'] + tutorial.get_absolute_url_online(),
                    validation.validator.username,
                    settings.ZDS_APP['site']['url'] + validation.validator.profile.get_absolute_url(),))
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            tutorial.authors.all(),
            _(u"Publication : {0}").format(tutorial.title),
            "",
            msg,
            True,
            direct=False,
        )
        return redirect(tutorial.get_absolute_url() + "?version="
                        + validation.version)
    else:
        messages.error(request,
                       _(u"Vous devez avoir réservé ce tutoriel "
                         u"pour pouvoir le valider."))
        return redirect(tutorial.get_absolute_url() + "?version="
                        + validation.version)


@can_write_and_read_now
@login_required
@permission_required("tutorial.change_tutorial", raise_exception=True)
@require_POST
def invalid_tutorial(request, tutorial_pk):
    """Staff invalid tutorial of an author."""

    # Retrieve current tutorial

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    un_mep(tutorial)
    validation = Validation.objects.filter(
        tutorial__pk=tutorial_pk,
        version=tutorial.sha_public).latest("date_proposition")
    validation.status = "PENDING"
    validation.date_validation = None
    validation.save()

    # Only update sha_validation because contributors can contribute on
    # rereading version.

    tutorial.sha_public = None
    tutorial.sha_validation = validation.version
    tutorial.pubdate = None
    tutorial.save()
    messages.success(request, _(u"Le tutoriel a bien été dépublié."))
    return redirect(tutorial.get_absolute_url() + "?version="
                    + validation.version)


# User actions on tutorial.

@can_write_and_read_now
@login_required
@require_POST
def ask_validation(request):
    """User ask validation for his tutorial."""

    # Retrieve current tutorial;

    try:
        tutorial_pk = request.POST["tutorial"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff, he
    # hasn't permission to execute this method:

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    old_validation = Validation.objects.filter(tutorial__pk=tutorial_pk,
                                               status__in=['PENDING_V']).first()
    if old_validation is not None:
        old_validator = old_validation.validator
    else:
        old_validator = None
    # delete old pending validation
    Validation.objects.filter(tutorial__pk=tutorial_pk,
                              status__in=['PENDING', 'PENDING_V'])\
        .delete()
    # We create and save validation object of the tutorial.

    validation = Validation()
    validation.content = tutorial
    validation.date_proposition = datetime.now()
    validation.comment_authors = request.POST["text"]
    validation.version = request.POST["version"]
    if old_validator is not None:
        validation.validator = old_validator
        validation.date_reserve
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        msg = \
            (_(u'Bonjour {0},'
               u'Le tutoriel *{1}* que tu as réservé a été mis à jour en zone de validation, '
               u'Pour retrouver les modifications qui ont été faites, je t\'invite à '
               u'consulter l\'historique des versions'
               u'\n\n> Merci').format(old_validator.username, tutorial.title))
        send_mp(
            bot,
            [old_validator],
            _(u"Mise à jour de tuto : {0}").format(tutorial.title),
            _(u"En validation"),
            msg,
            False,
        )
    validation.save()
    validation.content.source = request.POST["source"]
    validation.content.sha_validation = request.POST["version"]
    validation.content.save()
    messages.success(request,
                     _(u"Votre demande de validation a été envoyée à l'équipe."))
    return redirect(tutorial.get_absolute_url())


@can_write_and_read_now
@login_required
@require_POST
def delete_tutorial(request, tutorial_pk):
    """User would like delete his tutorial."""

    # Retrieve current tutorial

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff, he
    # hasn't permission to execute this method:

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    # when author is alone we can delete definitively tutorial

    if tutorial.authors.count() == 1:

        # user can access to gallery

        try:
            ug = UserGallery.objects.filter(user=request.user,
                                            gallery=tutorial.gallery)
            ug.delete()
        except:
            ug = None

        # Delete the tutorial on the repo and on the database.

        old_slug = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], tutorial.get_phy_slug())
        maj_repo_tuto(request, old_slug_path=old_slug, tuto=tutorial,
                      action="del")
        messages.success(request,
                         _(u'Le tutoriel {0} a bien '
                           u'été supprimé.').format(tutorial.title))
        tutorial.delete()
    else:
        tutorial.authors.remove(request.user)

        # user can access to gallery

        try:
            ug = UserGallery.objects.filter(
                user=request.user,
                gallery=tutorial.gallery)
            ug.delete()
        except:
            ug = None
        tutorial.save()
        messages.success(request,
                         _(u'Vous ne faites plus partie des rédacteurs de ce '
                           u'tutoriel.'))
    return redirect(reverse("zds.tutorial.views.index"))


@can_write_and_read_now
@require_POST
def modify_tutorial(request):
    tutorial_pk = request.POST["tutorial"]
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    # User actions

    if request.user in tutorial.authors.all() or request.user.has_perm("tutorial.change_tutorial"):
        if "add_author" in request.POST:
            redirect_url = reverse("zds.tutorial.views.view_tutorial", args=[
                tutorial.pk,
                tutorial.slug,
            ])
            author_username = request.POST["author"]
            author = None
            try:
                author = User.objects.get(username=author_username)
            except User.DoesNotExist:
                return redirect(redirect_url)
            tutorial.authors.add(author)
            tutorial.save()

            # share gallery

            ug = UserGallery()
            ug.user = author
            ug.gallery = tutorial.gallery
            ug.mode = "W"
            ug.save()
            messages.success(request,
                             _(u'L\'auteur {0} a bien été ajouté à la rédaction '
                               u'du tutoriel.').format(author.username))

            # send msg to new author

            msg = (
                _(u'Bonjour **{0}**,\n\n'
                  u'Tu as été ajouté comme auteur du tutoriel [{1}]({2}).\n'
                  u'Tu peux retrouver ce tutoriel en [cliquant ici]({3}), ou *via* le lien "En rédaction" du menu '
                  u'"Tutoriels" sur la page de ton profil.\n\n'
                  u'Tu peux maintenant commencer à rédiger !').format(
                      author.username,
                      tutorial.title,
                      settings.ZDS_APP['site']['url'] + tutorial.get_absolute_url(),
                      settings.ZDS_APP['site']['url'] + reverse("zds.member.views.tutorials"))
            )
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            send_mp(
                bot,
                [author],
                _(u"Ajout en tant qu'auteur : {0}").format(tutorial.title),
                "",
                msg,
                True,
                direct=False,
            )

            return redirect(redirect_url)
        elif "remove_author" in request.POST:
            redirect_url = reverse("zds.tutorial.views.view_tutorial", args=[
                tutorial.pk,
                tutorial.slug,
            ])

            # Avoid orphan tutorials

            if tutorial.authors.all().count() <= 1:
                raise Http404
            author_pk = request.POST["author"]
            author = get_object_or_404(User, pk=author_pk)
            tutorial.authors.remove(author)

            # user can access to gallery

            try:
                ug = UserGallery.objects.filter(user=author,
                                                gallery=tutorial.gallery)
                ug.delete()
            except:
                ug = None
            tutorial.save()
            messages.success(request,
                             _(u"L'auteur {0} a bien été retiré du tutoriel.")
                             .format(author.username))

            # send msg to removed author

            msg = (
                _(u'Bonjour **{0}**,\n\n'
                  u'Tu as été supprimé des auteurs du tutoriel [{1}]({2}). Tant qu\'il ne sera pas publié, tu ne '
                  u'pourra plus y accéder.\n').format(
                      author.username,
                      tutorial.title,
                      settings.ZDS_APP['site']['url'] + tutorial.get_absolute_url())
            )
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            send_mp(
                bot,
                [author],
                _(u"Suppression des auteurs : {0}").format(tutorial.title),
                "",
                msg,
                True,
                direct=False,
            )

            return redirect(redirect_url)
        elif "activ_beta" in request.POST:
            if "version" in request.POST:
                tutorial.sha_beta = request.POST['version']
                tutorial.save()
                topic = Topic.objects.filter(key=tutorial.pk, forum__pk=settings.ZDS_APP['forum']['beta_forum_id'])\
                    .first()
                msg = \
                    (_(u'Bonjour à tous,\n\n'
                       u'J\'ai commencé ({0}) la rédaction d\'un tutoriel dont l\'intitulé est **{1}**.\n\n'
                       u'J\'aimerais obtenir un maximum de retour sur celui-ci, sur le fond ainsi que '
                       u'sur la forme, afin de proposer en validation un texte de qualité.'
                       u'\n\nSi vous êtes intéressé, cliquez ci-dessous '
                       u'\n\n-> [Lien de la beta du tutoriel : {1}]({2}) <-\n\n'
                       u'\n\nMerci d\'avance pour votre aide').format(
                           naturaltime(tutorial.create_at),
                           tutorial.title,
                           settings.ZDS_APP['site']['url'] + tutorial.get_absolute_url_beta()))
                if topic is None:
                    forum = get_object_or_404(Forum, pk=settings.ZDS_APP['forum']['beta_forum_id'])

                    create_topic(author=request.user,
                                 forum=forum,
                                 title=_(u"[beta][tutoriel]{0}").format(tutorial.title),
                                 subtitle=u"{}".format(tutorial.description),
                                 text=msg,
                                 key=tutorial.pk
                                 )
                    tp = Topic.objects.get(key=tutorial.pk)
                    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                    private_mp = \
                        (_(u'Bonjour {},\n\n'
                           u'Vous venez de mettre votre tutoriel **{}** en beta. La communauté '
                           u'pourra le consulter afin de vous faire des retours '
                           u'constructifs avant sa soumission en validation.\n\n'
                           u'Un sujet dédié pour la beta de votre tutoriel a été '
                           u'crée dans le forum et est accessible [ici]({})').format(
                               request.user.username,
                               tutorial.title,
                               settings.ZDS_APP['site']['url'] + tp.get_absolute_url()))
                    send_mp(
                        bot,
                        [request.user],
                        _(u"Tutoriel en beta : {0}").format(tutorial.title),
                        "",
                        private_mp,
                        False,
                    )
                else:
                    msg_up = \
                        (_(u'Bonjour,\n\n'
                           u'La beta du tutoriel est de nouveau active.'
                           u'\n\n-> [Lien de la beta du tutoriel : {0}]({1}) <-\n\n'
                           u'\n\nMerci pour vos relectures').format(tutorial.title,
                                                                    settings.ZDS_APP['site']['url']
                                                                    + tutorial.get_absolute_url_beta()))
                    unlock_topic(topic, msg)
                    send_post(topic, msg_up)

                messages.success(request, _(u"La BETA sur ce tutoriel est bien activée."))
            else:
                messages.error(request, _(u"La BETA sur ce tutoriel n'a malheureusement pas pu être activée."))
            return redirect(tutorial.get_absolute_url_beta())
        elif "update_beta" in request.POST:
            if "version" in request.POST:
                tutorial.sha_beta = request.POST['version']
                tutorial.save()
                topic = Topic.objects.filter(key=tutorial.pk,
                                             forum__pk=settings.ZDS_APP['forum']['beta_forum_id']).first()
                msg = \
                    (_(u'Bonjour à tous,\n\n'
                       u'J\'ai commencé ({0}) la rédaction d\'un tutoriel dont l\'intitulé est **{1}**.\n\n'
                       u'J\'aimerai obtenir un maximum de retour sur celui-ci, sur le fond ainsi que '
                       u'sur la forme, afin de proposer en validation un texte de qualité.'
                       u'\n\nSi vous êtes intéressé, cliquez ci-dessous '
                       u'\n\n-> [Lien de la beta du tutoriel : {1}]({2}) <-\n\n'
                       u'\n\nMerci d\'avance pour votre aide').format(
                           naturaltime(tutorial.create_at),
                           tutorial.title,
                           settings.ZDS_APP['site']['url'] + tutorial.get_absolute_url_beta()))
                if topic is None:
                    forum = get_object_or_404(Forum, pk=settings.ZDS_APP['forum']['beta_forum_id'])

                    create_topic(author=request.user,
                                 forum=forum,
                                 title=u"[beta][tutoriel]{0}".format(tutorial.title),
                                 subtitle=u"{}".format(tutorial.description),
                                 text=msg,
                                 key=tutorial.pk
                                 )
                else:
                    msg_up = \
                        (_(u'Bonjour, !\n\n'
                           u'La beta du tutoriel a été mise à jour.'
                           u'\n\n-> [Lien de la beta du tutoriel : {0}]({1}) <-\n\n'
                           u'\n\nMerci pour vos relectures').format(tutorial.title,
                                                                    settings.ZDS_APP['site']['url']
                                                                    + tutorial.get_absolute_url_beta()))
                    unlock_topic(topic, msg)
                    send_post(topic, msg_up)
                messages.success(request, _(u"La BETA sur ce tutoriel a bien été mise à jour."))
            else:
                messages.error(request, _(u"La BETA sur ce tutoriel n'a malheureusement pas pu être mise à jour."))
            return redirect(tutorial.get_absolute_url_beta())
        elif "desactiv_beta" in request.POST:
            tutorial.sha_beta = None
            tutorial.save()
            topic = Topic.objects.filter(key=tutorial.pk, forum__pk=settings.ZDS_APP['forum']['beta_forum_id']).first()
            if topic is not None:
                msg = \
                    (_(u'Désactivation de la beta du tutoriel  **{}**'
                       u'\n\nPour plus d\'informations envoyez moi un message privé.').format(tutorial.title))
                lock_topic(topic)
                send_post(topic, msg)
            messages.info(request, _(u"La BETA sur ce tutoriel a bien été désactivée."))

            return redirect(tutorial.get_absolute_url())

    # No action performed, raise 403

    raise PermissionDenied


@can_write_and_read_now
@login_required
def add_tutorial(request):
    """'Adds a tutorial."""

    if request.method == "POST":
        form = TutorialForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data

            # Creating a tutorial

            tutorial = PublishableContent()
            tutorial.title = data["title"]
            tutorial.description = data["description"]
            tutorial.type = data["type"]
            tutorial.introduction = "introduction.md"
            tutorial.conclusion = "conclusion.md"
            tutorial.images = "images"
            if "licence" in data and data["licence"] != "":
                lc = Licence.objects.filter(pk=data["licence"]).all()[0]
                tutorial.licence = lc
            else:
                tutorial.licence = Licence.objects.get(
                    pk=settings.ZDS_APP['tutorial']['default_license_pk']
                )

            # add create date

            tutorial.create_at = datetime.now()
            tutorial.pubdate = datetime.now()

            # Creating the gallery

            gal = Gallery()
            gal.title = data["title"]
            gal.slug = slugify(data["title"])
            gal.pubdate = datetime.now()
            gal.save()

            # Attach user to gallery

            userg = UserGallery()
            userg.gallery = gal
            userg.mode = "W"  # write mode
            userg.user = request.user
            userg.save()
            tutorial.gallery = gal

            # Create image

            if "image" in request.FILES:
                img = Image()
                img.physical = request.FILES["image"]
                img.gallery = gal
                img.title = request.FILES["image"]
                img.slug = slugify(request.FILES["image"])
                img.pubdate = datetime.now()
                img.save()
                tutorial.image = img
            tutorial.save()

            # Add subcategories on tutorial

            for subcat in form.cleaned_data["subcategory"]:
                tutorial.subcategory.add(subcat)

            # Add helps if needed
            for helpwriting in form.cleaned_data["helps"]:
                tutorial.helps.add(helpwriting)

            # We need to save the tutorial before changing its author list
            # since it's a many-to-many relationship

            tutorial.authors.add(request.user)

            # If it's a small tutorial, create its corresponding chapter

            if tutorial.type == "MINI":
                chapter = Container()
                chapter.tutorial = tutorial
                chapter.save()
            tutorial.save()
            maj_repo_tuto(
                request,
                new_slug_path=tutorial.get_repo_path(),
                tuto=tutorial,
                introduction=data["introduction"],
                conclusion=data["conclusion"],
                action="add",
                msg=request.POST.get('msg_commit', None)
            )
            return redirect(tutorial.get_absolute_url())
    else:
        form = TutorialForm(
            initial={
                'licence': Licence.objects.get(pk=settings.ZDS_APP['tutorial']['default_license_pk'])
            }
        )
    return render(request, "tutorial/tutorial/new.html", {"form": form})


@can_write_and_read_now
@login_required
def edit_tutorial(request):
    """Edit a tutorial."""

    # Retrieve current tutorial;

    try:
        tutorial_pk = request.GET["tutoriel"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff, he
    # hasn't permission to execute this method:

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied
    introduction = os.path.join(tutorial.get_repo_path(), "introduction.md")
    conclusion = os.path.join(tutorial.get_repo_path(), "conclusion.md")
    if request.method == "POST":
        form = TutorialForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data
            if content_has_changed([introduction, conclusion], data["last_hash"]):
                form = TutorialForm(initial={
                    "title": tutorial.title,
                    "type": tutorial.type,
                    "licence": tutorial.licence,
                    "description": tutorial.description,
                    "subcategory": tutorial.subcategory.all(),
                    "introduction": tutorial.get_introduction(),
                    "conclusion": tutorial.get_conclusion(),
                    "helps": tutorial.helps.all(),
                })
                return render(request, "tutorial/tutorial/edit.html",
                                       {
                                           "tutorial": tutorial, "form": form,
                                           "last_hash": compute_hash([introduction, conclusion]),
                                           "new_version": True
                                       })
            old_slug = tutorial.get_repo_path()
            tutorial.title = data["title"]
            tutorial.description = data["description"]
            if "licence" in data and data["licence"] != "":
                lc = Licence.objects.filter(pk=data["licence"]).all()[0]
                tutorial.licence = lc
            else:
                tutorial.licence = Licence.objects.get(
                    pk=settings.ZDS_APP['tutorial']['default_license_pk']
                )

            # add MAJ date

            tutorial.update = datetime.now()

            # MAJ gallery

            gal = Gallery.objects.filter(pk=tutorial.gallery.pk)
            gal.update(title=data["title"])
            gal.update(slug=slugify(data["title"]))
            gal.update(update=datetime.now())

            # MAJ image

            if "image" in request.FILES:
                img = Image()
                img.physical = request.FILES["image"]
                img.gallery = tutorial.gallery
                img.title = request.FILES["image"]
                img.slug = slugify(request.FILES["image"])
                img.pubdate = datetime.now()
                img.save()
                tutorial.image = img
            tutorial.save()
            tutorial.update_children()

            new_slug = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], tutorial.get_phy_slug())

            maj_repo_tuto(
                request,
                old_slug_path=old_slug,
                new_slug_path=new_slug,
                tuto=tutorial,
                introduction=data["introduction"],
                conclusion=data["conclusion"],
                action="maj",
                msg=request.POST.get('msg_commit', None)
            )

            tutorial.subcategory.clear()
            for subcat in form.cleaned_data["subcategory"]:
                tutorial.subcategory.add(subcat)

            tutorial.helps.clear()
            for help in form.cleaned_data["helps"]:
                tutorial.helps.add(help)

            tutorial.save()
            return redirect(tutorial.get_absolute_url())
    else:
        json = tutorial.load_json_for_public(tutorial.sha_draft)
        if "licence" in json:
            licence = json['licence']
        else:
            licence = Licence.objects.get(
                pk=settings.ZDS_APP['tutorial']['default_license_pk']
            )
        form = TutorialForm(initial={
            "title": json["title"],
            "type": json["type"],
            "licence": licence,
            "description": json["description"],
            "subcategory": tutorial.subcategory.all(),
            "introduction": tutorial.get_introduction(),
            "conclusion": tutorial.get_conclusion(),
            "helps": tutorial.helps.all(),
        })
    return render(request, "tutorial/tutorial/edit.html",
                           {"tutorial": tutorial, "form": form, "last_hash": compute_hash([introduction, conclusion])})

# Parts.


@login_required
def view_part(
    request,
    tutorial_pk,
    tutorial_slug,
    part_pk,
    part_slug,
):
    """Display a part."""

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    try:
        sha = request.GET["version"]
    except KeyError:
        sha = tutorial.sha_draft

    is_beta = sha == tutorial.sha_beta and tutorial.in_beta()

    # Only authors of the tutorial and staff can view tutorial in offline.

    if request.user not in tutorial.authors.all() and not is_beta:
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    final_part = None

    # find the good manifest file

    repo = Repo(tutorial.get_repo_path())
    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    mandata = json_reader.loads(manifest)
    tutorial.load_dic(mandata, sha=sha)

    parts = mandata["parts"]
    find = False
    cpt_p = 1
    for part in parts:
        if part_pk == str(part["pk"]):
            find = True
            part["tutorial"] = tutorial
            part["path"] = tutorial.get_repo_path()
            part["slug"] = slugify(part["title"])
            part["position_in_tutorial"] = cpt_p
            part["intro"] = get_blob(repo.commit(sha).tree, part["introduction"])
            part["conclu"] = get_blob(repo.commit(sha).tree, part["conclusion"])
            cpt_c = 1
            for chapter in part["chapters"]:
                chapter["part"] = part
                chapter["path"] = tutorial.get_repo_path()
                chapter["slug"] = slugify(chapter["title"])
                chapter["type"] = "BIG"
                chapter["position_in_part"] = cpt_c
                chapter["position_in_tutorial"] = cpt_c * cpt_p
                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext["chapter"] = chapter
                    ext["position_in_chapter"] = cpt_e
                    ext["path"] = tutorial.get_repo_path()
                    cpt_e += 1
                cpt_c += 1
            final_part = part
            break
        cpt_p += 1

    # if part can't find
    if not find:
        raise Http404

    if tutorial.js_support:
        is_js = "js"
    else:
        is_js = ""

    return render(request, "tutorial/part/view.html",
                           {"tutorial": mandata,
                            "part": final_part,
                            "version": sha,
                            "is_js": is_js})


def view_part_online(
    request,
    tutorial_pk,
    tutorial_slug,
    part_pk,
    part_slug,
):
    """Display a part."""

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    if not tutorial.in_public():
        raise Http404

    # find the good manifest file

    mandata = tutorial.load_json_for_public()
    tutorial.load_dic(mandata, sha=tutorial.sha_public)
    mandata["update"] = tutorial.update

    mandata["get_parts"] = mandata["parts"]
    parts = mandata["parts"]
    cpt_p = 1
    final_part = None
    find = False
    for part in parts:
        part["tutorial"] = mandata
        part["path"] = tutorial.get_path()
        part["slug"] = slugify(part["title"])
        part["position_in_tutorial"] = cpt_p
        if part_pk == str(part["pk"]):
            find = True
            intro = open(os.path.join(tutorial.get_prod_path(),
                                      part["introduction"] + ".html"), "r")
            part["intro"] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(),
                                       part["conclusion"] + ".html"), "r")
            part["conclu"] = conclu.read()
            conclu.close()
            final_part = part
        cpt_c = 1
        for chapter in part["chapters"]:
            chapter["part"] = part
            chapter["path"] = tutorial.get_path()
            chapter["slug"] = slugify(chapter["title"])
            chapter["type"] = "BIG"
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            if part_slug == slugify(part["title"]):
                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext["chapter"] = chapter
                    ext["position_in_chapter"] = cpt_e
                    ext["path"] = tutorial.get_prod_path()
                    cpt_e += 1
            cpt_c += 1
        part["get_chapters"] = part["chapters"]
        cpt_p += 1

    # if part can't find
    if not find:
        raise Http404

    return render(request, "tutorial/part/view_online.html", {"part": final_part})


@can_write_and_read_now
@login_required
def add_part(request):
    """Add a new part."""

    try:
        tutorial_pk = request.GET["tutoriel"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    # Make sure it's a big tutorial, just in case

    if not tutorial.type == "BIG":
        raise Http404

    # Make sure the user belongs to the author list

    if request.user not in tutorial.authors.all() and not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    if request.method == "POST":
        form = PartForm(request.POST)
        if form.is_valid():
            data = form.data
            part = Container()
            part.tutorial = tutorial
            part.title = data["title"]
            part.position_in_tutorial = tutorial.get_parts().count() + 1
            part.save()
            part.introduction = os.path.join(part.get_phy_slug(), "introduction.md")
            part.conclusion = os.path.join(part.get_phy_slug(), "conclusion.md")
            part.save()

            new_slug = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                    part.tutorial.get_phy_slug(),
                                    part.get_phy_slug())

            maj_repo_part(
                request,
                new_slug_path=new_slug,
                part=part,
                introduction=data["introduction"],
                conclusion=data["conclusion"],
                action="add",
                msg=request.POST.get('msg_commit', None)
            )
            if "submit_continue" in request.POST:
                form = PartForm()
                messages.success(request,
                                 _(u'La partie « {0} » a été ajoutée '
                                   u'avec succès.').format(part.title))
            else:
                return redirect(part.get_absolute_url())
    else:
        form = PartForm()
    return render(request, "tutorial/part/new.html", {"tutorial": tutorial,
                                                      "form": form})


@can_write_and_read_now
@login_required
def modify_part(request):
    """Modifiy the given part."""

    if not request.method == "POST":
        raise Http404
    part_pk = request.POST["part"]
    part = get_object_or_404(Container, pk=part_pk)

    # Make sure the user is allowed to do that

    if request.user not in part.tutorial.authors.all() and not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    if "move" in request.POST:
        try:
            new_pos = int(request.POST["move_target"])
        except ValueError:
            # Invalid conversion, maybe the user played with the move button
            return redirect(part.tutorial.get_absolute_url())

        move(part, new_pos, "position_in_tutorial", "tutorial", "get_parts")
        part.save()

        new_slug_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], part.tutorial.get_phy_slug())

        maj_repo_tuto(request,
                      old_slug_path=new_slug_path,
                      new_slug_path=new_slug_path,
                      tuto=part.tutorial,
                      action="maj",
                      msg=_(u"Déplacement de la partie {} ").format(part.title))
    elif "delete" in request.POST:
        # Delete all chapters belonging to the part

        Container.objects.all().filter(part=part).delete()

        # Move other parts

        old_pos = part.position_in_tutorial
        for tut_p in part.tutorial.get_parts():
            if old_pos <= tut_p.position_in_tutorial:
                tut_p.position_in_tutorial = tut_p.position_in_tutorial - 1
                tut_p.save()
        old_slug = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                part.tutorial.get_phy_slug(),
                                part.get_phy_slug())
        maj_repo_part(request, old_slug_path=old_slug, part=part, action="del")

        new_slug_tuto_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], part.tutorial.get_phy_slug())
        # Actually delete the part
        part.delete()

        maj_repo_tuto(request,
                      old_slug_path=new_slug_tuto_path,
                      new_slug_path=new_slug_tuto_path,
                      tuto=part.tutorial,
                      action="maj",
                      msg=_(u"Suppression de la partie {} ").format(part.title))
    return redirect(part.tutorial.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_part(request):
    """Edit the given part."""

    try:
        part_pk = int(request.GET["partie"])
    except KeyError:
        raise Http404
    except ValueError:
        raise Http404

    part = get_object_or_404(Container, pk=part_pk)
    introduction = os.path.join(part.get_path(), "introduction.md")
    conclusion = os.path.join(part.get_path(), "conclusion.md")
    # Make sure the user is allowed to do that

    if request.user not in part.tutorial.authors.all() and not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    if request.method == "POST":
        form = PartForm(request.POST)
        if form.is_valid():
            data = form.data
            # avoid collision
            if content_has_changed([introduction, conclusion], data["last_hash"]):
                form = PartForm({"title": part.title,
                                 "introduction": part.get_introduction(),
                                 "conclusion": part.get_conclusion()})
                return render(request, "tutorial/part/edit.html",
                                       {
                                           "part": part,
                                           "last_hash": compute_hash([introduction, conclusion]),
                                           "new_version": True,
                                           "form": form
                                       })
            # Update title and his slug.

            part.title = data["title"]
            old_slug = part.get_path()
            part.save()

            # Update path for introduction and conclusion.
            part.introduction = os.path.join(part.get_phy_slug(), "introduction.md")
            part.conclusion = os.path.join(part.get_phy_slug(), "conclusion.md")
            part.save()
            part.update_children()

            new_slug = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                    part.tutorial.get_phy_slug(),
                                    part.get_phy_slug())

            maj_repo_part(
                request,
                old_slug_path=old_slug,
                new_slug_path=new_slug,
                part=part,
                introduction=data["introduction"],
                conclusion=data["conclusion"],
                action="maj",
                msg=request.POST.get('msg_commit', None)
            )
            return redirect(part.get_absolute_url())
    else:
        form = PartForm({"title": part.title,
                         "introduction": part.get_introduction(),
                         "conclusion": part.get_conclusion()})
    return render(request, "tutorial/part/edit.html",
                           {
                               "part": part,
                               "last_hash": compute_hash([introduction, conclusion]),
                               "form": form
                           })


# Containers.


@login_required
def view_chapter(
    request,
    tutorial_pk,
    tutorial_slug,
    part_pk,
    part_slug,
    chapter_pk,
    chapter_slug,
):
    """View chapter."""

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    try:
        sha = request.GET["version"]
    except KeyError:
        sha = tutorial.sha_draft

    is_beta = sha == tutorial.sha_beta and tutorial.in_beta()

    # Only authors of the tutorial and staff can view tutorial in offline.

    if request.user not in tutorial.authors.all() and not is_beta:
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    # find the good manifest file

    repo = Repo(tutorial.get_repo_path())
    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    mandata = json_reader.loads(manifest)
    tutorial.load_dic(mandata, sha=sha)

    parts = mandata["parts"]
    cpt_p = 1
    final_chapter = None
    chapter_tab = []
    final_position = 0
    find = False
    for part in parts:
        cpt_c = 1
        part["slug"] = slugify(part["title"])
        part["get_absolute_url"] = reverse(
            "zds.tutorial.views.view_part",
            args=[
                tutorial.pk,
                tutorial.slug,
                part["pk"],
                part["slug"]])
        part["tutorial"] = tutorial
        for chapter in part["chapters"]:
            chapter["part"] = part
            chapter["path"] = tutorial.get_repo_path()
            chapter["slug"] = slugify(chapter["title"])
            chapter["type"] = "BIG"
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            chapter["get_absolute_url"] = part["get_absolute_url"] \
                + "{0}/{1}/".format(chapter["pk"], chapter["slug"])
            if chapter_pk == str(chapter["pk"]):
                find = True
                chapter["intro"] = get_blob(repo.commit(sha).tree,
                                            chapter["introduction"])
                chapter["conclu"] = get_blob(repo.commit(sha).tree,
                                             chapter["conclusion"])

                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext["chapter"] = chapter
                    ext["position_in_chapter"] = cpt_e
                    ext["path"] = tutorial.get_repo_path()
                    ext["txt"] = get_blob(repo.commit(sha).tree, ext["text"])
                    cpt_e += 1
            chapter_tab.append(chapter)
            if chapter_pk == str(chapter["pk"]):
                final_chapter = chapter
                final_position = len(chapter_tab) - 1
            cpt_c += 1
        cpt_p += 1

    # if chapter can't find
    if not find:
        raise Http404

    prev_chapter = (chapter_tab[final_position - 1] if final_position
                    > 0 else None)
    next_chapter = (chapter_tab[final_position + 1] if final_position + 1
                    < len(chapter_tab) else None)

    if tutorial.js_support:
        is_js = "js"
    else:
        is_js = ""

    return render(request, "tutorial/chapter/view.html", {
        "tutorial": mandata,
        "chapter": final_chapter,
        "prev": prev_chapter,
        "next": next_chapter,
        "version": sha,
        "is_js": is_js
    })


def view_chapter_online(
    request,
    tutorial_pk,
    tutorial_slug,
    part_pk,
    part_slug,
    chapter_pk,
    chapter_slug,
):
    """View chapter."""

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    if not tutorial.in_public():
        raise Http404

    # find the good manifest file

    mandata = tutorial.load_json_for_public()
    tutorial.load_dic(mandata, sha=tutorial.sha_public)
    mandata["update"] = tutorial.update

    mandata['get_parts'] = mandata["parts"]
    parts = mandata["parts"]
    cpt_p = 1
    final_chapter = None
    chapter_tab = []
    final_position = 0

    find = False
    for part in parts:
        cpt_c = 1
        part["slug"] = slugify(part["title"])
        part["get_absolute_url_online"] = reverse(
            "zds.tutorial.views.view_part_online",
            args=[
                tutorial.pk,
                tutorial.slug,
                part["pk"],
                part["slug"]])
        part["tutorial"] = mandata
        part["position_in_tutorial"] = cpt_p
        part["get_chapters"] = part["chapters"]
        for chapter in part["chapters"]:
            chapter["part"] = part
            chapter["path"] = tutorial.get_prod_path()
            chapter["slug"] = slugify(chapter["title"])
            chapter["type"] = "BIG"
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            chapter["get_absolute_url_online"] = part[
                "get_absolute_url_online"] + "{0}/{1}/".format(chapter["pk"], chapter["slug"])
            if chapter_pk == str(chapter["pk"]):
                find = True
                intro = open(
                    os.path.join(
                        tutorial.get_prod_path(),
                        chapter["introduction"] +
                        ".html"),
                    "r")
                chapter["intro"] = intro.read()
                intro.close()
                conclu = open(
                    os.path.join(
                        tutorial.get_prod_path(),
                        chapter["conclusion"] +
                        ".html"),
                    "r")
                chapter["conclu"] = conclu.read()
                conclu.close()
                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext["chapter"] = chapter
                    ext["position_in_chapter"] = cpt_e
                    ext["path"] = tutorial.get_path()
                    text = open(os.path.join(tutorial.get_prod_path(),
                                             ext["text"] + ".html"), "r")
                    ext["txt"] = text.read()
                    text.close()
                    cpt_e += 1
            else:
                intro = None
                conclu = None
            chapter_tab.append(chapter)
            if chapter_pk == str(chapter["pk"]):
                final_chapter = chapter
                final_position = len(chapter_tab) - 1
            cpt_c += 1
        cpt_p += 1

    # if chapter can't find
    if not find:
        raise Http404

    prev_chapter = (chapter_tab[final_position - 1] if final_position > 0 else None)
    next_chapter = (chapter_tab[final_position + 1] if final_position + 1 < len(chapter_tab) else None)

    return render(request, "tutorial/chapter/view_online.html", {
        "chapter": final_chapter,
        "parts": parts,
        "prev": prev_chapter,
        "next": next_chapter,
    })


@can_write_and_read_now
@login_required
def add_chapter(request):
    """Add a new chapter to given part."""

    try:
        part_pk = request.GET["partie"]
    except KeyError:
        raise Http404
    part = get_object_or_404(Container, pk=part_pk)

    # Make sure the user is allowed to do that

    if request.user not in part.tutorial.authors.all() and not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    if request.method == "POST":
        form = ChapterForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data
            chapter = Container()
            chapter.title = data["title"]
            chapter.part = part
            chapter.position_in_part = part.get_chapters().count() + 1
            chapter.update_position_in_tutorial()

            # Create image

            if "image" in request.FILES:
                img = Image()
                img.physical = request.FILES["image"]
                img.gallery = part.tutorial.gallery
                img.title = request.FILES["image"]
                img.slug = slugify(request.FILES["image"])
                img.pubdate = datetime.now()
                img.save()
                chapter.image = img

            chapter.save()
            if chapter.tutorial:
                chapter_path = os.path.join(
                    os.path.join(
                        settings.ZDS_APP['tutorial']['repo_path'],
                        chapter.tutorial.get_phy_slug()),
                    chapter.get_phy_slug())
                chapter.introduction = os.path.join(chapter.get_phy_slug(),
                                                    "introduction.md")
                chapter.conclusion = os.path.join(chapter.get_phy_slug(),
                                                  "conclusion.md")
            else:
                chapter_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                            chapter.part.tutorial.get_phy_slug(),
                                            chapter.part.get_phy_slug(),
                                            chapter.get_phy_slug())
                chapter.introduction = os.path.join(
                    chapter.part.get_phy_slug(),
                    chapter.get_phy_slug(),
                    "introduction.md")
                chapter.conclusion = os.path.join(chapter.part.get_phy_slug(), chapter.get_phy_slug(), "conclusion.md")
            chapter.save()
            maj_repo_chapter(
                request,
                new_slug_path=chapter_path,
                chapter=chapter,
                introduction=data["introduction"],
                conclusion=data["conclusion"],
                action="add",
                msg=request.POST.get('msg_commit', None)
            )
            if "submit_continue" in request.POST:
                form = ChapterForm()
                messages.success(request,
                                 _(u'Le chapitre « {0} » a été ajouté '
                                   u'avec succès.').format(chapter.title))
            else:
                return redirect(chapter.get_absolute_url())
    else:
        form = ChapterForm()

    return render(request, "tutorial/chapter/new.html", {"part": part,
                                                         "form": form})


@can_write_and_read_now
@login_required
def modify_chapter(request):
    """Modify the given chapter."""

    if not request.method == "POST":
        raise Http404
    data = request.POST
    try:
        chapter_pk = request.POST["chapter"]
    except KeyError:
        raise Http404
    chapter = get_object_or_404(Container, pk=chapter_pk)

    # Make sure the user is allowed to do that

    if request.user not in chapter.get_tutorial().authors.all() and \
            not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    if "move" in data:
        try:
            new_pos = int(request.POST["move_target"])
        except ValueError:

            # User misplayed with the move button

            return redirect(chapter.get_absolute_url())
        move(chapter, new_pos, "position_in_part", "part", "get_chapters")
        chapter.update_position_in_tutorial()
        chapter.save()

        new_slug_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], chapter.part.tutorial.get_phy_slug())

        maj_repo_part(request,
                      old_slug_path=new_slug_path,
                      new_slug_path=new_slug_path,
                      part=chapter.part,
                      action="maj",
                      msg=_(u"Déplacement du chapitre {}").format(chapter.title))
        messages.info(request, _(u"Le chapitre a bien été déplacé."))
    elif "delete" in data:
        old_pos = chapter.position_in_part
        old_tut_pos = chapter.position_in_tutorial

        if chapter.part:
            parent = chapter.part
        else:
            parent = chapter.tutorial

        # Move other chapters first

        for tut_c in chapter.part.get_chapters():
            if old_pos <= tut_c.position_in_part:
                tut_c.position_in_part = tut_c.position_in_part - 1
                tut_c.save()
        maj_repo_chapter(request, chapter=chapter,
                         old_slug_path=chapter.get_path(), action="del")

        # Then delete the chapter
        new_slug_path_part = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                          chapter.part.tutorial.get_phy_slug())
        chapter.delete()

        # Update all the position_in_tutorial fields for the next chapters

        for tut_c in \
                Container.objects.filter(position_in_tutorial__gt=old_tut_pos):
            tut_c.update_position_in_tutorial()
            tut_c.save()

        maj_repo_part(request,
                      old_slug_path=new_slug_path_part,
                      new_slug_path=new_slug_path_part,
                      part=chapter.part,
                      action="maj",
                      msg=_(u"Suppression du chapitre {}").format(chapter.title))
        messages.info(request, _(u"Le chapitre a bien été supprimé."))

        return redirect(parent.get_absolute_url())

    return redirect(chapter.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_chapter(request):
    """Edit the given chapter."""

    try:
        chapter_pk = int(request.GET["chapitre"])
    except KeyError:
        raise Http404
    except ValueError:
        raise Http404

    chapter = get_object_or_404(Container, pk=chapter_pk)
    big = chapter.part
    small = chapter.tutorial

    # Make sure the user is allowed to do that

    if (big and request.user not in chapter.part.tutorial.authors.all()
        or small and request.user not in chapter.tutorial.authors.all())\
            and not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    introduction = os.path.join(chapter.get_path(), "introduction.md")
    conclusion = os.path.join(chapter.get_path(), "conclusion.md")
    if request.method == "POST":

        if chapter.part:
            form = ChapterForm(request.POST, request.FILES)
            gal = chapter.part.tutorial.gallery
        else:
            form = EmbdedChapterForm(request.POST, request.FILES)
            gal = chapter.tutorial.gallery
        if form.is_valid():
            data = form.data
            # avoid collision
            if content_has_changed([introduction, conclusion], data["last_hash"]):
                form = render_chapter_form(chapter)
                return render(request, "tutorial/part/edit.html",
                                       {
                                           "chapter": chapter,
                                           "last_hash": compute_hash([introduction, conclusion]),
                                           "new_version": True,
                                           "form": form
                                       })
            chapter.title = data["title"]

            old_slug = chapter.get_path()
            chapter.save()
            chapter.update_children()

            if chapter.part:
                if chapter.tutorial:
                    new_slug = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                            chapter.tutorial.get_phy_slug(),
                                            chapter.get_phy_slug())
                else:
                    new_slug = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                            chapter.part.tutorial.get_phy_slug(),
                                            chapter.part.get_phy_slug(),
                                            chapter.get_phy_slug())

                # Create image

                if "image" in request.FILES:
                    img = Image()
                    img.physical = request.FILES["image"]
                    img.gallery = gal
                    img.title = request.FILES["image"]
                    img.slug = slugify(request.FILES["image"])
                    img.pubdate = datetime.now()
                    img.save()
                    chapter.image = img
            maj_repo_chapter(
                request,
                old_slug_path=old_slug,
                new_slug_path=new_slug,
                chapter=chapter,
                introduction=data["introduction"],
                conclusion=data["conclusion"],
                action="maj",
                msg=request.POST.get('msg_commit', None)
            )
            return redirect(chapter.get_absolute_url())
    else:
        form = render_chapter_form(chapter)
    return render(request, "tutorial/chapter/edit.html", {"chapter": chapter,
                                                          "last_hash": compute_hash([introduction, conclusion]),
                                                          "form": form})


@login_required
def add_extract(request):
    """Add extract."""

    try:
        chapter_pk = int(request.GET["chapitre"])
    except KeyError:
        raise Http404
    except ValueError:
        raise Http404

    chapter = get_object_or_404(Container, pk=chapter_pk)
    part = chapter.part

    # If part exist, we check if the user is in authors of the tutorial of the
    # part or If part doesn't exist, we check if the user is in authors of the
    # tutorial of the chapter.

    if part and request.user not in chapter.part.tutorial.authors.all() \
            or not part and request.user not in chapter.tutorial.authors.all():

        # If the user isn't an author or a staff, we raise an exception.

        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied
    if request.method == "POST":
        data = request.POST

        # Using the « preview button »

        if "preview" in data:
            form = ExtractForm(initial={"title": data["title"],
                                        "text": data["text"],
                                        'msg_commit': data['msg_commit']})
            return render(request, "tutorial/extract/new.html",
                                   {"chapter": chapter, "form": form})
        else:

            # Save extract.

            form = ExtractForm(request.POST)
            if form.is_valid():
                data = form.data
                extract = Extract()
                extract.chapter = chapter
                extract.position_in_chapter = chapter.get_extract_count() + 1
                extract.title = data["title"]
                extract.save()
                extract.text = extract.get_path(relative=True)
                extract.save()
                maj_repo_extract(request, new_slug_path=extract.get_path(),
                                 extract=extract, text=data["text"],
                                 action="add",
                                 msg=request.POST.get('msg_commit', None))
                return redirect(extract.get_absolute_url())
    else:
        form = ExtractForm()

    return render(request, "tutorial/extract/new.html", {"chapter": chapter,
                                                         "form": form})


@can_write_and_read_now
@login_required
def edit_extract(request):
    """Edit extract."""
    try:
        extract_pk = request.GET["extrait"]
    except KeyError:
        raise Http404
    extract = get_object_or_404(Extract, pk=extract_pk)
    part = extract.chapter.part

    # If part exist, we check if the user is in authors of the tutorial of the
    # part or If part doesn't exist, we check if the user is in authors of the
    # tutorial of the chapter.

    if part and request.user \
            not in extract.chapter.part.tutorial.authors.all() or not part \
            and request.user not in extract.chapter.tutorial.authors.all():

        # If the user isn't an author or a staff, we raise an exception.

        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    if request.method == "POST":
        data = request.POST
        # Using the « preview button »

        if "preview" in data:
            form = ExtractForm(initial={
                "title": data["title"],
                "text": data["text"],
                'msg_commit': data['msg_commit']
            })
            return render(request, "tutorial/extract/edit.html",
                                   {
                                       "extract": extract, "form": form,
                                       "last_hash": compute_hash([extract.get_path()])
                                   })
        else:
            if content_has_changed([extract.get_path()], data["last_hash"]):
                form = ExtractForm(initial={
                    "title": extract.title,
                    "text": extract.get_text(),
                    'msg_commit': data['msg_commit']})
                return render(request, "tutorial/extract/edit.html",
                                       {
                                           "extract": extract,
                                           "last_hash": compute_hash([extract.get_path()]),
                                           "new_version": True,
                                           "form": form
                                       })
            # Edit extract.

            form = ExtractForm(request.POST)
            if form.is_valid():
                data = form.data
                old_slug = extract.get_path()
                extract.title = data["title"]
                extract.text = extract.get_path(relative=True)

                # Use path retrieve before and use it to create the new slug.
                extract.save()
                new_slug = extract.get_path()

                maj_repo_extract(
                    request,
                    old_slug_path=old_slug,
                    new_slug_path=new_slug,
                    extract=extract,
                    text=data["text"],
                    action="maj",
                    msg=request.POST.get('msg_commit', None)
                )
                return redirect(extract.get_absolute_url())
    else:
        form = ExtractForm({"title": extract.title,
                            "text": extract.get_text()})
    return render(request, "tutorial/extract/edit.html",
                           {
                               "extract": extract,
                               "last_hash": compute_hash([extract.get_path()]),
                               "form": form
                           })


@can_write_and_read_now
def modify_extract(request):
    if not request.method == "POST":
        raise Http404
    data = request.POST
    try:
        extract_pk = request.POST["extract"]
    except KeyError:
        raise Http404
    extract = get_object_or_404(Extract, pk=extract_pk)
    chapter = extract.chapter
    if "delete" in data:
        pos_current_extract = extract.position_in_chapter
        for extract_c in extract.chapter.get_extracts():
            if pos_current_extract <= extract_c.position_in_chapter:
                extract_c.position_in_chapter = extract_c.position_in_chapter \
                    - 1
                extract_c.save()

        # Use path retrieve before and use it to create the new slug.

        old_slug = extract.get_path()

        if extract.chapter.tutorial:
            new_slug_path_chapter = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                                 extract.chapter.tutorial.get_phy_slug())
        else:
            new_slug_path_chapter = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                                 chapter.part.tutorial.get_phy_slug(),
                                                 chapter.part.get_phy_slug(),
                                                 chapter.get_phy_slug())

        maj_repo_extract(request, old_slug_path=old_slug, extract=extract,
                         action="del")

        maj_repo_chapter(request,
                         old_slug_path=new_slug_path_chapter,
                         new_slug_path=new_slug_path_chapter,
                         chapter=chapter,
                         action="maj",
                         msg=_(u"Suppression de l'extrait {}").format(extract.title))
        return redirect(chapter.get_absolute_url())
    elif "move" in data:
        try:
            new_pos = int(request.POST["move_target"])
        except ValueError:
            # Error, the user misplayed with the move button
            return redirect(extract.get_absolute_url())

        move(extract, new_pos, "position_in_chapter", "chapter", "get_extracts")
        extract.save()

        if extract.chapter.tutorial:
            new_slug_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                         extract.chapter.tutorial.get_phy_slug())
        else:
            new_slug_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                         chapter.part.tutorial.get_phy_slug(),
                                         chapter.part.get_phy_slug(),
                                         chapter.get_phy_slug())

        maj_repo_chapter(request,
                         old_slug_path=new_slug_path,
                         new_slug_path=new_slug_path,
                         chapter=chapter,
                         action="maj",
                         msg=_(u"Déplacement de l'extrait {}").format(extract.title))
        return redirect(extract.get_absolute_url())
    raise Http404


def find_tuto(request, pk_user):
    try:
        type = request.GET["type"]
    except KeyError:
        type = None
    display_user = get_object_or_404(User, pk=pk_user)
    if type == "beta":
        tutorials = PublishableContent.objects.all().filter(
            authors__in=[display_user],
            sha_beta__isnull=False).exclude(sha_beta="").order_by("-pubdate")

        tuto_versions = []
        for tutorial in tutorials:
            mandata = tutorial.load_json_for_public(sha=tutorial.sha_beta)
            tutorial.load_dic(mandata, sha=tutorial.sha_beta)
            tuto_versions.append(mandata)

        return render(request, "tutorial/member/beta.html",
                               {"tutorials": tuto_versions, "usr": display_user})
    else:
        tutorials = PublishableContent.objects.all().filter(
            authors__in=[display_user],
            sha_public__isnull=False).exclude(sha_public="").order_by("-pubdate")

        tuto_versions = []
        for tutorial in tutorials:
            mandata = tutorial.load_json_for_public()
            tutorial.load_dic(mandata)
            tuto_versions.append(mandata)

        return render(request, "tutorial/member/online.html", {"tutorials": tuto_versions,
                                                               "usr": display_user})


def upload_images(images, tutorial):
    mapping = OrderedDict()

    # download images

    zfile = zipfile.ZipFile(images, "a")
    os.makedirs(os.path.abspath(os.path.join(tutorial.get_repo_path(), "images")))
    for i in zfile.namelist():
        ph_temp = os.path.abspath(os.path.join(tutorial.get_repo_path(), i))
        try:
            data = zfile.read(i)
            fp = open(ph_temp, "wb")
            fp.write(data)
            fp.close()
            f = File(open(ph_temp, "rb"))
            f.name = os.path.basename(i)
            pic = Image()
            pic.gallery = tutorial.gallery
            pic.title = os.path.basename(i)
            pic.pubdate = datetime.now()
            pic.physical = f
            pic.save()
            mapping[i] = pic.physical.url
            f.close()
        except IOError:
            try:
                os.makedirs(ph_temp)
            except OSError:
                pass
    zfile.close()
    return mapping


def replace_real_url(md_text, dict):
    for (dt_old, dt_new) in dict.iteritems():
        md_text = md_text.replace(dt_old, dt_new)
    return md_text


def import_content(
    request,
    tuto,
    images,
    logo,
):
    tutorial = PublishableContent()

    # add create date

    tutorial.create_at = datetime.now()
    tree = etree.parse(tuto)
    racine_big = tree.xpath("/bigtuto")
    racine_mini = tree.xpath("/minituto")
    if len(racine_big) > 0:

        # it's a big tuto

        tutorial.type = "BIG"
        tutorial_title = tree.xpath("/bigtuto/titre")[0]
        tutorial_intro = tree.xpath("/bigtuto/introduction")[0]
        tutorial_conclu = tree.xpath("/bigtuto/conclusion")[0]
        tutorial.title = tutorial_title.text.strip()
        tutorial.description = tutorial_title.text.strip()
        tutorial.images = "images"
        tutorial.introduction = "introduction.md"
        tutorial.conclusion = "conclusion.md"

        # Creating the gallery

        gal = Gallery()
        gal.title = tutorial_title.text
        gal.slug = slugify(tutorial_title.text)
        gal.pubdate = datetime.now()
        gal.save()

        # Attach user to gallery

        userg = UserGallery()
        userg.gallery = gal
        userg.mode = "W"  # write mode
        userg.user = request.user
        userg.save()
        tutorial.gallery = gal
        tutorial.save()
        tuto_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], tutorial.get_phy_slug())
        mapping = upload_images(images, tutorial)
        maj_repo_tuto(
            request,
            new_slug_path=tuto_path,
            tuto=tutorial,
            introduction=replace_real_url(tutorial_intro.text, mapping),
            conclusion=replace_real_url(tutorial_conclu.text, mapping),
            action="add",
        )
        tutorial.authors.add(request.user)
        part_count = 1
        for partie in tree.xpath("/bigtuto/parties/partie"):
            part_title = tree.xpath("/bigtuto/parties/partie["
                                    + str(part_count) + "]/titre")[0]
            part_intro = tree.xpath("/bigtuto/parties/partie["
                                    + str(part_count) + "]/introduction")[0]
            part_conclu = tree.xpath("/bigtuto/parties/partie["
                                     + str(part_count) + "]/conclusion")[0]
            part = Container()
            part.title = part_title.text.strip()
            part.position_in_tutorial = part_count
            part.tutorial = tutorial
            part.save()
            part.introduction = os.path.join(part.get_phy_slug(), "introduction.md")
            part.conclusion = os.path.join(part.get_phy_slug(), "conclusion.md")
            part_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                     part.tutorial.get_phy_slug(),
                                     part.get_phy_slug())
            part.save()
            maj_repo_part(
                request,
                None,
                part_path,
                part,
                replace_real_url(part_intro.text, mapping),
                replace_real_url(part_conclu.text, mapping),
                action="add",
            )
            chapter_count = 1
            for chapitre in tree.xpath("/bigtuto/parties/partie["
                                       + str(part_count)
                                       + "]/chapitres/chapitre"):
                chapter_title = tree.xpath(
                    "/bigtuto/parties/partie[" +
                    str(part_count) +
                    "]/chapitres/chapitre[" +
                    str(chapter_count) +
                    "]/titre")[0]
                chapter_intro = tree.xpath(
                    "/bigtuto/parties/partie[" +
                    str(part_count) +
                    "]/chapitres/chapitre[" +
                    str(chapter_count) +
                    "]/introduction")[0]
                chapter_conclu = tree.xpath(
                    "/bigtuto/parties/partie[" +
                    str(part_count) +
                    "]/chapitres/chapitre[" +
                    str(chapter_count) +
                    "]/conclusion")[0]
                chapter = Container()
                chapter.title = chapter_title.text.strip()
                chapter.position_in_part = chapter_count
                chapter.position_in_tutorial = part_count * chapter_count
                chapter.part = part
                chapter.save()
                chapter.introduction = os.path.join(
                    part.get_phy_slug(),
                    chapter.get_phy_slug(),
                    "introduction.md")
                chapter.conclusion = os.path.join(
                    part.get_phy_slug(),
                    chapter.get_phy_slug(),
                    "conclusion.md")
                chapter_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                            chapter.part.tutorial.get_phy_slug(),
                                            chapter.part.get_phy_slug(),
                                            chapter.get_phy_slug())
                chapter.save()
                maj_repo_chapter(
                    request,
                    new_slug_path=chapter_path,
                    chapter=chapter,
                    introduction=replace_real_url(chapter_intro.text,
                                                  mapping),
                    conclusion=replace_real_url(chapter_conclu.text, mapping),
                    action="add",
                )
                extract_count = 1
                for souspartie in tree.xpath("/bigtuto/parties/partie["
                                             + str(part_count) + "]/chapitres/chapitre["
                                             + str(chapter_count) + "]/sousparties/souspartie"):
                    extract_title = tree.xpath(
                        "/bigtuto/parties/partie[" +
                        str(part_count) +
                        "]/chapitres/chapitre[" +
                        str(chapter_count) +
                        "]/sousparties/souspartie[" +
                        str(extract_count) +
                        "]/titre")[0]
                    extract_text = tree.xpath(
                        "/bigtuto/parties/partie[" +
                        str(part_count) +
                        "]/chapitres/chapitre[" +
                        str(chapter_count) +
                        "]/sousparties/souspartie[" +
                        str(extract_count) +
                        "]/texte")[0]
                    extract = Extract()
                    extract.title = extract_title.text.strip()
                    extract.position_in_chapter = extract_count
                    extract.chapter = chapter
                    extract.save()
                    extract.text = extract.get_path(relative=True)
                    extract.save()
                    maj_repo_extract(
                        request,
                        new_slug_path=extract.get_path(),
                        extract=extract,
                        text=replace_real_url(
                            extract_text.text,
                            mapping),
                        action="add")
                    extract_count += 1
                chapter_count += 1
            part_count += 1
    elif len(racine_mini) > 0:

        # it's a mini tuto

        tutorial.type = "MINI"
        tutorial_title = tree.xpath("/minituto/titre")[0]
        tutorial_intro = tree.xpath("/minituto/introduction")[0]
        tutorial_conclu = tree.xpath("/minituto/conclusion")[0]
        tutorial.title = tutorial_title.text.strip()
        tutorial.description = tutorial_title.text.strip()
        tutorial.images = "images"
        tutorial.introduction = "introduction.md"
        tutorial.conclusion = "conclusion.md"

        # Creating the gallery

        gal = Gallery()
        gal.title = tutorial_title.text
        gal.slug = slugify(tutorial_title.text)
        gal.pubdate = datetime.now()
        gal.save()

        # Attach user to gallery

        userg = UserGallery()
        userg.gallery = gal
        userg.mode = "W"  # write mode
        userg.user = request.user
        userg.save()
        tutorial.gallery = gal
        tutorial.save()
        tuto_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], tutorial.get_phy_slug())
        mapping = upload_images(images, tutorial)
        maj_repo_tuto(
            request,
            new_slug_path=tuto_path,
            tuto=tutorial,
            introduction=replace_real_url(tutorial_intro.text, mapping),
            conclusion=replace_real_url(tutorial_conclu.text, mapping),
            action="add",
        )
        tutorial.authors.add(request.user)
        chapter = Container()
        chapter.tutorial = tutorial
        chapter.save()
        extract_count = 1
        for souspartie in tree.xpath("/minituto/sousparties/souspartie"):
            extract_title = tree.xpath("/minituto/sousparties/souspartie["
                                       + str(extract_count) + "]/titre")[0]
            extract_text = tree.xpath("/minituto/sousparties/souspartie["
                                      + str(extract_count) + "]/texte")[0]
            extract = Extract()
            extract.title = extract_title.text.strip()
            extract.position_in_chapter = extract_count
            extract.chapter = chapter
            extract.save()
            extract.text = extract.get_path(relative=True)
            extract.save()
            maj_repo_extract(request, new_slug_path=extract.get_path(),
                             extract=extract,
                             text=replace_real_url(extract_text.text,
                                                   mapping), action="add")
            extract_count += 1


@can_write_and_read_now
@login_required
@require_POST
def local_import(request):
    import_content(request, request.POST["tuto"], request.POST["images"],
                   request.POST["logo"])
    return redirect(reverse("zds.member.views.tutorials"))


@can_write_and_read_now
@login_required
def import_tuto(request):
    if request.method == "POST":
        # for import tuto
        if "import-tuto" in request.POST:
            form = ImportForm(request.POST, request.FILES)
            if form.is_valid():
                import_content(request, request.FILES["file"], request.FILES["images"], "")
                return redirect(reverse("zds.member.views.tutorials"))
            else:
                form_archive = ImportArchiveForm(user=request.user)

        elif "import-archive" in request.POST:
            form_archive = ImportArchiveForm(request.user, request.POST, request.FILES)
            if form_archive.is_valid():
                (check, reason) = import_archive(request)
                if not check:
                    messages.error(request, reason)
                else:
                    messages.success(request, reason)
                    return redirect(reverse("zds.member.views.tutorials"))
            else:
                form = ImportForm()

    else:
        form = ImportForm()
        form_archive = ImportArchiveForm(user=request.user)

    profile = get_object_or_404(Profile, user=request.user)
    oldtutos = []
    if profile.sdz_tutorial:
        olds = profile.sdz_tutorial.strip().split(":")
    else:
        olds = []
    for old in olds:
        oldtutos.append(get_info_old_tuto(old))
    return render(
        request,
        "tutorial/tutorial/import.html",
        {"form": form, "form_archive": form_archive, "old_tutos": oldtutos}
    )


# Handling repo
def maj_repo_tuto(
    request,
    old_slug_path=None,
    new_slug_path=None,
    tuto=None,
    introduction=None,
    conclusion=None,
    action=None,
    msg=None,
):

    if action == "del":
        shutil.rmtree(old_slug_path)
    else:
        if action == "maj":
            if old_slug_path != new_slug_path:
                shutil.move(old_slug_path, new_slug_path)
                repo = Repo(new_slug_path)
            msg = _(u"Modification du tutoriel : «{}» {} {}").format(tuto.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()

        elif action == "add":
            if not os.path.exists(new_slug_path):
                os.makedirs(new_slug_path, mode=0o777)
            repo = Repo.init(new_slug_path, bare=False)
            msg = _(u"Création du tutoriel «{}» {} {}").format(tuto.title, get_sep(msg), get_text_is_empty(msg)).strip()
        repo = Repo(new_slug_path)
        index = repo.index
        man_path = os.path.join(new_slug_path, "manifest.json")
        tuto.dump_json(path=man_path)
        index.add(["manifest.json"])
        if introduction is not None:
            intro = open(os.path.join(new_slug_path, "introduction.md"), "w")
            intro.write(smart_str(introduction).strip())
            intro.close()
            index.add(["introduction.md"])
        if conclusion is not None:
            conclu = open(os.path.join(new_slug_path, "conclusion.md"), "w")
            conclu.write(smart_str(conclusion).strip())
            conclu.close()
            index.add(["conclusion.md"])
        aut_user = str(request.user.pk)
        aut_email = str(request.user.email)
        if aut_email is None or aut_email.strip() == "":
            aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['dns'])
        com = index.commit(
            msg,
            author=Actor(
                aut_user,
                aut_email),
            committer=Actor(
                aut_user,
                aut_email))
        tuto.sha_draft = com.hexsha
        tuto.save()


def maj_repo_part(
    request,
    old_slug_path=None,
    new_slug_path=None,
    part=None,
    introduction=None,
    conclusion=None,
    action=None,
    msg=None,
):

    repo = Repo(part.tutorial.get_repo_path())
    index = repo.index
    if action == "del":
        shutil.rmtree(old_slug_path)
        msg = _(u"Suppresion de la partie : «{}»").format(part.title)
    else:
        if action == "maj":
            if old_slug_path != new_slug_path:
                os.rename(old_slug_path, new_slug_path)

            msg = _(u"Modification de la partie «{}» {} {}").format(part.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()
        elif action == "add":
            if not os.path.exists(new_slug_path):
                os.makedirs(new_slug_path, mode=0o777)
            msg = _(u"Création de la partie «{}» {} {}").format(part.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()
        index.add([part.get_phy_slug()])
        man_path = os.path.join(part.tutorial.get_repo_path(), "manifest.json")
        part.tutorial.dump_json(path=man_path)
        index.add(["manifest.json"])
        if introduction is not None:
            intro = open(os.path.join(new_slug_path, "introduction.md"), "w")
            intro.write(smart_str(introduction).strip())
            intro.close()
            index.add([os.path.join(part.get_repo_path(relative=True), "introduction.md")])
        if conclusion is not None:
            conclu = open(os.path.join(new_slug_path, "conclusion.md"), "w")
            conclu.write(smart_str(conclusion).strip())
            conclu.close()
            index.add([os.path.join(part.get_repo_path(relative=True), "conclusion.md"
                                    )])
    aut_user = str(request.user.pk)
    aut_email = str(request.user.email)
    if aut_email is None or aut_email.strip() == "":
        aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['litteral_name'])
    com_part = index.commit(
        msg,
        author=Actor(
            aut_user,
            aut_email),
        committer=Actor(
            aut_user,
            aut_email))
    part.tutorial.sha_draft = com_part.hexsha
    part.tutorial.save()
    part.save()


def maj_repo_chapter(
    request,
    old_slug_path=None,
    new_slug_path=None,
    chapter=None,
    introduction=None,
    conclusion=None,
    action=None,
    msg=None,
):

    if chapter.tutorial:
        repo = Repo(os.path.join(settings.ZDS_APP['tutorial']['repo_path'], chapter.tutorial.get_phy_slug()))
        ph = None
    else:
        repo = Repo(os.path.join(settings.ZDS_APP['tutorial']['repo_path'], chapter.part.tutorial.get_phy_slug()))
        ph = os.path.join(chapter.part.get_phy_slug(), chapter.get_phy_slug())
    index = repo.index
    if action == "del":
        shutil.rmtree(old_slug_path)
        msg = _(u"Suppresion du chapitre : «{}»").format(chapter.title)
    else:
        if action == "maj":
            if old_slug_path != new_slug_path:
                os.rename(old_slug_path, new_slug_path)
            if chapter.tutorial:
                msg = _(u"Modification du tutoriel «{}» "
                        u"{} {}").format(chapter.tutorial.title, get_sep(msg), get_text_is_empty(msg)).strip()
            else:
                msg = _(u"Modification du chapitre «{}» "
                        u"{} {}").format(chapter.title, get_sep(msg), get_text_is_empty(msg)).strip()
        elif action == "add":
            if not os.path.exists(new_slug_path):
                os.makedirs(new_slug_path, mode=0o777)
            msg = _(u"Création du chapitre «{}» {} {}").format(chapter.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()
        if introduction is not None:
            intro = open(os.path.join(new_slug_path, "introduction.md"), "w")
            intro.write(smart_str(introduction).strip())
            intro.close()
        if conclusion is not None:
            conclu = open(os.path.join(new_slug_path, "conclusion.md"), "w")
            conclu.write(smart_str(conclusion).strip())
            conclu.close()
        if ph is not None:
            index.add([ph])

    # update manifest

    if chapter.tutorial:
        man_path = os.path.join(chapter.tutorial.get_repo_path(), "manifest.json")
        chapter.tutorial.dump_json(path=man_path)
    else:
        man_path = os.path.join(chapter.part.tutorial.get_repo_path(),
                                "manifest.json")
        chapter.part.tutorial.dump_json(path=man_path)
    index.add(["manifest.json"])
    aut_user = str(request.user.pk)
    aut_email = str(request.user.email)
    if aut_email is None or aut_email.strip() == "":
        aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['dns'])
    com_ch = index.commit(
        msg,
        author=Actor(
            aut_user,
            aut_email),
        committer=Actor(
            aut_user,
            aut_email))
    if chapter.tutorial:
        chapter.tutorial.sha_draft = com_ch.hexsha
        chapter.tutorial.save()
    else:
        chapter.part.tutorial.sha_draft = com_ch.hexsha
        chapter.part.tutorial.save()
    chapter.save()


def maj_repo_extract(
    request,
    old_slug_path=None,
    new_slug_path=None,
    extract=None,
    text=None,
    action=None,
    msg=None,
):

    if extract.chapter.tutorial:
        repo = Repo(os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                 extract.chapter.tutorial.get_phy_slug()))
    else:
        repo = Repo(os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                 extract.chapter.part.tutorial.get_phy_slug()))
    index = repo.index

    chap = extract.chapter

    if action == "del":
        msg = _(u"Suppression de l'extrait : «{}»").format(extract.title)
        extract.delete()
        if old_slug_path:
            os.remove(old_slug_path)
    else:
        if action == "maj":
            if old_slug_path != new_slug_path:
                os.rename(old_slug_path, new_slug_path)
            msg = _(u"Mise à jour de l'extrait «{}» {} {}").format(extract.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()
        elif action == "add":
            msg = _(u"Création de l'extrait «{}» {} {}").format(extract.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()
        ext = open(new_slug_path, "w")
        ext.write(smart_str(text).strip())
        ext.close()
        index.add([extract.get_repo_path(relative=True)])

    # update manifest
    if chap.tutorial:
        man_path = os.path.join(chap.tutorial.get_repo_path(), "manifest.json")
        chap.tutorial.dump_json(path=man_path)
    else:
        man_path = os.path.join(chap.part.tutorial.get_repo_path(), "manifest.json")
        chap.part.tutorial.dump_json(path=man_path)

    index.add(["manifest.json"])
    aut_user = str(request.user.pk)
    aut_email = str(request.user.email)
    if aut_email is None or aut_email.strip() == "":
        aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['dns'])
    com_ex = index.commit(
        msg,
        author=Actor(
            aut_user,
            aut_email),
        committer=Actor(
            aut_user,
            aut_email))
    if chap.tutorial:
        chap.tutorial.sha_draft = com_ex.hexsha
        chap.tutorial.save()
    else:
        chap.part.tutorial.sha_draft = com_ex.hexsha
        chap.part.tutorial.save()


def insert_into_zip(zip_file, git_tree):
    """recursively add files from a git_tree to a zip archive"""
    for blob in git_tree.blobs:  # first, add files :
        zip_file.writestr(blob.path, blob.data_stream.read())
    if len(git_tree.trees) is not 0:  # then, recursively add dirs :
        for subtree in git_tree.trees:
            insert_into_zip(zip_file, subtree)


def download(request):
    """Download a tutorial."""
    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])

    repo_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], tutorial.get_phy_slug())
    repo = Repo(repo_path)
    sha = tutorial.sha_draft
    if 'online' in request.GET and tutorial.in_public():
        sha = tutorial.sha_public
    elif request.user not in tutorial.authors.all():
        if not request.user.has_perm('tutorial.change_tutorial'):
            raise PermissionDenied  # Only authors can download draft version
    zip_path = os.path.join(tempfile.gettempdir(), tutorial.slug + '.zip')
    zip_file = zipfile.ZipFile(zip_path, 'w')
    insert_into_zip(zip_file, repo.commit(sha).tree)
    zip_file.close()
    response = HttpResponse(open(zip_path, "rb").read(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename={0}.zip".format(tutorial.slug)
    os.remove(zip_path)
    return response


@permission_required("tutorial.change_tutorial", raise_exception=True)
def download_markdown(request):
    """Download a markdown tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".md")
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="application/txt")
    response["Content-Disposition"] = \
        "attachment; filename={0}.md".format(tutorial.slug)
    return response


def download_html(request):
    """Download a pdf tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".html")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="text/html")
    response["Content-Disposition"] = \
        "attachment; filename={0}.html".format(tutorial.slug)
    return response


def download_pdf(request):
    """Download a pdf tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".pdf")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="application/pdf")
    response["Content-Disposition"] = \
        "attachment; filename={0}.pdf".format(tutorial.slug)
    return response


def download_epub(request):
    """Download an epub tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".epub")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="application/epub")
    response["Content-Disposition"] = \
        "attachment; filename={0}.epub".format(tutorial.slug)
    return response


def get_url_images(md_text, pt):
    """find images urls in markdown text and download this."""

    regex = ur"(!\[.*?\]\()(.+?)(\))"
    unknow_path = os.path.join(settings.SITE_ROOT, "fixtures", "noir_black.png")

    # if text is empty don't download

    if md_text is not None:
        imgs = re.findall(regex, md_text)
        for img in imgs:
            real_url = img[1]
            # decompose images
            parse_object = urlparse(real_url)
            if parse_object.query != '':
                resp = parse_qs(urlparse(img[1]).query, keep_blank_values=True)
                real_url = resp["u"][0]
                parse_object = urlparse(real_url)

            # if link is http type
            if parse_object.scheme in ["http", "https", "ftp"] or \
                    parse_object.netloc[:3] == "www" or \
                    parse_object.path[:3] == "www":
                (filepath, filename) = os.path.split(parse_object.path)
                if not os.path.isdir(os.path.join(pt, "images")):
                    os.makedirs(os.path.join(pt, "images"))

                # download image
                down_path = os.path.abspath(os.path.join(pt, "images", filename))
                try:
                    urlretrieve(real_url, down_path)
                    try:
                        ext = filename.split(".")[-1]
                        im = ImagePIL.open(down_path)
                        # if image is gif, convert to png
                        if ext == "gif":
                            im.save(os.path.join(pt, "images", filename.split(".")[0] + ".png"))
                    except IOError:
                        ext = filename.split(".")[-1]
                        im = ImagePIL.open(unknow_path)
                        if ext == "gif":
                            im.save(os.path.join(pt, "images", filename.split(".")[0] + ".png"))
                        else:
                            im.save(os.path.join(pt, "images", filename))
                except IOError:
                    pass
            else:
                # relative link
                srcfile = settings.SITE_ROOT + real_url
                if os.path.isfile(srcfile):
                    dstroot = pt + real_url
                    dstdir = os.path.dirname(dstroot)
                    if not os.path.exists(dstdir):
                        os.makedirs(dstdir)
                    shutil.copy(srcfile, dstroot)

                    try:
                        ext = dstroot.split(".")[-1]
                        im = ImagePIL.open(dstroot)
                        # if image is gif, convert to png
                        if ext == "gif":
                            im.save(os.path.join(dstroot.split(".")[0] + ".png"))
                    except IOError:
                        ext = dstroot.split(".")[-1]
                        im = ImagePIL.open(unknow_path)
                        if ext == "gif":
                            im.save(os.path.join(dstroot.split(".")[0] + ".png"))
                        else:
                            im.save(os.path.join(dstroot))


def sub_urlimg(g):
    start = g.group("start")
    url = g.group("url")
    parse_object = urlparse(url)
    if parse_object.query != '':
        resp = parse_qs(urlparse(url).query, keep_blank_values=True)
        parse_object = urlparse(resp["u"][0])
    (filepath, filename) = os.path.split(parse_object.path)
    if filename != '':
        mark = g.group("mark")
        ext = filename.split(".")[-1]
        if ext == "gif":
            if parse_object.scheme in ("http", "https") or \
                    parse_object.netloc[:3] == "www" or \
                    parse_object.path[:3] == "www":
                url = os.path.join("images", filename.split(".")[0] + ".png")
            else:
                url = (url.split(".")[0])[1:] + ".png"
        else:
            if parse_object.scheme in ("http", "https") or \
                    parse_object.netloc[:3] == "www" or \
                    parse_object.path[:3] == "www":
                url = os.path.join("images", filename)
            else:
                url = url[1:]
        end = g.group("end")
        return start + mark + url + end
    else:
        return start


def markdown_to_out(md_text):
    return re.sub(ur"(?P<start>)(?P<mark>!\[.*?\]\()(?P<url>.+?)(?P<end>\))", sub_urlimg,
                  md_text)


def mep(tutorial, sha):
    (output, err) = (None, None)
    repo = Repo(tutorial.get_path())
    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    tutorial_version = json_reader.loads(manifest)

    prod_path = tutorial.get_prod_path(sha)

    pattern = os.path.join(settings.ZDS_APP['tutorial']['repo_public_path'], str(tutorial.pk) + '_*')
    del_paths = glob.glob(pattern)
    for del_path in del_paths:
        if os.path.isdir(del_path):
            try:
                shutil.rmtree(del_path)
            except OSError:
                shutil.rmtree(u"\\\\?\{0}".format(del_path))
                # WARNING: this can throw another OSError
    shutil.copytree(tutorial.get_path(), prod_path)
    repo.head.reset(commit=sha, index=True, working_tree=True)

    # collect md files

    fichiers = []
    fichiers.append(tutorial_version["introduction"])
    fichiers.append(tutorial_version["conclusion"])
    if "parts" in tutorial_version:
        for part in tutorial_version["parts"]:
            fichiers.append(part["introduction"])
            fichiers.append(part["conclusion"])
            if "chapters" in part:
                for chapter in part["chapters"]:
                    fichiers.append(chapter["introduction"])
                    fichiers.append(chapter["conclusion"])
                    if "extracts" in chapter:
                        for extract in chapter["extracts"]:
                            fichiers.append(extract["text"])
    if "chapter" in tutorial_version:
        chapter = tutorial_version["chapter"]
        if "extracts" in tutorial_version["chapter"]:
            for extract in chapter["extracts"]:
                fichiers.append(extract["text"])

    # convert markdown file to html file

    for fichier in fichiers:
        md_file_contenu = get_blob(repo.commit(sha).tree, fichier)

        # download images

        get_url_images(md_file_contenu, prod_path)

        # convert to out format
        out_file = open(os.path.join(prod_path, fichier), "w")
        if md_file_contenu is not None:
            out_file.write(markdown_to_out(md_file_contenu.encode("utf-8")))
        out_file.close()
        target = os.path.join(prod_path, fichier + ".html")
        os.chdir(os.path.dirname(target))
        try:
            html_file = open(target, "w")
        except IOError:

            # handle limit of 255 on windows

            target = u"\\\\?\{0}".format(target)
            html_file = open(target, "w")
        if tutorial.js_support:
            is_js = "js"
        else:
            is_js = ""
        if md_file_contenu is not None:
            html_file.write(emarkdown(md_file_contenu, is_js))
        html_file.close()

    # load markdown out

    contenu = export_tutorial_to_md(tutorial, sha).lstrip()
    out_file = open(os.path.join(prod_path, tutorial.slug + ".md"), "w")
    out_file.write(smart_str(contenu))
    out_file.close()

    # define whether to log pandoc's errors

    pandoc_debug_str = ""
    if settings.PANDOC_LOG_STATE:
        pandoc_debug_str = " 2>&1 | tee -a " + settings.PANDOC_LOG

    # load pandoc

    os.chdir(prod_path)
    os.system(settings.PANDOC_LOC
              + "pandoc --latex-engine=xelatex -s -S --toc "
              + os.path.join(prod_path, tutorial.slug)
              + ".md -o " + os.path.join(prod_path,
                                         tutorial.slug) + ".html" + pandoc_debug_str)
    os.system(settings.PANDOC_LOC + "pandoc " + settings.PANDOC_PDF_PARAM + " "
              + os.path.join(prod_path, tutorial.slug) + ".md "
              + "-o " + os.path.join(prod_path, tutorial.slug)
              + ".pdf" + pandoc_debug_str)
    os.system(settings.PANDOC_LOC + "pandoc -s -S --toc "
              + os.path.join(prod_path, tutorial.slug)
              + ".md -o " + os.path.join(prod_path,
                                         tutorial.slug) + ".epub" + pandoc_debug_str)
    os.chdir(settings.SITE_ROOT)
    return (output, err)


def un_mep(tutorial):
    del_paths = glob.glob(os.path.join(settings.ZDS_APP['tutorial']['repo_public_path'],
                          str(tutorial.pk) + '_*'))
    for del_path in del_paths:
        if os.path.isdir(del_path):
            try:
                shutil.rmtree(del_path)
            except OSError:
                shutil.rmtree(u"\\\\?\{0}".format(del_path))
                # WARNING: this can throw another OSError


@can_write_and_read_now
@login_required
def answer(request):
    """Adds an answer from a user to an tutorial."""

    try:
        tutorial_pk = request.GET["tutorial"]
    except KeyError:
        raise Http404

    # Retrieve current tutorial.

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    # Making sure reactioning is allowed

    if tutorial.is_locked:
        raise PermissionDenied

    # Check that the user isn't spamming

    if tutorial.antispam(request.user):
        raise PermissionDenied

    # Retrieve 3 last notes of the current tutorial.

    notes = ContentReaction.objects.filter(tutorial=tutorial).order_by("-pubdate")[:3]

    # If there is a last notes for the tutorial, we save his pk. Otherwise, we
    # save 0.

    last_note_pk = 0
    if tutorial.last_note:
        last_note_pk = tutorial.last_note.pk

    # Retrieve lasts notes of the current tutorial.
    notes = ContentReaction.objects.filter(tutorial=tutorial) \
        .prefetch_related() \
        .order_by("-pubdate")[:settings.ZDS_APP['forum']['posts_per_page']]

    # User would like preview his post or post a new note on the tutorial.

    if request.method == "POST":
        data = request.POST
        newnote = last_note_pk != int(data["last_note"])

        # Using the « preview button », the « more » button or new note

        if "preview" in data or newnote:
            form = NoteForm(tutorial, request.user,
                            initial={"text": data["text"]})
            if request.is_ajax():
                return HttpResponse(json.dumps({"text": emarkdown(data["text"])}),
                                    content_type='application/json')
            else:
                return render(request, "tutorial/comment/new.html", {
                    "tutorial": tutorial,
                    "last_note_pk": last_note_pk,
                    "newnote": newnote,
                    "notes": notes,
                    "form": form,
                })
        else:

            # Saving the message

            form = NoteForm(tutorial, request.user, request.POST)
            if form.is_valid():
                data = form.data
                note = ContentReaction()
                note.related_content = tutorial
                note.author = request.user
                note.text = data["text"]
                note.text_html = emarkdown(data["text"])
                note.pubdate = datetime.now()
                note.position = tutorial.get_note_count() + 1
                note.ip_address = get_client_ip(request)
                note.save()
                tutorial.last_note = note
                tutorial.save()
                return redirect(note.get_absolute_url())
            else:
                return render(request, "tutorial/comment/new.html", {
                    "tutorial": tutorial,
                    "last_note_pk": last_note_pk,
                    "newnote": newnote,
                    "notes": notes,
                    "form": form,
                })
    else:

        # Actions from the editor render to answer.html.
        text = ""

        # Using the quote button

        if "cite" in request.GET:
            note_cite_pk = request.GET["cite"]
            note_cite = ContentReaction.objects.get(pk=note_cite_pk)
            if not note_cite.is_visible:
                raise PermissionDenied

            for line in note_cite.text.splitlines():
                text = text + "> " + line + "\n"

            text = u'{0}Source:[{1}]({2}{3})'.format(
                text,
                note_cite.author.username,
                settings.ZDS_APP['site']['url'],
                note_cite.get_absolute_url())

        form = NoteForm(tutorial, request.user, initial={"text": text})
        return render(request, "tutorial/comment/new.html", {
            "tutorial": tutorial,
            "notes": notes,
            "last_note_pk": last_note_pk,
            "form": form,
        })


@can_write_and_read_now
@login_required
@require_POST
@transaction.atomic
def solve_alert(request):

    # only staff can move topic

    if not request.user.has_perm("tutorial.change_note"):
        raise PermissionDenied

    alert = get_object_or_404(Alert, pk=request.POST["alert_pk"])
    note = ContentReaction.objects.get(pk=alert.comment.id)

    if "text" in request.POST and request.POST["text"] != "":
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        msg = \
            (_(u'Bonjour {0},'
               u'Vous recevez ce message car vous avez signalé le message de *{1}*, '
               u'dans le tutoriel [{2}]({3}). Votre alerte a été traitée par **{4}** '
               u'et il vous a laissé le message suivant :'
               u'\n\n> {5}\n\nToute l\'équipe de la modération vous remercie !').format(
                   alert.author.username,
                   note.author.username,
                   note.tutorial.title,
                   settings.ZDS_APP['site']['url'] + note.get_absolute_url(),
                   request.user.username,
                   request.POST["text"],))
        send_mp(
            bot,
            [alert.author],
            _(u"Résolution d'alerte : {0}").format(note.tutorial.title),
            "",
            msg,
            False,
        )
    alert.delete()
    messages.success(request, _(u"L'alerte a bien été résolue."))
    return redirect(note.get_absolute_url())


@login_required
@require_POST
def activ_js(request):

    # only for staff

    if not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    tutorial = get_object_or_404(PublishableContent, pk=request.POST["tutorial"])
    tutorial.js_support = "js_support" in request.POST
    tutorial.save()

    return redirect(tutorial.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_note(request):
    """Edit the given user's note."""

    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    note = get_object_or_404(ContentReaction, pk=note_pk)
    g_tutorial = None
    if note.position >= 1:
        g_tutorial = get_object_or_404(PublishableContent, pk=note.related_content.pk)

    # Making sure the user is allowed to do that. Author of the note must to be
    # the user logged.

    if note.author != request.user \
            and not request.user.has_perm("tutorial.change_note") \
            and "signal_message" not in request.POST:
        raise PermissionDenied
    if note.author != request.user and request.method == "GET" \
            and request.user.has_perm("tutorial.change_note"):
        messages.add_message(request, messages.WARNING,
                             _(u'Vous éditez ce message en tant que '
                               u'modérateur (auteur : {}). Soyez encore plus '
                               u'prudent lors de l\'édition de '
                               u'celui-ci !').format(note.author.username))
        note.alerts.all().delete()
    if request.method == "POST":
        if "delete_message" in request.POST:
            if note.author == request.user \
                    or request.user.has_perm("tutorial.change_note"):
                note.alerts.all().delete()
                note.is_visible = False
                if request.user.has_perm("tutorial.change_note"):
                    note.text_hidden = request.POST["text_hidden"]
                note.editor = request.user
        if "show_message" in request.POST:
            if request.user.has_perm("tutorial.change_note"):
                note.is_visible = True
                note.text_hidden = ""
        if "signal_message" in request.POST:
            alert = Alert()
            alert.author = request.user
            alert.comment = note
            alert.scope = Alert.TUTORIAL
            alert.text = request.POST["signal_text"]
            alert.pubdate = datetime.now()
            alert.save()

        # Using the preview button
        if "preview" in request.POST:
            form = NoteForm(g_tutorial, request.user,
                            initial={"text": request.POST["text"]})
            form.helper.form_action = reverse("zds.tutorial.views.edit_note") \
                + "?message=" + str(note_pk)
            if request.is_ajax():
                return HttpResponse(json.dumps({"text": emarkdown(request.POST["text"])}),
                                    content_type='application/json')
            else:
                return render(request,
                              "tutorial/comment/edit.html",
                              {"note": note, "tutorial": g_tutorial, "form": form})
        if "delete_message" not in request.POST and "signal_message" \
                not in request.POST and "show_message" not in request.POST:

            # The user just sent data, handle them

            if request.POST["text"].strip() != "":
                note.text = request.POST["text"]
                note.text_html = emarkdown(request.POST["text"])
                note.update = datetime.now()
                note.editor = request.user
        note.save()
        return redirect(note.get_absolute_url())
    else:
        form = NoteForm(g_tutorial, request.user, initial={"text": note.text})
        form.helper.form_action = reverse("zds.tutorial.views.edit_note") \
            + "?message=" + str(note_pk)
        return render(request, "tutorial/comment/edit.html", {"note": note, "tutorial": g_tutorial, "form": form})


@can_write_and_read_now
@login_required
def like_note(request):
    """Like a note."""
    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    resp = {}
    note = get_object_or_404(ContentReaction, pk=note_pk)

    user = request.user
    if note.author.pk != request.user.pk:

        # Making sure the user is allowed to do that

        if CommentLike.objects.filter(user__pk=user.pk,
                                      comments__pk=note_pk).count() == 0:
            like = CommentLike()
            like.user = user
            like.comments = note
            note.like = note.like + 1
            note.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk,
                                             comments__pk=note_pk).count() > 0:
                CommentDislike.objects.filter(
                    user__pk=user.pk,
                    comments__pk=note_pk).all().delete()
                note.dislike = note.dislike - 1
                note.save()
        else:
            CommentLike.objects.filter(user__pk=user.pk,
                                       comments__pk=note_pk).all().delete()
            note.like = note.like - 1
            note.save()
    resp["upvotes"] = note.like
    resp["downvotes"] = note.dislike
    if request.is_ajax():
        return HttpResponse(json_writer.dumps(resp))
    else:
        return redirect(note.get_absolute_url())


@can_write_and_read_now
@login_required
def dislike_note(request):
    """Dislike a note."""

    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    resp = {}
    note = get_object_or_404(ContentReaction, pk=note_pk)
    user = request.user
    if note.author.pk != request.user.pk:

        # Making sure the user is allowed to do that

        if CommentDislike.objects.filter(user__pk=user.pk,
                                         comments__pk=note_pk).count() == 0:
            dislike = CommentDislike()
            dislike.user = user
            dislike.comments = note
            note.dislike = note.dislike + 1
            note.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk,
                                          comments__pk=note_pk).count() > 0:
                CommentLike.objects.filter(user__pk=user.pk,
                                           comments__pk=note_pk).all().delete()
                note.like = note.like - 1
                note.save()
        else:
            CommentDislike.objects.filter(user__pk=user.pk,
                                          comments__pk=note_pk).all().delete()
            note.dislike = note.dislike - 1
            note.save()
    resp["upvotes"] = note.like
    resp["downvotes"] = note.dislike
    if request.is_ajax():
        return HttpResponse(json_writer.dumps(resp))
    else:
        return redirect(note.get_absolute_url())
