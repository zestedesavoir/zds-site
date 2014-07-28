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
from zds.tutorial.views.versionning import maj_repo
from zds.tutorial.forms import TutorialForm, PartForm, ChapterForm, EmbdedChapterForm, \
    ExtractForm, ImportForm, NoteForm, AskValidationForm, ValidForm, RejectForm
from zds.tutorial.models import Tutorial, Part, Chapter, Extract, Validation, never_read, \
    mark_read, Note
from zds.utils import render_template, slugify
from zds.utils.misc import compute_hash, content_has_changed 
from zds.utils.models import Category, Licence, CommentLike, CommentDislike, \
    SubCategory, Alert
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move, load_data_part,\
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
def add_tutorial(request):
    """'Adds a tutorial."""

    if request.method == "POST":
        form = TutorialForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data

            # Creating a tutorial

            tutorial = Tutorial()
            tutorial.title = data["title"]
            tutorial.description = data["description"]
            tutorial.type = data["type"]
            tutorial.introduction = "introduction.md"
            tutorial.conclusion = "conclusion.md"
            tutorial.images = "images"
            if "licence" in data and data["licence"] != "":
                lc = Licence.objects.filter(pk=data["licence"]).all()[0]
                tutorial.licence = lc

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

            # We need to save the tutorial before changing its author list
            # since it's a many-to-many relationship

            tutorial.authors.add(request.user)

            # If it's a small tutorial, create its corresponding chapter

            if tutorial.type == "MINI":
                chapter = Chapter()
                chapter.tutorial = tutorial
                chapter.save()
            tutorial.save()
            maj_repo(
                user = request.user,
                new_slug_path=tutorial.get_path(),
                tutorial=tutorial,
                obj=tutorial,
                contents = [("introduction.md", data["introduction"]),
                            ("conclusion.md", data["conclusion"])],
                action="add",
            )
            return redirect(tutorial.get_absolute_url())
    else:
        form = TutorialForm()
    return render_template("tutorial/tutorial/new.html", {"form": form})


@can_write_and_read_now
@login_required
def edit_tutorial(request):
    """Edit a tutorial."""

    # Retrieve current tutorial;

    try:
        tutorial_pk = request.GET["tutoriel"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff, he
    # hasn't permission to execute this method:

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied
    introduction = os.path.join(tutorial.get_path(), "introduction.md")
    conclusion = os.path.join(tutorial.get_path(), "conclusion.md")
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

                })
                return render_template("tutorial/tutorial/edit.html",
                           {
                               "tutorial": tutorial, "form": form,
                               "last_hash": compute_hash([introduction, conclusion]),
                               "new_version": True
                           })        
            old_slug = tutorial.get_path()
            tutorial.title = data["title"]
            tutorial.description = data["description"]
            if "licence" in data and data["licence"] != "":
                lc = Licence.objects.filter(pk=data["licence"]).all()[0]
                tutorial.licence = lc

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

            new_slug = os.path.join(settings.REPO_PATH, tutorial.get_phy_slug())
            
            maj_repo(
                user = request.user,
                old_slug_path = old_slug,
                new_slug_path = new_slug,
                tutorial = tutorial,
                obj=tutorial,
                contents = [("introduction.md", data["introduction"]),
                            ("conclusion.md", data["conclusion"])],
                action="maj",
            )
            tutorial.subcategory.clear()
            for subcat in form.cleaned_data["subcategory"]:
                tutorial.subcategory.add(subcat)
            tutorial.save()
            return redirect(tutorial.get_absolute_url())
    else:
        json = tutorial.load_json(sha=tutorial.sha_draft)
        if "licence" in json:
            licence = Licence.objects.filter(code=json["licence"]).all()[0]
        else:
            licence = None
        form = TutorialForm(initial={
            "title": json["title"],
            "type": json["type"],
            "licence": licence,
            "description": json["description"],
            "subcategory": tutorial.subcategory.all(),
            "introduction": tutorial.get_introduction(),
            "conclusion": tutorial.get_conclusion(),
        })
    return render_template("tutorial/tutorial/edit.html",
                           {"tutorial": tutorial, "form": form, "last_hash": compute_hash([introduction, conclusion])})

@can_write_and_read_now
def modify_tutorial(request):
    if not request.method == "POST":
        raise Http404
    tutorial_pk = request.POST["tutorial"]
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

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
                             u'L\'auteur {0} a bien été ajouté à la rédaction '
                             u'du tutoriel.'.format(author.username))
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
                             u"L'auteur {0} a bien été retiré du tutoriel."
                             .format(author.username))
            return redirect(redirect_url)
        elif "activ_beta" in request.POST:
            if "version" in request.POST and tutorial.sha_draft == request.POST['version'] :
                tutorial.sha_beta = tutorial.sha_draft
                tutorial.save()
                messages.success(request, u"La BETA sur ce tutoriel est bien activée.")
            else:
                messages.error(request, u"Impossible d'activer la BETA sur ce tutoriel.")
            return redirect(tutorial.get_absolute_url_beta())
        elif "update_beta" in request.POST:
            if "version" in request.POST and tutorial.sha_draft == request.POST['version'] :
                tutorial.sha_beta = tutorial.sha_draft
                tutorial.save()
                messages.success(request, u"La BETA sur ce tutoriel a bien été mise à jour.")
            else:
                messages.error(request, u"Impossible de mettre à jour la BETA sur ce tutoriel.")
            return redirect(tutorial.get_absolute_url_beta())
        elif "desactiv_beta" in request.POST:
            tutorial.sha_beta = None
            tutorial.save()
            messages.info(request, u"La BETA sur ce tutoriel a été désactivée.")
            return redirect(tutorial.get_absolute_url())

    # No action performed, raise 403

    raise PermissionDenied


@can_write_and_read_now
@login_required
@require_POST
def delete_tutorial(request, tutorial_pk):
    """User would like delete his tutorial."""

    # Retrieve current tutorial

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

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
        maj_repo(user = request.user,
                 old_slug_path=tutorial.get_path(),
                 tutorial=tutorial,
                 obj = tutorial,
                 action="del")
        messages.success(request,
                         u'Le tutoriel {0} a bien '
                         u'été supprimé.'.format(tutorial.title))
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
                         u'Vous ne faites plus partie des rédacteurs de ce '
                         u'tutoriel')
    return redirect(reverse("zds.tutorial.views.index"))


@login_required
def view_tutorial(request, tutorial_pk, tutorial_slug):
    """Show the given offline tutorial if exists."""

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # Retrieve sha given by the user. This sha must to be exist. If it doesn't
    # exist, we take draft version of the article.

    try:
        sha = request.GET["version"]
    except KeyError:
        sha = tutorial.sha_draft
    
    is_beta = sha == tutorial.sha_beta and tutorial.in_beta()

    # Only authors of the tutorial and staff can view tutorial in offline.

    if request.user not in tutorial.authors.all() and not is_beta:
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied


    # Two variables to handle two distinct cases (large/small tutorial)

    chapter = None
    parts = None

    # Find the good manifest file

    repo = Repo(tutorial.get_path())

    # Load the tutorial.

    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    mandata = tutorial.load_data(mandata=json_reader.loads(manifest), sha=sha)

    # If it's a small tutorial, fetch its chapter

    if tutorial.type == "MINI":
        if "chapter" in mandata:
            chapter = mandata["chapter"]
            chapter["pk"] = tutorial.get_chapter().pk
            chapter["path"] = tutorial.get_path()
            chapter["type"] = "MINI"
            chapter["intro"] = get_blob(repo.commit(sha).tree,
                                        "introduction.md")
            chapter["conclu"] = get_blob(repo.commit(sha).tree, "conclusion.md"
                                         )
            cpt = 1
            for ext in chapter["extracts"]:
                ext["position_in_chapter"] = cpt
                ext["path"] = tutorial.get_path()
                ext["txt"] = get_blob(repo.commit(sha).tree, ext["text"])
                cpt += 1
        else:
            chapter = None
    else:

        # If it's a big tutorial, fetch parts.

        parts = mandata["parts"]
        cpt_p = 1
        for part in parts:
            part = load_data_part(tutorial=mandata, man_level=part)
            part["position_in_tutorial"] = cpt_p
            cpt_c = 1
            for chapter in part["chapters"]:
                chapter = load_data_chapter(part=part, man_level=chapter)
                chapter["position_in_part"] = cpt_c
                chapter["position_in_tutorial"] = cpt_c * cpt_p
                cpt_e = 1
                for ext in chapter["extracts"]:
                    ext = load_data_extract(chapter=chapter, man_level=ext)
                    ext["position_in_chapter"] = cpt_e
                    ext["txt"] = get_blob(repo.commit(sha).tree, ext["text"])
                    cpt_e += 1
                cpt_c += 1
            cpt_p += 1
    validation = Validation.objects.filter(tutorial__pk=tutorial.pk,
                                           version=sha)\
                                    .order_by("-date_proposition")\
                                    .first()
    formAskValidation = AskValidationForm()
    if tutorial.source:
        formValid = ValidForm(initial={"source": tutorial.source})
    else:
        formValid = ValidForm()
    formReject = RejectForm()

    return render_template("tutorial/tutorial/view.html", {
        "tutorial": mandata,
        "chapter": chapter,
        "parts": parts,
        "version": sha,
        "validation": validation,
        "formAskValidation": formAskValidation,
        "formValid": formValid,
        "formReject": formReject,
    })



def view_tutorial_online(request, tutorial_pk, tutorial_slug):
    """Display a tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # If the tutorial isn't online, we raise 404 error.
    if not tutorial.on_line():
        raise Http404

    # Two variables to handle two distinct cases (large/small tutorial)

    chapter = None
    parts = None

    # find the good manifest file

    mandata = tutorial.load_data(tutorial.load_json(tutorial.sha_public), sha=tutorial.sha_public, public=True)
    mandata["get_note_count"] = tutorial.get_note_count()

    # If it's a small tutorial, fetch its chapter

    if tutorial.type == "MINI":
        if "chapter" in mandata:
            chapter = mandata["chapter"]
            chapter["path"] = tutorial.get_prod_path()
            chapter["type"] = "MINI"
            intro = open(os.path.join(tutorial.get_prod_path(),
                                      mandata["introduction"] + ".html"), "r")
            chapter["intro"] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(),
                                       mandata["conclusion"] + ".html"), "r")
            chapter["conclu"] = conclu.read()
            conclu.close()
            cpt = 1
            for ext in chapter["extracts"]:
                ext["position_in_chapter"] = cpt
                ext["path"] = tutorial.get_prod_path()
                text = open(os.path.join(tutorial.get_prod_path(), ext["text"]
                                         + ".html"), "r")
                ext["txt"] = text.read()
                text.close()
                cpt += 1
        else:
            chapter = None
    else:

        # chapter = Chapter.objects.get(tutorial=tutorial)

        parts = mandata["parts"]
        cpt_p = 1
        for part in parts:
            part = load_data_part(tutorial=mandata, man_level=part)
            part["position_in_tutorial"] = cpt_p
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
            cpt_p += 1

        mandata['get_parts'] = parts

    # If the user is authenticated

    if request.user.is_authenticated():

        # If the user is never read, we mark this tutorial read.
        if never_read(tutorial):
            mark_read(tutorial)

    # Find all notes of the tutorial.

    notes = Note.objects.filter(tutorial__pk=tutorial.pk).order_by("position"
                                                                   ).all()

    # Retrieve pk of the last note. If there aren't notes for the tutorial, we
    # initialize this last note at 0.

    last_note_pk = 0
    if tutorial.last_note:
        last_note_pk = tutorial.last_note.pk

    # Handle pagination

    paginator = Paginator(notes, settings.POSTS_PER_PAGE)
    try:
        page_nbr = int(request.GET["page"])
    except KeyError:
        page_nbr = 1
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

    # Build form to send a note for the current tutorial.

    form = NoteForm(tutorial, request.user)
    return render_template("tutorial/tutorial/view_online.html", {
        "tutorial": mandata,
        "chapter": chapter,
        "parts": parts,
        "notes": res,
        "pages": paginator_range(page_nbr, paginator.num_pages),
        "nb": page_nbr,
        "last_note_pk": last_note_pk,
        "form": form,
    })

def find_tuto(request, pk_user):
    try:
        type = request.GET["type"]
    except KeyError:
        type = None
    display_user = get_object_or_404(User, pk=pk_user)
    if type == "beta":
        tutorials = Tutorial.objects.all().filter(
            authors__in=[display_user],
            sha_beta__isnull=False).exclude(sha_beta="").order_by("-pubdate")
        
        tuto_versions = []
        for tutorial in tutorials:
            mandata = tutorial.load_data(mandata=tutorial.load_json(sha=tutorial.sha_beta),
                                        sha=tutorial.sha_beta)
            tuto_versions.append(mandata)

        return render_template("tutorial/member/beta.html",
                               {"tutorials": tuto_versions, "usr": display_user})
    else:
        tutorials = Tutorial.objects.all().filter(
            authors__in=[display_user],
            sha_public__isnull=False).exclude(sha_public="").order_by("-pubdate")
        
        tuto_versions = []
        for tutorial in tutorials:
            mandata = tutorial.load_data(mandata=tutorial.load_json(tutorial.sha_public),
                                        sha=sha_public,
                                        public=True)
            tuto_versions.append(mandata)

        return render_template("tutorial/member/online.html", {"tutorials": tuto_versions,
                                                               "usr": display_user})
