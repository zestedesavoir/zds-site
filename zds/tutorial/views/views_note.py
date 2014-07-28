# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import datetime
from operator import attrgetter
from urllib import urlretrieve
from urlparse import urlparse
import os.path
import re
import shutil
import zipfile

from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str
from django.views.decorators.http import require_POST
from git import *
from lxml import etree

from zds.gallery.models import Gallery, UserGallery, Image
from zds.member.decorator import can_write_and_read_now
from zds.member.models import get_info_old_tuto, Profile
from zds.member.views import get_client_ip
from zds.tutorial.forms import TutorialForm, PartForm, ChapterForm, EmbdedChapterForm, \
    ExtractForm, ImportForm, NoteForm, AskValidationForm, ValidForm, RejectForm
from zds.tutorial.models import Tutorial, Part, Chapter, Extract, Validation, never_read, \
    mark_read, Note
from zds.utils import render_template
from zds.utils import slugify
from zds.utils.misc import compute_hash, content_has_changed
from zds.utils.models import Alert
from zds.utils.models import Category, Licence, CommentLike, CommentDislike, \
    SubCategory
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move
import json as json_writer


try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader




@can_write_and_read_now
@login_required
def answer(request):
    """Adds an answer from a user to an tutorial."""

    try:
        tutorial_pk = request.GET["tutorial"]
    except KeyError:
        raise Http404

    # Retrieve current tutorial.

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # Making sure reactioning is allowed

    if tutorial.is_locked:
        raise PermissionDenied

    # Check that the user isn't spamming

    if tutorial.antispam(request.user):
        raise PermissionDenied

    # Retrieve 3 last notes of the current tutorial.

    notes = Note.objects.filter(tutorial=tutorial).order_by("-pubdate")[:3]

    # If there is a last notes for the tutorial, we save his pk. Otherwise, we
    # save 0.

    last_note_pk = 0
    if tutorial.last_note:
        last_note_pk = tutorial.last_note.pk

    # User would like preview his post or post a new note on the tutorial.

    if request.method == "POST":
        data = request.POST
        newnote = last_note_pk != int(data["last_note"])

        # Using the « preview button », the « more » button or new note

        if "preview" in data or newnote:
            form = NoteForm(tutorial, request.user,
                            initial={"text": data["text"]})
            return render_template("tutorial/comment/new.html", {
                "tutorial": tutorial,
                "last_note_pk": last_note_pk,
                "newnote": newnote,
                "form": form,
            })
        else:

            # Saving the message

            form = NoteForm(tutorial, request.user, request.POST)
            if form.is_valid():
                data = form.data
                note = Note()
                note.tutorial = tutorial
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
                return render_template("tutorial/comment/new.html", {
                    "tutorial": tutorial,
                    "last_note_pk": last_note_pk,
                    "newnote": newnote,
                    "form": form,
                })
    else:

        # Actions from the editor render to answer.html.

        text = ""

        # Using the quote button

        if "cite" in request.GET:
            note_cite_pk = request.GET["cite"]
            note_cite = Note.objects.get(pk=note_cite_pk)
            if not note_cite.is_visible:
                raise PermissionDenied
            for line in note_cite.text.splitlines():
                text = text + "> " + line + "\n"
            text = u"{0}Source:[{1}]({2})".format(
                text,
                note_cite.author.username,
                note_cite.get_absolute_url())
        form = NoteForm(tutorial, request.user, initial={"text": text})
        return render_template("tutorial/comment/new.html", {
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
    note = Note.objects.get(pk=alert.comment.id)
    bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
    msg = \
        (u'Bonjour {0},'
        u'Vous recevez ce message car vous avez signalé le message de *{1}*, '
        u'dans le tutoriel [{2}]({3}). Votre alerte a été traitée par **{4}** '
        u'et il vous a laissé le message suivant :'
        u'\n\n> {5}\n\nToute l\'équipe de la modération vous remercie !'.format(
            alert.author.username,
            note.author.username,
            note.tutorial.title,
            settings.SITE_URL + note.get_absolute_url(),
            request.user.username,
            request.POST["text"],))
    send_mp(
        bot,
        [alert.author],
        u"Résolution d'alerte : {0}".format(note.tutorial.title),
        "",
        msg,
        False,
    )
    alert.delete()
    messages.success(request, u"L'alerte a bien été résolue")
    return redirect(note.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_note(request):
    """Edit the given user's note."""

    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    note = get_object_or_404(Note, pk=note_pk)
    g_tutorial = None
    if note.position >= 1:
        g_tutorial = get_object_or_404(Tutorial, pk=note.tutorial.pk)

    # Making sure the user is allowed to do that. Author of the note must to be
    # the user logged.

    if note.author != request.user \
            and not request.user.has_perm("tutorial.change_note") \
            and "signal_message" not in request.POST:
        raise PermissionDenied
    if note.author != request.user and request.method == "GET" \
            and request.user.has_perm("tutorial.change_note"):
        messages.add_message(request, messages.WARNING,
                             u'Vous \xe9ditez ce message en tant que '
                             u'mod\xe9rateur (auteur : {}). Soyez encore plus '
                             u'prudent lors de l\'\xe9dition de '
                             u'celui-ci !'.format(note.author.username))
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
            return render_template(
                "tutorial/comment/edit.html", {"note": note, "tutorial": g_tutorial, "form": form})
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
        return render_template(
            "tutorial/comment/edit.html", {"note": note, "tutorial": g_tutorial, "form": form})


@can_write_and_read_now
@login_required
def like_note(request):
    """Like a note."""
    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    resp = {}
    note = get_object_or_404(Note, pk=note_pk)

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
    note = get_object_or_404(Note, pk=note_pk)
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
