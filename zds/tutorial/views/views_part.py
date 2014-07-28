# -*- coding: utf-8 -*-
import os.path
import re
import shutil
import zipfile

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

from zds.member.decorator import can_write_and_read_now
from zds.tutorial.views.versionning import maj_repo
from zds.tutorial.forms import PartForm
from zds.tutorial.models import Tutorial, Part, Chapter, Extract, never_read, \
    mark_read
from zds.utils import render_template
from zds.utils import slugify
from zds.utils.misc import compute_hash, content_has_changed
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move, export_tutorial, load_data_part,\
load_data_chapter, load_data_extract
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
def add_part(request):
    """Add a new part."""

    try:
        tutorial_pk = request.GET["tutoriel"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

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
            part = Part()
            part.tutorial = tutorial
            part.title = data["title"]
            part.position_in_tutorial = tutorial.get_parts().count() + 1
            part.save()
            part.introduction = os.path.join(part.get_phy_slug(), "introduction.md")
            part.conclusion = os.path.join(part.get_phy_slug(), "conclusion.md")
            part.save()
            
            new_slug = os.path.join(settings.REPO_PATH, part.tutorial.get_phy_slug(), part.get_phy_slug())

            maj_repo(
                user=request.user,
                new_slug_path=new_slug,
                tutorial=part.tutorial,
                obj=part,
                contents=[(os.path.join(part.get_path(relative=True), "introduction.md"),
                           data["introduction"]),
                          (os.path.join(part.get_path(relative=True), "conclusion.md"),
                           data["conclusion"])],
                action="add",
            )
            if "submit_continue" in request.POST:
                form = PartForm()
                messages.success(request,
                                 u'Partie « {0} » ajouté '
                                 u'avec succès.'.format(part.title))
            else:
                return redirect(part.get_absolute_url())
    else:
        form = PartForm()
    return render_template("tutorial/part/new.html", {"tutorial": tutorial,
                                                      "form": form})


@can_write_and_read_now
@login_required
def modify_part(request):
    """Modifiy the given part."""

    if not request.method == "POST":
        raise Http404
    part_pk = request.POST["part"]
    part = get_object_or_404(Part, pk=part_pk)
    tutorial = part.tutorial

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
        
        new_slug_path = os.path.join(settings.REPO_PATH, part.tutorial.get_phy_slug())
        
        maj_repo(user = request.user,
                 old_slug_path = new_slug_path,
                 new_slug_path = new_slug_path,
                 tutorial = part.tutorial,
                 obj = tutorial,
                 action = "maj")
    elif "delete" in request.POST:
        # Delete all chapters belonging to the part
        Chapter.objects.all().filter(part=part).delete()

        # Move other parts
        old_pos = part.position_in_tutorial
        for tut_p in part.tutorial.get_parts():
            if old_pos <= tut_p.position_in_tutorial:
                tut_p.position_in_tutorial = tut_p.position_in_tutorial - 1
                tut_p.save()

        maj_repo(user = request,
                 old_slug_path=part.get_path(),
                 tutorial = tutorial,
                 obj=part,
                 action="del")

        # Actually delete the part
        part.delete()
        tutorial.update_children()
        
        maj_repo(user = request.user,
                 old_slug_path = tutorial.get_path(),
                 new_slug_path = tutorial.get_path(),
                 tutorial = tutorial,
                 obj = tutorial,
                 action = "maj")
        
    return redirect(part.tutorial.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_part(request):
    """Edit the given part."""

    try:
        part_pk = int(request.GET["partie"])
    except KeyError:
        raise Http404
    part = get_object_or_404(Part, pk=part_pk)
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
            if content_has_changed([introduction, conclusion],data["last_hash"]):
                form = PartForm({"title": part.title,
                         "introduction": part.get_introduction(),
                         "conclusion": part.get_conclusion()})
                return render_template("tutorial/part/edit.html", 
                    {
                         "part": part,
                         "last_hash": compute_hash([introduction, conclusion]),
                         "new_version":True,
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
            
            maj_repo(
                     user = request.user,
                     old_slug_path=old_slug,
                     new_slug_path=part.get_path(),
                     obj=part,
                     tutorial=part.tutorial,
                     contents=[(os.path.join(part.get_path(relative=True), "introduction.md"),
                                data["introduction"]),
                               (os.path.join(part.get_path(relative=True), "conclusion.md"),
                                data["conclusion"])],
                action="maj",
            )
            return redirect(part.get_absolute_url())
    else:
        form = PartForm({"title": part.title,
                         "introduction": part.get_introduction(),
                         "conclusion": part.get_conclusion()})
    return render_template("tutorial/part/edit.html",
        {
            "part": part,
	        "last_hash": compute_hash([introduction, conclusion]),
            "form": form
        })

@login_required
def view_part(
    request,
    tutorial_pk,
    tutorial_slug,
    part_pk,
    part_slug,
):
    """Display a part."""

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

    final_part = None

    # find the good manifest file

    repo = Repo(tutorial.get_path())
    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    mandata = tutorial.load_data(mandata=json_reader.loads(manifest), sha=sha)
    parts = mandata["parts"]
    cpt_p = 1
    for part in parts:
        part = load_data_part(tutorial=mandata, man_level=part)
        part["position_in_tutorial"] = cpt_p
        if part_pk == str(part["pk"]):
            part["intro"] = get_blob(repo.commit(sha).tree, part["introduction"])
            part["conclu"] = get_blob(repo.commit(sha).tree, part["conclusion"])
        cpt_c = 1
        for chapter in part["chapters"]:
            chapter = load_data_chapter(part=part, man_level=chapter)
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            cpt_e = 1
            for ext in chapter["extracts"]:
                ext = load_data_extract(chapter=chapter, man_level=ext)
                ext["position_in_chapter"] = cpt_e
                cpt_e += 1
            cpt_c += 1
        final_part = part
        cpt_p += 1
    # if part can't find
    if final_part is None:
        raise Http404
    return render_template("tutorial/part/view.html",
                           {"tutorial": mandata,
                            "part": final_part,
                            "version": sha})



def view_part_online(
    request,
    tutorial_pk,
    tutorial_slug,
    part_pk,
    part_slug,
):
    """Display a part."""

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    if not tutorial.on_line():
        raise Http404

    # find the good manifest file
    mandata = tutorial.load_data(mandata=tutorial.load_json(tutorial.sha_public), sha=tutorial.sha_public, public=True)
    parts = mandata["parts"]
    cpt_p = 1
    final_part= None
    find = False
    for part in parts:
        part = load_data_part(tutorial=mandata, man_level=part)
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
            final_part=part
        cpt_c = 1
        for chapter in part["chapters"]:
            chapter = load_data_chapter(part=part, man_level=chapter)
            chapter["position_in_part"] = cpt_c
            chapter["position_in_tutorial"] = cpt_c * cpt_p
            if part_slug == slugify(part["title"]):
                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext = load_data_extract(chapter=chapter, man_level=ext)
                    ext["position_in_chapter"] = cpt_e
                    cpt_e += 1
            cpt_c += 1
        cpt_p += 1

    # if part can't find
    if not find:
        raise Http404
    return render_template("tutorial/part/view_online.html", {"tutorial": mandata, "part": final_part})