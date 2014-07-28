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
from zds.utils.tutorials import get_blob, export_tutorial_to_md, move
from zds.utils.misc import compute_hash, content_has_changed
from zds.tutorial.views.versionning import maj_repo

def index(request):
    """Display all public tutorials of the website."""

    # The tag indicate what the category tutorial the user would like to
    # display. We can display all subcategories for tutorials.

    try:
        tag = get_object_or_404(SubCategory, slug=request.GET["tag"])
    except (KeyError, Http404):
        tag = None
    if tag is None:
        tutorials = \
            Tutorial.objects.filter(sha_public__isnull=False).exclude(sha_public="") \
            .order_by("-pubdate") \
            .all()
    else:
        # The tag isn't None and exist in the system. We can use it to retrieve
        # all tutorials in the subcategory specified.

        tutorials = Tutorial.objects.filter(
            sha_public__isnull=False,
            subcategory__in=[tag]).exclude(sha_public="").order_by("-pubdate").all()
    
    tuto_versions = []
    for tutorial in tutorials:
        mandata = tutorial.load_json(tutorial.sha_public)
        mandata = tutorial.load_dic(mandata)
        tuto_versions.append(mandata)
    return render_template("tutorial/index.html", {"tutorials": tuto_versions, "tag": tag})




def upload_images(images, tutorial):
    mapping = OrderedDict()

    # download images

    zfile = zipfile.ZipFile(images, "a")
    os.makedirs(os.path.abspath(os.path.join(tutorial.get_path(), "images")))
    for i in zfile.namelist():
        ph_temp = os.path.abspath(os.path.join(tutorial.get_path(), i))
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
            except:
                pass
    zfile.close()
    return mapping


def replace_real_url(md_text, dict):
    for (dt_old, dt_new) in dict.iteritems():
        md_text = md_text.replace(dt_old, dt_new)
    return md_text


def import_content(
    user,
    tuto,
    images,
    logo,
):
    tutorial = Tutorial()

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
        userg.user = user
        userg.save()
        tutorial.gallery = gal
        tutorial.save()
        tuto_path = os.path.join(settings.REPO_PATH, tutorial.get_phy_slug())
        mapping = upload_images(images, tutorial)
        maj_repo(
            user=user,
            new_slug_path=tuto_path,
            tutorial=tutorial,
            obj=tutorial,
            contents=[("introduction.md", replace_real_url(tutorial_intro.text, mapping)),
                      ("conclusion.md", replace_real_url(tutorial_conclu.text, mapping))],
            action="add",
        )
        tutorial.authors.add(user)
        part_count = 1
        for partie in tree.xpath("/bigtuto/parties/partie"):
            part_title = tree.xpath("/bigtuto/parties/partie["
                                    + str(part_count) + "]/titre")[0]
            part_intro = tree.xpath("/bigtuto/parties/partie["
                                    + str(part_count) + "]/introduction")[0]
            part_conclu = tree.xpath("/bigtuto/parties/partie["
                                     + str(part_count) + "]/conclusion")[0]
            part = Part()
            part.title = part_title.text.strip()
            part.position_in_tutorial = part_count
            part.tutorial = tutorial
            part.save()
            part.introduction = os.path.join(part.get_phy_slug(), "introduction.md")
            part.conclusion = os.path.join(part.get_phy_slug(), "conclusion.md")
            part_path = os.path.join(settings.REPO_PATH, part.tutorial.get_phy_slug(),part.get_phy_slug())
            part.save()
            maj_repo(
                user=user,
                new_slug_path=part_path,
                obj=part,
                tutorial=tutorial,
                contents=[(os.path.join(part.get_path(relative=True), "introduction.md"),
                           replace_real_url(part_intro.text, mapping)),
                          (os.path.join(part.get_path(relative=True), "conclusion.md"),
                           replace_real_url(part_conclu.text, mapping))],
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
                chapter = Chapter()
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
                chapter_path = os.path.join(settings.REPO_PATH,
                                            chapter.part.tutorial.get_phy_slug(),
                                            chapter.part.get_phy_slug(),
                                            chapter.get_phy_slug())
                chapter.save()
                maj_repo(
                    user=user,
                    new_slug_path=chapter_path,
                    obj=chapter,
                    tutorial=tutorial,
                    contents=[(os.path.join(chapter.get_path(relative=True), "introduction.md"),
                               replace_real_url(chapter_intro.text, mapping)),
                              (os.path.join(chapter.get_path(relative=True), "conclusion.md"),
                               replace_real_url(chapter_conclu.text, mapping))],
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
                    maj_repo(
                        user=user,
                        new_slug_path=extract.get_path(),
                        obj=extract,
                        tutorial=tutorial,
                        contents=[(os.path.join(extract.get_path(relative=True)),
                                   replace_real_url(extract_text.text,mapping))],
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
        userg.user = user
        userg.save()
        tutorial.gallery = gal
        tutorial.save()
        tuto_path = os.path.join(settings.REPO_PATH, tutorial.get_phy_slug())
        mapping = upload_images(images, tutorial)
        maj_repo(
                 user=user,
                 new_slug_path=tuto_path,
                 obj=tutorial,
                 tutorial=tutorial,
                 contents=[("introduction.md", replace_real_url(tutorial_intro.text, mapping)),
                           ("conclusion.md", replace_real_url(tutorial_conclu.text, mapping))],
                 action="add",
        )
        tutorial.authors.add(user)
        chapter = Chapter()
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
            maj_repo(
                     user=user,
                     new_slug_path=extract.get_path(),
                     obj=extract,
                     tutorial=tutorial,
                     contents=[(os.path.join(extract.get_path(relative=True)),
                                replace_real_url(extract_text.text,mapping))],
                     action="add")
            extract_count += 1


@can_write_and_read_now
@login_required
@require_POST
def local_import(request):
    import_content(request.user, request.POST["tuto"], request.POST["images"],
                   request.POST["logo"])
    return redirect(reverse("zds.member.views.tutorials"))


@can_write_and_read_now
@login_required
def import_tuto(request):
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)

        # check extension

        if "file" in request.FILES:
            filename = str(request.FILES["file"])
            ext = filename.split(".")[-1]
            if ext == "tuto":
                import_content(request.user, request.FILES["file"],
                               request.FILES["images"], "")
            else:
                raise Http404
        return redirect(reverse("zds.member.views.tutorials"))
    else:
        form = ImportForm()
        profile = get_object_or_404(Profile, user=request.user)
        oldtutos = []
        if profile.sdz_tutorial:
            olds = profile.sdz_tutorial.strip().split(":")
        else:
            olds = []
        for old in olds:
            oldtutos.append(get_info_old_tuto(old))
    return render_template(
        "tutorial/tutorial/import.html", {"form": form, "old_tutos": oldtutos})



def download(request):
    """Download a tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=request.GET["tutoriel"])
    ph = os.path.join(settings.REPO_PATH, tutorial.get_phy_slug())
    repo = Repo(ph)
    repo.archive(open(ph + ".tar", "w"))
    response = HttpResponse(open(ph + ".tar", "rb").read(),
                            mimetype="application/tar")
    response["Content-Disposition"] = \
        "attachment; filename={0}.tar".format(tutorial.slug)
    return response



@permission_required("tutorial.change_tutorial", raise_exception=True)
def download_markdown(request):
    """Download a markdown tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
                tutorial.get_prod_path(),
                tutorial.slug +
                ".md") 
    response = HttpResponse(
        open(phy_path, "rb").read(),
        mimetype="application/txt")
    response["Content-Disposition"] = \
        "attachment; filename={0}.md".format(tutorial.slug)
    return response



def download_html(request):
    """Download a pdf tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
                tutorial.get_prod_path(),
                tutorial.slug +
                ".html")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        mimetype="text/html")
    response["Content-Disposition"] = \
        "attachment; filename={0}.html".format(tutorial.slug)
    return response



def download_pdf(request):
    """Download a pdf tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
                tutorial.get_prod_path(),
                tutorial.slug +
                ".pdf")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        mimetype="application/pdf")
    response["Content-Disposition"] = \
        "attachment; filename={0}.pdf".format(tutorial.slug)
    return response



def download_epub(request):
    """Download an epub tutorial."""

    tutorial = get_object_or_404(Tutorial, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
                tutorial.get_prod_path(),
                tutorial.slug +
                ".epub")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        mimetype="application/epub")
    response["Content-Disposition"] = \
        "attachment; filename={0}.epub".format(tutorial.slug)
    return response


def get_url_images(md_text, pt):
    """find images urls in markdown text and download this."""

    regex = ur"(!\[.*?\]\()(.+?)(\))"

    # if text is empty don't download

    if md_text is not None:
        imgs = re.findall(regex, md_text)
        for img in imgs:

            # decompose images

            parse_object = urlparse(img[1])

            # if link is http type

            if parse_object.scheme in ("http", "https", "ftp") or \
            parse_object.netloc[:3]=="www" or \
            parse_object.path[:3]=="www":
                (filepath, filename) = os.path.split(parse_object.path)
                if not os.path.isdir(os.path.join(pt, "images")):
                    os.makedirs(os.path.join(pt, "images"))

                # download image

                urlretrieve(img[1], os.path.abspath(os.path.join(pt, "images",
                                                                 filename)))
                ext = filename.split(".")[-1]

                # if image is gif, convert to png

                if ext == "gif":
                    im = ImagePIL.open(os.path.join(pt, img[1]))
                    im.save(os.path.join(pt, filename.split(".")[0] + ".png"))
            else:

                # relative link

                srcfile = settings.SITE_ROOT + img[1]
                if os.path.isfile(srcfile):
                    dstroot = pt + img[1]
                    dstdir = os.path.dirname(dstroot)
                    if not os.path.exists(dstdir):
                        os.makedirs(dstdir)
                    shutil.copy(srcfile, dstroot)
                    ext = dstroot.split(".")[-1]
    
                    # if image is gif, convert to png
    
                    if ext == "gif":
                        im = ImagePIL.open(dstroot)
                        im.save(os.path.join(dstroot.split(".")[0] + ".png"))


def sub_urlimg(g):
    start = g.group("start")
    url = g.group("url")
    parse_object = urlparse(url)
    (filepath, filename) = os.path.split(parse_object.path)
    ext = filename.split(".")[-1]
    if ext == "gif":
        if parse_object.scheme in ("http", "https") or \
        parse_object.netloc[:3]=="www" or \
        parse_object.path[:3]=="www":
            url = os.path.join("images", filename.split(".")[0] + ".png")
        else:
            url = (url.split(".")[0])[1:] + ".png"
    else:
        if parse_object.scheme in ("http", "https") or \
        parse_object.netloc[:3]=="www" or \
        parse_object.path[:3]=="www":
            url = os.path.join("images", filename)
        else:
            url = url[1:]
    end = g.group("end")
    return start + url + end


def markdown_to_out(md_text):
    return re.sub(ur"(?P<start>!\[.*?\]\()(?P<url>.+?)(?P<end>\))", sub_urlimg,
                  md_text)