#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import datetime
from operator import attrgetter
from urllib import urlretrieve
from urlparse import urlparse, parse_qs
from django.contrib.humanize.templatetags.humanize import naturaltime
from zds.forum.models import Forum, Topic
from zds.tutorialv2.forms import BetaForm
from zds.utils.forums import send_post, unlock_topic, create_topic

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
from git import Repo

from forms import ContentForm, ContainerForm, \
    ExtractForm, NoteForm, AskValidationForm, ValidForm, RejectForm, ActivJsForm
from models import PublishableContent, Container, Extract, Validation, ContentReaction, init_new_repo
from utils import never_read, mark_read, search_container_or_404
from zds.gallery.models import Gallery, UserGallery, Image
from zds.member.decorator import can_write_and_read_now
from zds.member.views import get_client_ip
from zds.utils import slugify
from zds.utils.models import Alert
from zds.utils.models import Category, CommentLike, CommentDislike, \
    SubCategory, HelpWriting
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md
from django.utils.translation import ugettext as _
from django.views.generic import ListView, DetailView, FormView, DeleteView


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
        return reverse('content:view', args=[self.content.pk, self.content.slug])


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
        query_set = PublishableContent.objects\
            .select_related("licence")\
            .prefetch_related("authors")\
            .prefetch_related("subcategory")\
            .filter(pk=self.kwargs["pk"])

        obj = query_set.first()
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
        can_edit = self.request.user in content.authors.all()
        if self.request.user not in content.authors.all() and not is_beta:
            # if we are not author of this content or if we did not ask for beta
            # the only members that can display and modify the tutorial are validators
            if not self.request.user.has_perm("tutorial.change_tutorial"):
                raise PermissionDenied
            else:
                can_edit = True

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
        context["can_edit"] = can_edit
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


class CreateContainer(FormView):
    template_name = 'tutorialv2/create/container.html'
    form_class = ContainerForm
    content = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(CreateContainer, self).dispatch(*args, **kwargs)

    def get_object(self):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        self.content = self.get_object()
        context = super(CreateContainer, self).get_context_data(**kwargs)
        context['content'] = self.content.load_version()

        # get the container:
        if 'container_slug' in self.kwargs:
            try:
                container = context['content'].children_dict[self.kwargs['container_slug']]
            except KeyError:
                raise Http404
            else:
                if not isinstance(container, Container):
                    raise Http404
                context['container'] = container
        else:
            context['container'] = context['content']
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        parent = context['container']

        sha = parent.repo_add_container(form.cleaned_data['title'],
                                        form.cleaned_data['introduction'],
                                        form.cleaned_data['conclusion'],
                                        form.cleaned_data['msg_commit'])

        # then save
        self.content.sha_draft = sha
        self.content.update_date = datetime.now()
        self.content.save()

        self.success_url = parent.get_absolute_url()

        return super(CreateContainer, self).form_valid(form)


class DisplayContainer(DetailView):
    """Base class that can show any content in any state"""

    model = PublishableContent
    template_name = 'tutorialv2/view/container.html'
    online = False
    sha = None

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DisplayContainer, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""

        context = super(DisplayContainer, self).get_context_data(**kwargs)
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
        context['content'] = content.load_version(sha)
        container = context['content']

        context['container'] = search_container_or_404(container, self.kwargs)

        return context


class EditContainer(FormView):
    template_name = 'tutorialv2/edit/container.html'
    form_class = ContainerForm
    content = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(EditContainer, self).dispatch(*args, **kwargs)

    def get_object(self):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        self.content = self.get_object()
        context = super(EditContainer, self).get_context_data(**kwargs)
        context['content'] = self.content.load_version()
        container = context['content']

        # get the container:
        container = search_container_or_404(container, self.kwargs)

        context['container'] = container

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        context = self.get_context_data()
        container = context['container']
        initial = super(EditContainer, self).get_initial()

        initial['title'] = container.title
        initial['introduction'] = container.get_introduction()
        initial['conclusion'] = container.get_conclusion()

        return initial

    def form_valid(self, form):
        context = self.get_context_data()
        container = context['container']

        sha = container.repo_update(form.cleaned_data['title'],
                                    form.cleaned_data['introduction'],
                                    form.cleaned_data['conclusion'],
                                    form.cleaned_data['msg_commit'])

        # then save
        self.content.sha_draft = sha
        self.content.update_date = datetime.now()
        self.content.save()

        self.success_url = container.get_absolute_url()

        return super(EditContainer, self).form_valid(form)


class CreateExtract(FormView):
    template_name = 'tutorialv2/create/extract.html'
    form_class = ExtractForm
    content = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(CreateExtract, self).dispatch(*args, **kwargs)

    def get_object(self):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        self.content = self.get_object()
        context = super(CreateExtract, self).get_context_data(**kwargs)
        context['content'] = self.content.load_version()
        container = context['content']

        context['container'] = search_container_or_404(container, self.kwargs)

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        parent = context['container']

        sha = parent.repo_add_extract(form.cleaned_data['title'],
                                      form.cleaned_data['text'],
                                      form.cleaned_data['msg_commit'])

        # then save
        self.content.sha_draft = sha
        self.content.update_date = datetime.now()
        self.content.save()

        self.success_url = parent.get_absolute_url()

        return super(CreateExtract, self).form_valid(form)


class EditExtract(FormView):
    template_name = 'tutorialv2/edit/extract.html'
    form_class = ExtractForm
    content = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(EditExtract, self).dispatch(*args, **kwargs)

    def get_object(self):
        """get the PublishableContent object that the user asked. We double check pk and slug"""
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        self.content = self.get_object()
        context = super(EditExtract, self).get_context_data(**kwargs)
        context['content'] = self.content.load_version()
        container = context['content']

        # if the extract is at a depth of 3 we get the first parent container
        container = search_container_or_404(container, self.kwargs)

        extract = None
        if 'extract_slug' in self.kwargs:
            try:
                extract = container.children_dict[self.kwargs['extract_slug']]
            except KeyError:
                raise Http404
            else:
                if not isinstance(extract, Extract):
                    raise Http404

        context['extract'] = extract

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        context = self.get_context_data()
        extract = context['extract']
        initial = super(EditExtract, self).get_initial()

        initial['title'] = extract.title
        initial['text'] = extract.get_text()

        return initial

    def form_valid(self, form):
        context = self.get_context_data()
        extract = context['extract']

        sha = extract.repo_update(form.cleaned_data['title'],
                                  form.cleaned_data['text'],
                                  form.cleaned_data['msg_commit'])

        # then save
        self.content.sha_draft = sha
        self.content.update_date = datetime.now()
        self.content.save()

        self.success_url = extract.get_absolute_url()

        return super(EditExtract, self).form_valid(form)


class DeleteContainerOrExtract(DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = [u'delete', u'post']
    object = None
    content = None

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(DeleteContainerOrExtract, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        self.content = self.get_object()
        context = super(DeleteContainerOrExtract, self).get_context_data(**kwargs)
        context['content'] = self.content.load_version()
        container = context['content']

        container = search_container_or_404(container, self.kwargs)

        to_delete = None
        if 'object_slug' in self.kwargs:
            try:
                to_delete = container.children_dict[self.kwargs['object_slug']]
            except KeyError:
                raise Http404

        context['to_delete'] = to_delete

        return context

    def delete(self, request, *args, **kwargs):
        """delete any object, either Extract or Container"""

        context = self.get_context_data()
        to_delete = context['to_delete']

        sha = to_delete.repo_delete()

        # then save
        self.content.sha_draft = sha
        self.content.update_date = datetime.now()
        self.content.save()

        success_url = ''
        if isinstance(to_delete, Extract):
            success_url = to_delete.container.get_absolute_url()
        else:
            success_url = to_delete.parent.get_absolute_url()

        return redirect(success_url)


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


class DisplayHistory(DetailView):
    """Display the whole modification history.
    this class has no reason to be adapted to any content type"""
    model = PublishableContent
    template_name = "tutorialv2/view/history.html"
    context_object_name = "object"

    def get_object(self, queryset=None):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if self.request.user not in obj.authors.all():
            raise Http404
        return obj

    def get_context_data(self, **kwargs):

        context = super(DisplayHistory, self).get_context_data(**kwargs)
        repo = Repo(context['object'].get_repo_path())
        logs = repo.head.reference.log()
        logs = sorted(logs, key=attrgetter("time"), reverse=True)
        context['logs'] = logs
        context['content'] = context['object'].load_version()
        return context


class DisplayDiff(DetailView):
    """Display the difference between two version of a content.
    Reference is always HEAD and compared version is a GET query parameter named sha
    this class has no reason to be adapted to any content type"""
    model = PublishableContent
    template_name = "tutorialv2/diff.html"
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


class PutContentOnBeta(FormView):
    model = PublishableContent
    content = None
    form_class = BetaForm

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        """rewrite this method to ensure decoration"""
        return super(PutContentOnBeta, self).dispatch(*args, **kwargs)

    def get_object(self):
        obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if obj.slug != self.kwargs['slug']:
            raise Http404
        if self.request.user not in obj.authors.all():
            # Todo: find how to throw http 403
            raise Http404
        return obj

    def form_valid(self, form):

        self.content = self.get_object()
        try:
            self.content.load_version(self.request.POST['version'])

            self.content.sha_beta = self.request.POST['version']
            self.content.save()
        except Exception:
            # exception are raised if :
            #     - we have a false version number
            #     - we have a not supported manfile
            pass
        topic = Topic.objects.filter(key=self.content.pk, forum__pk=settings.ZDS_APP['forum']['beta_forum_id']).first()
        msg = \
            (_(u'Bonjour à tous,\n\n'
               u'J\'ai commencé ({0}) la rédaction d\'un tutoriel dont l\'intitulé est **{1}**.\n\n'
               u'J\'aimerais obtenir un maximum de retour sur celui-ci, sur le fond ainsi que '
               u'sur la forme, afin de proposer en validation un texte de qualité.'
               u'\n\nSi vous êtes intéressé, cliquez ci-dessous '
               u'\n\n-> [Lien de la beta du tutoriel : {1}]({2}) <-\n\n'
               u'\n\nMerci d\'avance pour votre aide').format(
                   naturaltime(self.content.creation_date),
                   self.content.title,
                   settings.ZDS_APP['site']['url'] +
                   reverse("content:view", args=[self.content.pk, self.content.slug])))
        if topic is None:
            forum = get_object_or_404(Forum, pk=settings.ZDS_APP['forum']['beta_forum_id'])

            create_topic(author=self.request.user,
                         forum=forum,
                         title=_(u"[beta][tutoriel]{0}").format(self.content.title),
                         subtitle=u"{}".format(self.content.description),
                         text=msg,
                         key=self.content.pk
                         )
            tp = Topic.objects.get(key=self.content.pk)
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            private_mp = \
                (_(u'Bonjour {},\n\n'
                   u'Vous venez de mettre votre tutoriel **{}** en beta. La communauté '
                   u'pourra le consulter afin de vous faire des retours '
                   u'constructifs avant sa soumission en validation.\n\n'
                   u'Un sujet dédié pour la beta de votre tutoriel a été '
                   u'crée dans le forum et est accessible [ici]({})').format(
                       self.request.user.username,
                       self.content.title,
                       settings.ZDS_APP['site']['url'] + tp.get_absolute_url()))
            send_mp(
                bot,
                [self.request.user],
                _(u"Tutoriel en beta : {0}").format(self.content.title),
                "",
                private_mp,
                False,
            )
        else:
            msg_up = \
                (_(u'Bonjour,\n\n'
                   u'La beta du {2} est de nouveau active.'
                   u'\n\n-> [Lien de la beta du tutoriel : {0}]({1}) <-\n\n'
                   u'\n\nMerci pour vos relectures').format(self.content.title,
                                                            settings.ZDS_APP['site']['url']
                                                            + reverse("content:view",
                                                                      args=[self.content.pk,
                                                                            self.content.slug]),
                                                            self.content.type))
            unlock_topic(topic, msg)
            send_post(topic, msg_up)
        self.content.save()
        return super(PutContentOnBeta, self).form_valid(form)

    def get_success_url(self):
        return reverse('content:view', args=[self.content.pk, self.content.slug])

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
