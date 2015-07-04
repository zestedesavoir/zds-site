# coding: utf-8

from collections import OrderedDict
from datetime import datetime
import os

from git import Repo, Actor

from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _

from zds.utils import slugify
from zds.utils.models import Licence


# Used for indexing tutorials, we need to parse each manifest to know which content have been published
class GetPublished:

    published_part = []
    published_chapter = []
    published_extract = []

    def __init__(self):
        pass

    @classmethod
    def get_published_content(cls):
        # If all array are empty load_it
        if not len(GetPublished.published_part) and \
           not len(GetPublished.published_chapter) and \
           not len(GetPublished.published_extract):

            # Get all published tutorials
            from zds.tutorial.models import Tutorial
            tutorials_database = Tutorial.objects.filter(sha_public__isnull=False).all()

            for tutorial in tutorials_database:
                # Load Manifest
                json = tutorial.load_json_for_public()

                # Parse it
                GetPublished.load_tutorial(json)

        return {"parts": GetPublished.published_part,
                "chapters": GetPublished.published_chapter,
                "extracts": GetPublished.published_extract}

    @classmethod
    def load_tutorial(cls, json):
        # Load parts, chapter and extract
        if 'parts' in json:
            for part_json in json['parts']:

                # If inside of parts we have chapters, load it
                GetPublished.load_chapters(part_json)
                GetPublished.load_extracts(part_json)

                GetPublished.published_part.append(part_json['pk'])

        GetPublished.load_chapters(json)
        GetPublished.load_extracts(json)

    @classmethod
    def load_chapters(cls, json):
        if 'chapters' in json:
            for chapters_json in json['chapters']:

                GetPublished.published_chapter.append(chapters_json['pk'])
                GetPublished.load_extracts(chapters_json)

        return GetPublished.published_chapter

    @classmethod
    def load_extracts(cls, json):
        if 'extracts' in json:
            for extract_json in json['extracts']:
                GetPublished.published_extract.append(extract_json['pk'])

        return GetPublished.published_extract


# Export-to-dict functions
def export_chapter(chapter, export_all=True):
    from zds.tutorial.models import Extract
    """
    Export a chapter to a dict
    """
    dct = OrderedDict()
    if export_all:
        dct['pk'] = chapter.pk
        dct['title'] = chapter.title
        dct['introduction'] = chapter.introduction
        dct['conclusion'] = chapter.conclusion
    dct['extracts'] = []

    extracts = Extract.objects.filter(chapter=chapter)\
        .order_by('position_in_chapter')

    for extract in extracts:
        extract_dct = OrderedDict()
        extract_dct['pk'] = extract.pk
        extract_dct['title'] = extract.title
        extract_dct['text'] = extract.text
        dct['extracts'].append(extract_dct)

    return dct


def export_part(part):
    from zds.tutorial.models import Chapter
    """
    Export a part to a dict
    """
    dct = OrderedDict()
    dct['pk'] = part.pk
    dct['title'] = part.title
    dct['introduction'] = part.introduction
    dct['conclusion'] = part.conclusion
    dct['chapters'] = []

    chapters = Chapter.objects\
        .filter(part=part)\
        .order_by('position_in_part')
    for chapter in chapters:
        dct['chapters'].append(export_chapter(chapter))

    return dct


def export_tutorial(tutorial):
    from zds.tutorial.models import Part, Chapter
    """
    Export a tutorial to a dict
    """
    dct = OrderedDict()
    dct['title'] = tutorial.title
    dct['description'] = tutorial.description
    dct['type'] = tutorial.type
    if tutorial.licence:
        dct['licence'] = tutorial.licence.code
    dct['introduction'] = tutorial.introduction
    dct['conclusion'] = tutorial.conclusion

    if tutorial.is_mini():
        # We export the chapter without its empty title if mini tutorial
        try:
            chapter = Chapter.objects.get(tutorial__pk=tutorial.pk)
            dct['chapter'] = export_chapter(chapter, export_all=False)
        except Chapter.DoesNotExist:
            pass
    else:
        dct['parts'] = []
        parts = Part.objects\
            .filter(tutorial__pk=tutorial.pk)\
            .order_by('position_in_tutorial')
        for part in parts:
            dct['parts'].append(export_part(part))

    return dct


def get_blob(tree, chemin):
    for blob in tree.blobs:
        try:
            if os.path.abspath(blob.path) == os.path.abspath(chemin):
                data = blob.data_stream.read()
                return data.decode('utf-8')
        except (OSError, IOError):
            return ""
    if len(tree.trees) > 0:
        for atree in tree.trees:
            result = get_blob(atree, chemin)
            if result is not None:
                return result
        return None
    else:
        return None


def export_tutorial_to_md(tutorial, sha=None):
    # Two variables to handle two distinct cases (large/small tutorial)
    chapter = None
    parts = None
    tuto = OrderedDict()

    intro = open(os.path.join(tutorial.get_prod_path(sha), tutorial.introduction), "r")
    intro_contenu = intro.read()
    intro.close()
    tuto['intro'] = intro_contenu

    conclu = open(os.path.join(tutorial.get_prod_path(sha), tutorial.conclusion), "r")
    conclu_contenu = conclu.read()
    conclu.close()
    tuto['conclu'] = conclu_contenu

    tuto['image'] = tutorial.image
    tuto['title'] = tutorial.title
    tuto['is_mini'] = tutorial.is_mini()
    tuto['authors'] = tutorial.authors
    tuto['subcategory'] = tutorial.subcategory
    tuto['pubdate'] = datetime.now()

    tuto['pk'] = tutorial.pk
    tuto['slug'] = tutorial.slug

    # find the good manifest file
    mandata = tutorial.load_json_for_public(sha=sha)

    # If it's a small tutorial, fetch its chapter
    if tutorial.type == 'MINI':
        if 'chapter' in mandata:
            chapter = mandata['chapter']
            chapter['path'] = tutorial.get_prod_path(sha)
            chapter['type'] = 'MINI'
            intro = open(
                os.path.join(
                    tutorial.get_prod_path(sha),
                    mandata['introduction']),
                "r")
            chapter['intro'] = intro.read()
            intro.close()
            conclu = open(
                os.path.join(
                    tutorial.get_prod_path(sha),
                    mandata['conclusion']),
                "r")
            chapter['conclu'] = conclu.read()
            conclu.close()
            cpt = 1
            for ext in chapter['extracts']:
                ext['position_in_chapter'] = cpt
                ext['path'] = tutorial.get_prod_path(sha)
                text = open(
                    os.path.join(
                        tutorial.get_prod_path(sha),
                        ext['text']),
                    "r")
                ext['txt'] = text.read()
                text.close()
                cpt += 1
        else:
            chapter = None
    else:
        parts = mandata['parts']
        cpt_p = 1
        for part in parts:
            part['tutorial'] = tutorial
            part['path'] = tutorial.get_path()
            part['slug'] = slugify(part['title'])
            part['position_in_tutorial'] = cpt_p
            intro = open(
                os.path.join(
                    tutorial.get_prod_path(sha),
                    part['introduction']),
                "r")
            part['intro'] = intro.read()
            intro.close()
            conclu = open(
                os.path.join(
                    tutorial.get_prod_path(sha),
                    part['conclusion']),
                "r")
            part['conclu'] = conclu.read()
            conclu.close()

            cpt_c = 1
            for chapter in part['chapters']:
                chapter['part'] = part
                chapter['path'] = tutorial.get_path()
                chapter['slug'] = slugify(chapter['title'])
                chapter['type'] = 'BIG'
                chapter['position_in_part'] = cpt_c
                chapter['position_in_tutorial'] = cpt_c * cpt_p
                intro = open(
                    os.path.join(
                        tutorial.get_prod_path(sha),
                        chapter['introduction']),
                    "r")
                chapter['intro'] = intro.read()
                intro.close()
                conclu = open(
                    os.path.join(
                        tutorial.get_prod_path(sha),
                        chapter['conclusion']),
                    "r")
                chapter['conclu'] = conclu.read()
                cpt_e = 1
                for ext in chapter['extracts']:
                    ext['chapter'] = chapter
                    ext['position_in_chapter'] = cpt_e
                    ext['path'] = tutorial.get_path()
                    text = open(
                        os.path.join(
                            tutorial.get_prod_path(sha),
                            ext['text']),
                        "r")
                    ext['txt'] = text.read()
                    text.close()
                    cpt_e += 1
                cpt_c += 1

            cpt_p += 1

    contenu_html = get_template('tutorial/export.md').render(
        Context({
            'chapter': chapter,
            'parts': parts,
            'tutorial': tuto,
        })
    )

    return contenu_html


def get_sep(msg):
    """
    Handle separator for commit msg
    """
    if msg is None or msg.strip() == "":
        return ""
    else:
        return ":"


def get_text_is_empty(msg):
    if msg is None or msg.strip() == "":
        return ""
    else:
        return msg


def move(obj, new_pos, position_f, parent_f, children_fn):
    """Move an object and reorder other objects affected by moving.

    This function need the object, the new position you want the object to go,
    the position field name of the object (eg. 'position_in_chapter'), the
    parent field of the object (eg. 'chapter') and the children function's
    name to apply to parent (eg. 'get_extracts').

    You will still have to save the object once modified.

    Example for extracts :

      move(extract, new_pos, 'position_in_chapter', 'chapter', 'get_extracts')

    """
    old_pos = getattr(obj, position_f)
    objects = getattr(getattr(obj, parent_f), children_fn)()

    # Check that asked new position is correct
    if not 1 <= new_pos <= objects.count():
        raise ValueError(_(u"Impossible de déplacer l'objet en position {0}").format(new_pos))

    increased_pos = new_pos - old_pos > 0

    # Loop on other extracts to move them first
    for obj_mv in objects:
        # If position was increased and obj was between older and new position,
        # lower their position by one
        if increased_pos \
                and old_pos <= getattr(obj_mv, position_f) <= new_pos:
            setattr(obj_mv, position_f, getattr(obj_mv, position_f) - 1)
            obj_mv.save()
        # Otherwise if position was decreased and obj was between newer and old
        # position, increase their position by one
        elif not increased_pos \
                and new_pos <= getattr(obj_mv, position_f) <= old_pos:
            setattr(obj_mv, position_f, getattr(obj_mv, position_f) + 1)
            obj_mv.save()

    # All objects have been updated except the current one we want to move, so
    # we can do it now
    setattr(obj, position_f, new_pos)


def check_json(data, tutorial, zip_file):
    from zds.tutorial.models import Part, Chapter, Extract
    if "title" not in data:
        return False, _(u"Le tutoriel que vous souhaitez importer manque de titre")
    if "type" not in data:
        return False, _(u"Les métadonnées du tutoriel à importer ne nous permettent pas de connaître son type")
    elif tutorial.is_mini():
        if data["type"] == "BIG":
            return False, _(u"Vous essayez d'importer un big tutoriel dans un mini tutoriel")
        elif "chapter" not in data:
            return False, _(u"La structure de vos métadonnées est incohérente")
        elif "extracts" not in data["chapter"]:
            return False, _(u"La structure de vos extraits est incohérente")
        else:
            for extract in data["chapter"]["extracts"]:
                if "pk" not in extract or "title" not in extract or "text" not in extract:
                    return False, _(u"Un de vos extraits est mal renseigné")
                elif not Extract.objects.filter(pk=extract["pk"]).exists():
                    return False, _(u"L'extrait « {} » n'existe pas dans notre base").format(extract["title"])
                elif not Extract.objects.filter(pk=extract["pk"], chapter__tutorial__pk=tutorial.pk).exists():
                    return False, _(u"Vous n'êtes pas autorisé à modifier l'extrait « {} »").format(extract["title"])
                try:
                    zip_file.getinfo(extract["text"])
                except KeyError:
                    return (False,
                            _(u'Le fichier « {} » renseigné dans vos métadonnées '
                              u'pour l\'extrait « {} » ne se trouve pas dans votre zip').format(
                                extract["text"],
                                extract["title"]))
        subs = ["introduction", "conclusion"]
        for sub in subs:
            if sub in data:
                try:
                    zip_file.getinfo(data[sub])
                except KeyError:
                    return (False,
                            _(u'Le fichier « {} » renseigné dans vos métadonnées pour le tutoriel « {} » ne se trouve '
                              u'pas dans votre zip').format(data[sub], data["title"]))
    elif tutorial.is_big():
        if data["type"] == "MINI":
            return False, _(u"Vous essayez d'importer un mini tutoriel dans un big tutoriel")
        elif "parts" not in data:
            return False, _(u"La structure de vos métadonnées est incohérente")
        else:
            for part in data["parts"]:
                if "pk" not in part or "title" not in part:
                    return False, _(u"La structure de vos parties est incohérente")
                elif not Part.objects.filter(pk=part["pk"]).exists():
                    return False, _(u"La partie « {} » n'existe pas dans notre base").format(part["title"])
                elif not Part.objects.filter(pk=part["pk"], tutorial__pk=tutorial.pk).exists():
                    return False, _(u"La partie « {} » n'est pas dans le tutoriel à modifier ").format(part["title"])
                if "chapters" in part:
                    for chapter in part["chapters"]:
                        if "pk" not in chapter or "title" not in chapter:
                            return False, _(u"La structure de vos chapitres est incohérente")
                        elif not Chapter.objects.filter(pk=chapter["pk"]).exists():
                            return False, _(u"Le chapitre « {} » n'existe pas dans notre base").format(chapter["title"])
                        elif not Chapter.objects.filter(pk=chapter["pk"], part__tutorial__pk=tutorial.pk).exists():
                            return False, _(u"Le chapitre « {} » n'est pas dans le tutoriel a modifier").format(
                                chapter["title"])
                        elif "extracts" in chapter:
                            for extract in chapter["extracts"]:
                                if "pk" not in extract or "title" not in extract or "text" not in extract:
                                    return False, _(u"Un de vos extraits est mal renseigné")
                                elif not Extract.objects.filter(pk=extract["pk"]).exists():
                                    return False, _(u"L'extrait « {} » n'existe pas dans notre base").format(
                                        extract["title"])
                                elif not Extract.objects.filter(pk=extract["pk"],
                                                                chapter__part__tutorial__pk=tutorial.pk).exists():
                                    return False, _(u"Vous n'êtes pas autorisé à modifier l'extrait « {} » ").format(
                                        extract["title"])
                                try:
                                    zip_file.getinfo(extract["text"])
                                except KeyError:
                                    return (False,
                                            _(u"Le fichier « {} » renseigné dans vos métadonnées "
                                              u"pour l\'extrait « {} » ne se trouve pas dans votre zip").
                                            format(extract["text"], extract["title"]))
                        subs = ["introduction", "conclusion"]
                        for sub in subs:
                            if sub in chapter:
                                try:
                                    zip_file.getinfo(chapter[sub])
                                except KeyError:
                                    return (False,
                                            _(u'Le fichier « {} » renseigné dans vos métadonnées '
                                              u'pour le chapitre « {} » ne se trouve pas dans votre zip').
                                            format(chapter[sub], chapter["title"]))
                subs = ["introduction", "conclusion"]
                for sub in subs:
                    if sub in part:
                        try:
                            zip_file.getinfo(part[sub])
                        except KeyError:
                            return (False,
                                    _(u'Le fichier « {} » renseigné dans vos métadonnées '
                                      u'pour la partie « {} » ne se trouve pas dans votre zip').format(
                                          part[sub], part["title"]))
        subs = ["introduction", "conclusion"]
        for sub in subs:
            if sub in data:
                try:
                    zip_file.getinfo(data[sub])
                except KeyError:
                    return False, _(u'Le fichier « {} » renseigné dans vos métadonnées pour le tutoriel « {} » ne se '
                                    u'trouve pas dans votre zip').format(data[sub], data["title"])
    return True, None


def import_archive(request):
    from zds.tutorial.models import Tutorial
    import zipfile
    import shutil

    try:
        import ujson as json_reader
    except ImportError:
        try:
            import simplejson as json_reader
        except ImportError:
            import json as json_reader

    archive = request.FILES["file"]
    tutorial = Tutorial.objects.get(pk=request.POST["tutorial"])
    ext = str(archive).split(".")[-1]
    if ext == "zip":
        zfile = zipfile.ZipFile(archive, "a")
        json_here = False
        for i in zfile.namelist():
            ph = i
            if ph == "manifest.json":
                json_data = zfile.read(i)
                mandata = json_reader.loads(json_data)
                ck_zip = zipfile.ZipFile(archive, "r")
                (check, reason) = check_json(mandata, tutorial, ck_zip)
                if not check:
                    return check, reason
                tutorial.title = mandata['title']
                if "description" in mandata:
                    tutorial.description = mandata['description']
                if "introduction" in mandata:
                    tutorial.introduction = mandata['introduction']
                if "conclusion" in mandata:
                    tutorial.conclusion = mandata['conclusion']
                if "licence" in mandata:
                    tutorial.licence = Licence.objects.filter(code=mandata["licence"]).all()[0]
                old_path = tutorial.get_path()
                tutorial.save()
                new_path = tutorial.get_path()
                shutil.move(old_path, new_path)
                json_here = True
                break
        if not json_here:
            return False, _(u"L'archive n'a pas pu être importée car le "
                            u"fichier manifest.json (fichier de métadonnées est introuvable).")

        # init git
        repo = Repo(tutorial.get_path())
        index = repo.index

        # delete old file
        for filename in os.listdir(tutorial.get_path()):
            if not filename.startswith('.'):
                manifest = os.path.join(tutorial.get_path(), filename)
                if os.path.isfile(manifest):
                    os.remove(manifest)
                elif os.path.isdir(manifest):
                    shutil.rmtree(manifest)

        # copy new file
        for i in zfile.namelist():
            ph = i
            if ph != "":
                ph_dest = os.path.join(tutorial.get_path(), ph)
                try:
                    data = zfile.read(i)
                    fp = open(ph_dest, "wb")
                    fp.write(data)
                    fp.close()
                    index.add([ph])
                except IOError:
                    try:
                        os.makedirs(ph_dest)
                    except OSError:
                        pass
        zfile.close()

        # save in git
        msg = _(u"Import du tutoriel")
        aut_user = str(request.user.pk)
        aut_email = str(request.user.email)
        if aut_email is None or aut_email.strip() == "":
            aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['dns'])
        com = index.commit(msg.encode("utf-8"),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email))
        tutorial.sha_draft = com.hexsha
        tutorial.save()
        tutorial.update_children()

        return True, _(u"Le tutoriel {} a été importé avec succès").format(tutorial.title)
    else:
        return False, _(u"L'archive n'a pas pu être importée car elle n'est pas au format zip")
