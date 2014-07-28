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

from zds.tutorial.views.versionning import maj_repo
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
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move, load_data_part,\
load_data_chapter, load_data_extract


try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

def render_chapter_form(chapter):
    if chapter.part:
        return ChapterForm({"title": chapter.title,
                            "introduction": chapter.get_introduction(),
                            "conclusion": chapter.get_conclusion()})
    else:

        return EmbdedChapterForm({"introduction": chapter.get_introduction(),
                               "conclusion": chapter.get_conclusion()})

@can_write_and_read_now
@login_required
def add_chapter(request):
    """Add a new chapter to given part."""

    try:
        part_pk = request.GET["partie"]
    except KeyError:
        raise Http404
    part = get_object_or_404(Part, pk=part_pk)

    # Make sure the user is allowed to do that

    if request.user not in part.tutorial.authors.all() and not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    if request.method == "POST":
        form = ChapterForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data
            chapter = Chapter()
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
            chapter_path = os.path.join(settings.REPO_PATH, 
                                        chapter.part.tutorial.get_phy_slug(),
                                        chapter.part.get_phy_slug(), 
                                        chapter.get_phy_slug())
            chapter.introduction = os.path.join(chapter.part.get_phy_slug(),chapter.get_phy_slug(),"introduction.md")
            chapter.conclusion = os.path.join(chapter.part.get_phy_slug(),chapter.get_phy_slug(),"conclusion.md")
            chapter.save()
            maj_repo(
                user = request.user,
                new_slug_path=chapter_path,
                obj=chapter,
                tutorial = part.tutorial,
                contents = [(os.path.join(chapter.get_path(relative=True),"introduction.md"), data["introduction"]),
                            (os.path.join(chapter.get_path(relative=True),"conclusion.md"), data["conclusion"])],
                action="add",
            )
            if "submit_continue" in request.POST:
                form = ChapterForm()
                messages.success(request,
                                 u'Chapitre « {0} » ajouté '
                                 u'avec succès.'.format(chapter.title))
            else:
                return redirect(chapter.get_absolute_url())
    else:
        form = ChapterForm()

    return render_template("tutorial/chapter/new.html", {"part": part,
                                                         "form": form})

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

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    
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

    repo = Repo(tutorial.get_path())
    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    mandata = tutorial.load_data(mandata=json_reader.loads(manifest), sha=sha)
    parts = mandata["parts"]
    cpt_p = 1
    final_chapter = None
    chapter_tab = []
    final_position = 0
    find = False
    for part in parts:
        cpt_c = 1
        part = load_data_part(tutorial=mandata, man_level=part)
        part["position_in_tutorial"] = cpt_p
        for chapter in part["chapters"]:
            chapter = load_data_chapter(part=part, man_level=chapter)
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            if chapter_pk == str(chapter["pk"]):
                find = True
                chapter["intro"] = get_blob(repo.commit(sha).tree, chapter["introduction"])
                chapter["conclu"] = get_blob(repo.commit(sha).tree, chapter["conclusion"])
                
                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext = load_data_extract(chapter=chapter, man_level=ext)
                    ext["position_in_chapter"] = cpt_e
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

    prev_chapter = (chapter_tab[final_position - 1] if final_position > 0 else None)
    next_chapter = (chapter_tab[final_position + 1] if final_position + 1
                    < len(chapter_tab) else None)
    
    return render_template("tutorial/chapter/view.html", {
        "tutorial": mandata,
        "chapter": final_chapter,
        "prev": prev_chapter,
        "next": next_chapter,
        "version": sha,
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
    """View chapter online."""

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    if not tutorial.on_line():
        raise Http404

    # find the good manifest file
    mandata = tutorial.load_data(mandata=tutorial.load_json(tutorial.sha_public), sha=tutorial.sha_public, public=True)
    mandata['get_parts'] = mandata["parts"]
    parts = mandata["parts"]
    cpt_p = 1
    final_chapter = None
    chapter_tab = []
    final_position = 0
    
    find = False
    for part in parts:
        cpt_c = 1
        part = load_data_part(tutorial=mandata, man_level=part)
        part["position_in_tutorial"] = cpt_p
        
        for chapter in part["chapters"]:
            chapter = load_data_chapter(part=part, man_level=chapter)
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            if chapter_pk == str(chapter["pk"]):
                find = True
                intro = open(os.path.join(tutorial.get_prod_path(),chapter["introduction"] + ".html"), "r")
                chapter["intro"] = intro.read()
                intro.close()
                conclu = open(os.path.join(tutorial.get_prod_path(),chapter["conclusion"] +".html"), "r")
                chapter["conclu"] = conclu.read()
                conclu.close()
                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext = load_data_extract(chapter=chapter, man_level=ext)
                    ext["position_in_chapter"] = cpt_e
                    text = open(os.path.join(tutorial.get_prod_path(), ext["text"] + ".html"), "r")
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

    return render_template("tutorial/chapter/view_online.html", {
        "tutorial" : mandata,
        "chapter": final_chapter,
        "parts": parts,
        "prev": prev_chapter,
        "next": next_chapter,
    })

@can_write_and_read_now
@login_required
@require_POST
def modify_chapter(request):
    """Modify the given chapter."""

    data = request.POST
    try:
        chapter_pk = request.POST["chapter"]
    except KeyError:
        raise Http404
    chapter = get_object_or_404(Chapter, pk=chapter_pk)
    part = chapter.part

    # Make sure the user is allowed to do that

    if request.user not in chapter.get_tutorial().authors.all() and not request.user.has_perm("tutorial.change_tutorial"):
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
        
        maj_repo(user=request.user,
                 old_slug_path = chapter.part.get_path(),
                 new_slug_path = chapter.part.get_path(),
                 obj = chapter.part,
                 tutorial = chapter.part.tutorial,
                 action = "maj")
        
        messages.info(request, u"Le chapitre a bien été déplacé.")
    elif "delete" in data:
        old_pos = chapter.position_in_part
        old_tut_pos = chapter.position_in_tutorial
        
        # Move other chapters first

        for tut_c in part.get_chapters():
            if old_pos <= tut_c.position_in_part:
                tut_c.position_in_part = tut_c.position_in_part - 1
                tut_c.save()
        maj_repo(user=request.user,
                 obj=chapter,
                 tutorial=part.tutorial,
                 old_slug_path=chapter.get_path(),
                 action="del")

        # Then delete the chapter
        new_slug_path_part = os.path.join(settings.REPO_PATH, part.tutorial.get_phy_slug())
        chapter.delete()
        part.update_children()

        # Update all the position_in_tutorial fields for the next chapters
        for tut_c in Chapter.objects.filter(position_in_tutorial__gt=old_tut_pos):
            tut_c.update_position_in_tutorial()
            tut_c.save()
        
        maj_repo(user=request.user,
                 old_slug_path = new_slug_path_part,
                 new_slug_path = new_slug_path_part,
                 obj = part,
                 tutorial = part.tutorial,
                 action = "maj")
        messages.info(request, u"Le chapitre a bien été supprimé.")

        return redirect(part.get_absolute_url())

    return redirect(chapter.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_chapter(request):
    """Edit the given chapter."""
    try:
        chapter_pk = int(request.GET["chapitre"])
    except KeyError:
        raise Http404
    chapter = get_object_or_404(Chapter, pk=chapter_pk)

    big = chapter.part
    small = chapter.tutorial
    tutorial = chapter.get_tutorial()
    # Make sure the user is allowed to do that
    if (big and request.user not in chapter.part.tutorial.authors.all() \
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
                return render_template("tutorial/part/edit.html", 
                    {
                         "chapter": chapter,
                         "last_hash": compute_hash([introduction, conclusion]),
                         "new_version":True,
                         "form": form
                    })
            chapter.title = data["title"]
            
            old_slug = chapter.get_path()
            chapter.save()
            chapter.update_children()
            
            if chapter.part:
                new_slug =  chapter.get_path()
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
            maj_repo(
                     user=request.user,
                     old_slug_path=old_slug,
                     new_slug_path=new_slug,
                     obj=chapter,
                     tutorial=tutorial,
                     contents = [(os.path.join(chapter.get_path(relative=True), "introduction.md"),
                                  data["introduction"]),
                                 (os.path.join(chapter.get_path(relative=True), "conclusion.md"),
                                  data["conclusion"])],
                     action="maj",
            )
            return redirect(chapter.get_absolute_url())
    else:
        form = render_chapter_form(chapter)
    return render_template("tutorial/chapter/edit.html", {"chapter": chapter,
                                                          "last_hash": compute_hash([introduction, conclusion]),
                                                          "form": form})