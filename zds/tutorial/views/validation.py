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
from zds.member.decorator import can_write_and_read_now
from zds.member.models import get_info_old_tuto, Profile
from zds.utils import render_template
from zds.utils import slugify
from zds.utils.models import Category, Licence, SubCategory
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move
from zds.utils.misc import compute_hash, content_has_changed
from zds.tutorial.views.views_index import *

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
        subcategory = get_object_or_404(Category, pk=request.GET["subcategory"
                                                                 ])
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
                .order_by("date_proposition"
                          ).all()
    return render_template("tutorial/validation/index.html",
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
        messages.info(request, u"Le tutoriel n'est plus sous réserve.")
        return redirect(reverse("zds.tutorial.views.list_validation"))
    else:
        validation.validator = request.user
        validation.date_reserve = datetime.now()
        validation.status = "PENDING_V"
        validation.save()
        messages.info(request,
                      u"Le tutoriel a bien été \
                      réservé par {0}.".format(request.user.username))
        return redirect(validation.tutorial.get_absolute_url())



@login_required
def diff(request, tutorial_pk, tutorial_slug):
    try:
        sha = request.GET["sha"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied
    repo = Repo(tutorial.get_path())
    hcommit = repo.commit(sha)
    tdiff = hcommit.diff("HEAD~1")
    return render_template("tutorial/tutorial/diff.html", {
        "tutorial": tutorial,
        "path_add": tdiff.iter_change_type("A"),
        "path_ren": tdiff.iter_change_type("R"),
        "path_del": tdiff.iter_change_type("D"),
        "path_maj": tdiff.iter_change_type("M"),
    })



@login_required
def history(request, tutorial_pk, tutorial_slug):
    """History of the tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    repo = Repo(tutorial.get_path())
    logs = repo.head.reference.log()
    logs = sorted(logs, key=attrgetter("time"), reverse=True)
    return render_template("tutorial/tutorial/history.html",
                           {"tutorial": tutorial, "logs": logs})



@login_required
@permission_required("tutorial.change_tutorial", raise_exception=True)
def history_validation(request, tutorial_pk):
    """History of the validation of a tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # Get subcategory to filter validations.

    try:
        subcategory = get_object_or_404(Category, pk=request.GET["subcategory"
                                                                 ])
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
    return render_template("tutorial/validation/history.html",
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
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
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
        messages.info(request, u"Le tutoriel a bien été refusé.")

        # send feedback

        for author in tutorial.authors.all():
            msg = (
                u'Désolé **{0}**, ton zeste **{1}** n\'a malheureusement '
                u'pas passé l’étape de validation. Mais ne désespère pas, '
                u'certaines corrections peuvent sûrement être faites pour '
                u'l’améliorer et repasser la validation plus tard. '
                u'Voici le message que [{2}]({3}), ton validateur t\'a laissé\n\n> {4}\n\n'
                u'N\'hésite pas à lui envoyer un petit message pour discuter '
                u'de la décision ou demander plus de détails si tout cela te '
                u'semble injuste ou manque de clarté.'.format(
                author.username,
                tutorial.title,
                validation.validator.username,
                settings.SITE_URL + validation.validator.profile.get_absolute_url(),
                validation.comment_validator))
            bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
            send_mp(
                bot,
                [author],
                u"Refus de Validation : {0}".format(tutorial.title),
                "",
                msg,
                True,
                direct=False,
            )
        return redirect(tutorial.get_absolute_url() + "?version="
                        + validation.version)
    else:
        messages.error(request,
                    "Vous devez avoir réservé ce tutoriel "
                    "pour pouvoir le refuser.")
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
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    validation = Validation.objects.filter(
        tutorial__pk=tutorial_pk,
        version=tutorial.sha_validation).latest("date_proposition")

    if request.user == validation.validator:
        (output, err) = MEP(tutorial, tutorial.sha_validation)
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
        messages.success(request, u"Le tutoriel a bien été validé.")

        # send feedback

        for author in tutorial.authors.all():
            msg = (
                u'Félicitations **{0}** ! Ton zeste [{1}]({2}) '
                u'a été publié par [{3}]({4}) ! Les lecteurs du monde entier '
                u'peuvent venir l\'éplucher et réagir à son sujet. '
                u'Je te conseille de rester à leur écoute afin '
                u'd\'apporter des corrections/compléments.'
                u'Un Tutoriel vivant et à jour est bien plus lu '
                u'qu\'un sujet abandonné !'.format(
                author.username,
                tutorial.title,
                settings.SITE_URL + tutorial.get_absolute_url_online(),
                validation.validator.username,
                settings.SITE_URL + validation.validator.profile.get_absolute_url()))
            bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
            send_mp(
                bot,
                [author],
                u"Publication : {0}".format(tutorial.title),
                "",
                msg,
                True,
                direct=False,
            )
        return redirect(tutorial.get_absolute_url() + "?version="
                        + validation.version)
    else:
        messages.error(request,
                    "Vous devez avoir réservé ce tutoriel "
                    "pour pouvoir le valider.")
        return redirect(tutorial.get_absolute_url() + "?version="
                        + validation.version)


@can_write_and_read_now
@login_required
@permission_required("tutorial.change_tutorial", raise_exception=True)
@require_POST
def invalid_tutorial(request, tutorial_pk):
    """Staff invalid tutorial of an author."""

    # Retrieve current tutorial

    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)
    UNMEP(tutorial)
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
    messages.success(request, u"Le tutoriel a bien été dépublié.")
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
    tutorial = get_object_or_404(Tutorial, pk=tutorial_pk)

    # If the user isn't an author of the tutorial or isn't in the staff, he
    # hasn't permission to execute this method:

    if request.user not in tutorial.authors.all():
        if not request.user.has_perm("tutorial.change_tutorial"):
            raise PermissionDenied

    #delete old pending validation
    Validation.objects.filter(tutorial__pk=tutorial_pk,
                              status__in=['PENDING','PENDING_V'])\
                              .delete()
    # We create and save validation object of the tutorial.
    
    
    validation = Validation()
    validation.tutorial = tutorial
    validation.date_proposition = datetime.now()
    validation.comment_authors = request.POST["text"]
    validation.version = request.POST["version"]
    validation.save()
    validation.tutorial.source=request.POST["source"]
    validation.tutorial.sha_validation = request.POST["version"]
    validation.tutorial.save()
    messages.success(request,
                     u"Votre demande de validation a été envoyée à l'équipe.")
    return redirect(tutorial.get_absolute_url())


def MEP(tutorial, sha):
    (output, err) = (None, None)
    repo = Repo(tutorial.get_path())
    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    tutorial_version = json_reader.loads(manifest)
    if os.path.isdir(tutorial.get_prod_path()):
        try:
            shutil.rmtree(tutorial.get_prod_path())
        except:
            shutil.rmtree(u"\\\\?\{0}".format(tutorial.get_prod_path()))
    shutil.copytree(tutorial.get_path(), tutorial.get_prod_path())
    repo.head.reset(commit = sha, index=True, working_tree=True)
    
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

        get_url_images(md_file_contenu, tutorial.get_prod_path())

        # convert to out format
        out_file = open(os.path.join(tutorial.get_prod_path(), fichier), "w")
        if md_file_contenu is not None:
            out_file.write(markdown_to_out(md_file_contenu.encode("utf-8")))
        out_file.close()
        target = os.path.join(tutorial.get_prod_path(), fichier + ".html")
        os.chdir(os.path.dirname(target))
        try:
            html_file = open(target, "w")
        except IOError:

            # handle limit of 255 on windows

            target = u"\\\\?\{0}".format(target)
            html_file = open(target, "w")
        if md_file_contenu is not None:
            html_file.write(emarkdown(md_file_contenu))
        html_file.close()

    # load markdown out

    contenu = export_tutorial_to_md(tutorial, sha).lstrip()
    out_file = open(os.path.join(tutorial.get_prod_path(), tutorial.slug + ".md"), "w")
    out_file.write(smart_str(contenu))
    out_file.close()

    # define whether to log pandoc's errors
    
    pandoc_debug_str = ""
    if settings.PANDOC_LOG_STATE:
        pandoc_debug_str = " 2>&1 | tee -a "+settings.PANDOC_LOG
    
    # load pandoc

    os.chdir(tutorial.get_prod_path())
    os.system(settings.PANDOC_LOC
              + "pandoc --latex-engine=xelatex -s -S --toc "
              + os.path.join(tutorial.get_prod_path(), tutorial.slug)
              + ".md -o " + os.path.join(tutorial.get_prod_path(),
                                         tutorial.slug) + ".html"+pandoc_debug_str)
    os.system(settings.PANDOC_LOC + "pandoc " + "--latex-engine=xelatex "
              + "--template=../../assets/tex/template.tex " + "-s " + "-S "
              + "-N " + "--toc " + "-V documentclass=scrbook "
              + "-V lang=francais " + "-V mainfont=Verdana "
              + "-V monofont=\"Andale Mono\" " + "-V fontsize=12pt "
              + "-V geometry:margin=1in "
              + os.path.join(tutorial.get_prod_path(), tutorial.slug) + ".md "
              + "-o " + os.path.join(tutorial.get_prod_path(), tutorial.slug)
              + ".pdf"+pandoc_debug_str)
    os.system(settings.PANDOC_LOC + "pandoc -s -S --toc "
              + os.path.join(tutorial.get_prod_path(), tutorial.slug)
              + ".md -o " + os.path.join(tutorial.get_prod_path(),
                                         tutorial.slug) + ".epub"+pandoc_debug_str)
    os.chdir(settings.SITE_ROOT)
    return (output, err)


def UNMEP(tutorial):
    if os.path.isdir(tutorial.get_prod_path()):
        try:
            shutil.rmtree(tutorial.get_prod_path())
        except:
            shutil.rmtree(u"\\\\?\{0}".format(tutorial.get_prod_path()))