# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import datetime
from operator import attrgetter
from urllib import urlretrieve
from urlparse import urlparse
try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

import json as json_writer
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

from zds.tutorial.forms import TutorialForm, PartForm, ChapterForm, EmbdedChapterForm, \
    ExtractForm, ImportForm, NoteForm, AskValidationForm, ValidForm, RejectForm
from zds.tutorial.models import Tutorial, Part, Chapter, Extract, Validation, never_read, \
    mark_read, Note
from zds.tutorial.views.versionning import maj_repo
from zds.gallery.models import Gallery, UserGallery, Image
from zds.member.decorator import can_write_and_read_now
from zds.member.models import get_info_old_tuto, Profile
from zds.member.views import get_client_ip
from zds.utils import render_template
from zds.utils import slugify
from zds.utils.models import Alert
from zds.utils.models import Category, Licence, CommentLike, CommentDislike, \
    SubCategory
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move, load_data_part,\
load_data_chapter, load_data_extract
from zds.utils.misc import compute_hash, content_has_changed

@login_required
def add_extract(request):
    """Add extract."""

    try:
        chapter_pk = int(request.GET["chapitre"])
    except KeyError:
        raise Http404
    chapter = get_object_or_404(Chapter, pk=chapter_pk)
    part = chapter.part
    tutorial=chapter.get_tutorial()

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
                                        "text": data["text"]})
            return render_template("tutorial/extract/new.html",
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
                maj_repo(user=request.user,
                         new_slug_path=extract.get_path(),
                         obj=extract,
                         tutorial=tutorial,
                         contents=[(extract.get_path(relative=True), data["text"])],
                         action="add")
                return redirect(extract.get_absolute_url())
    else:
        form = ExtractForm()

    return render_template("tutorial/extract/new.html", {"chapter": chapter,
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
    tutorial = extract.chapter.get_tutorial()
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
                                           "text": data["text"]
                                       })
            return render_template("tutorial/extract/edit.html",
                                   {
                                       "extract": extract, "form": form,
                                       "last_hash": compute_hash([extract.get_path()])
                                   })
        else:
            if content_has_changed([extract.get_path()], data["last_hash"]):
                form = ExtractForm(initial={
                    "title": extract.title,
                    "text": extract.get_text()})
                return render_template("tutorial/extract/edit.html", 
                    {
                         "extract": extract,
                         "last_hash": compute_hash([extract.get_path()]),
                         "new_version":True,
                         "form": form
                    })
            # Edit extract.

            form = ExtractForm(request.POST)
            if form.is_valid():
                data = form.data
                old_slug = extract.get_path()
                extract.title = data["title"]
                extract.text = extract.get_path(relative=True)

                # Get path for mini-tuto

                if extract.chapter.tutorial:
                    chapter_tutorial_path = os.path.join(settings.REPO_PATH, extract.chapter.tutorial.get_phy_slug())
                    chapter_part = os.path.join(chapter_tutorial_path)
                else:

                    # Get path for big-tuto

                    chapter_part_tutorial_path = \
                        os.path.join(settings.REPO_PATH, extract.chapter.part.tutorial.get_phy_slug())
                    chapter_part_path = os.path.join(chapter_part_tutorial_path, extract.chapter.part.get_phy_slug())
                    chapter_part = os.path.join(chapter_part_path, extract.chapter.get_phy_slug())

                # Use path retrieve before and use it to create the new slug.
                extract.save()
                new_slug = extract.get_path()
                
                maj_repo(
                         user=request.user,
                         old_slug_path=old_slug,
                         new_slug_path=new_slug,
                         obj=extract,
                         tutorial=tutorial,
                         contents=[(extract.get_path(relative=True), data["text"])],
                         action="maj",
                )
                return redirect(extract.get_absolute_url())
    else:
        form = ExtractForm({"title": extract.title,
                            "text": extract.get_text()})
    return render_template("tutorial/extract/edit.html", 
        {
            "extract": extract,
            "last_hash": compute_hash([extract.get_path()]),
            "form": form
        })


@can_write_and_read_now
@require_POST
def modify_extract(request):
    data = request.POST
    try:
        extract_pk = data["extract"]
    except KeyError:
        raise Http404
    extract = get_object_or_404(Extract, pk=extract_pk)
    chapter = extract.chapter
    tutorial = chapter.get_tutorial()
    if "delete" in data:
        pos_current_extract = extract.position_in_chapter
        for extract_c in extract.chapter.get_extracts():
            if pos_current_extract <= extract_c.position_in_chapter:
                extract_c.position_in_chapter = extract_c.position_in_chapter \
                    - 1
                extract_c.save()
        # Use path retrieve before and use it to create the new slug.

        old_slug = extract.get_path()
        maj_repo(user=request.user,
                 old_slug_path=old_slug,
                 obj=extract,
                 tutorial=tutorial,
                 action="del")
        extract.delete()

        new_slug_path_chapter = chapter.get_path()
        maj_repo(user=request.user,
                 old_slug_path = new_slug_path_chapter,
                 new_slug_path = new_slug_path_chapter,
                 obj = chapter,
                 tutorial=tutorial,
                 action = "maj")
        return redirect(chapter.get_absolute_url())
    elif "move" in data:
        try:
            new_pos = int(request.POST["move_target"])
        except ValueError:
            # Error, the user misplayed with the move button
            return redirect(extract.get_absolute_url())
        
        move(extract, new_pos, "position_in_chapter", "chapter", "get_extracts")
        extract.save()
        new_slug_path = extract.get_path()

        maj_repo(user=request.user,
                 old_slug_path = new_slug_path,
                 new_slug_path = new_slug_path,
                 obj = chapter,
                 tutorial=tutorial,
                 action = "maj")
        return redirect(extract.get_absolute_url())
    raise Http404