# coding: utf-8

from collections import OrderedDict
from datetime import datetime
import os
from django.template import Context
from django.template.loader import get_template
from git import *
from django.core.urlresolvers import reverse
try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader
import json as json_writer

from zds.utils import slugify

BIG_STRUCTURE = ['parts','chapters','extracts']
MINI_STRUCTURE = ['chapter','extracts']

# Export-to-dict functions
def export_chapter(chapter, export_all=True):
    from zds.tutorial.models import Extract
    '''
    Export a chapter to a dict
    '''
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
    '''
    Export a part to a dict
    '''
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
    '''
    Export a tutorial to a dict
    '''
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
            chapter = None
    else:
        dct['parts'] = []
        parts = Part.objects\
            .filter(tutorial__pk=tutorial.pk)\
            .order_by('position_in_tutorial')
        for part in parts:
            dct['parts'].append(export_part(part))

    return dct


def get_blob(tree, chemin):
    for bl in tree.blobs:
        try:
            if os.path.abspath(bl.path) == os.path.abspath(chemin):
                data = bl.data_stream.read()
                return data.decode('utf-8')
        except:
            return ""
    if len(tree.trees) > 0:
        for tr in tree.trees:
            result = get_blob(tr, chemin)
            if result is not None:
                return result
        return None
    else:
        return None


def export_tutorial_to_md(tutorial, sha):
    # Two variables to handle two distinct cases (large/small tutorial)
    chapter = None
    parts = None
    tuto = OrderedDict()

    i = open(
        os.path.join(
            tutorial.get_prod_path(),
            tutorial.introduction),
        "r")
    i_contenu = i.read()
    i.close()
    tuto['intro'] = i_contenu

    c = open(os.path.join(tutorial.get_prod_path(), tutorial.conclusion), "r")
    c_contenu = c.read()
    c.close()
    tuto['conclu'] = c_contenu

    tuto['image'] = tutorial.image
    tuto['title'] = tutorial.title
    tuto['is_mini'] = tutorial.is_mini()
    tuto['authors'] = tutorial.authors
    tuto['subcategory'] = tutorial.subcategory
    tuto['pubdate'] = datetime.now()

    tuto['pk'] = tutorial.pk
    tuto['slug'] = tutorial.slug

    # find the good manifest file
    mandata = tutorial.load_json(sha=sha)

    # If it's a small tutorial, fetch its chapter
    if tutorial.type == 'MINI':
        if 'chapter' in mandata:
            chapter = mandata['chapter']
            chapter['path'] = tutorial.get_prod_path()
            chapter['type'] = 'MINI'
            intro = open(
                os.path.join(
                    tutorial.get_prod_path(),
                    mandata['introduction']),
                "r")
            chapter['intro'] = intro.read()
            intro.close()
            conclu = open(
                os.path.join(
                    tutorial.get_prod_path(),
                    mandata['conclusion']),
                "r")
            chapter['conclu'] = conclu.read()
            conclu.close()
            cpt = 1
            for ext in chapter['extracts']:
                ext['position_in_chapter'] = cpt
                ext['path'] = tutorial.get_prod_path()
                text = open(
                    os.path.join(
                        tutorial.get_prod_path(),
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
                    tutorial.get_prod_path(),
                    part['introduction']),
                "r")
            part['intro'] = intro.read()
            intro.close()
            conclu = open(
                os.path.join(
                    tutorial.get_prod_path(),
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
                        tutorial.get_prod_path(),
                        chapter['introduction']),
                    "r")
                chapter['intro'] = intro.read()
                intro.close()
                conclu = open(
                    os.path.join(
                        tutorial.get_prod_path(),
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
                            tutorial.get_prod_path(),
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
        raise ValueError('Can\'t move object to position {0}'.format(new_pos))

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

def read_tree(tree, level, target_level, target_value, target_leaf, structure):
    """
    Recursive function which returns content of tree depending on the type of tree
    """
    
    if level == None:
        if target_level in tree:
            return tree[target_leaf]
    if level in tree:
        for elt in tree[level]:    

            if level==target_level:
                if elt["pk"] == target_value:
                    return elt[target_leaf]
            else:
                l = structure.index(level)
                if len(structure) > l+1:
                    next_level = structure[l+1]
                    final_path = read_tree(elt, next_level, target_level, target_value, target_leaf, structure)
                    if final_path is not None:
                        return final_path
                else:
                    return None
    return None
    
def get_content(obj_top, level, obj_level, path_obj_fn, type, sha=None):
    """
    Returns type of content related to commit hash
    By default, if the hash commit is not specified,
    considering that this is the hash commit of draft version. 
    
    obj_top : means the highest in the hierarchy queryset object (often tutorial)
    level : means starting json attribute from the top
    obj_level : means object which are analyse
    path_obj_fn : function which give path of obj_top
    type : means type of content, like "introduction", "conclusion" or "text"
    sha : means hash commit of the content

    Example for get introduction of chapter:
    
    get_content(obj_top=tutorial,
                level="chapter",
                obj_level=chapter,
                path_obj_fn="get_path",
                type="introduction",
                sha=sha)
    """

    # find hash code
    if sha is None:
        sha = getattr(obj_top, "sha_draft")
    repo = Repo(getattr(obj_top, path_obj_fn)())

    if getattr(obj_top, "is_mini")():
        structure = MINI_STRUCTURE
    else:
        structure = BIG_STRUCTURE

    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    tutorial_version = json_reader.loads(manifest)
    
    if level == "tutorial":
        path = read_tree(tutorial_version,
                         level = None,
                         target_level = type,
                         target_value = None,
                         target_leaf = type,
                         structure=structure)
    elif level == "part":
        path = read_tree(tutorial_version,
                         level = "parts",
                         target_level = "parts",
                         target_value = getattr(obj_level, "pk"),
                         target_leaf = type,
                         structure = structure)
    elif level == "chapter":
        if not getattr(obj_top, "is_mini")():
            path = read_tree(tutorial_version,
                             level = "parts",
                             target_level = "chapters",
                             target_value = getattr(obj_level, "pk"),
                             target_leaf = type,
                             structure = structure)
        else:
            path = read_tree(tutorial_version,
                             level = "chapter",
                             target_level = "chapter",
                             target_value = getattr(obj_level, "pk"),
                             target_leaf = type,
                             structure = structure)
    else:
        if not getattr(obj_top, "is_mini")():
            path = read_tree(tutorial_version,
                             level = "parts",
                             target_level = "extracts",
                             target_value = getattr(obj_level, "pk"),
                             target_leaf = type,
                             structure = structure)
        else:
            path = read_tree(tutorial_version,
                             level = "chapter",
                             target_level = "extracts",
                             target_value = getattr(obj_level, "pk"),
                             target_leaf = type,
                             structure = structure)
    if path:
        return get_blob(repo.commit(sha).tree, path)        
    else:
        return None

def load_data_part(tutorial, man_level):
        
        man_level["tutorial"] = tutorial
        man_level["path"] = tutorial["get_path"]
        man_level["slug"] = slugify(man_level['title'])
        if tutorial["is_big"]:
            man_level["type"] = "BIG"
        else:
            man_level["type"] = "MINI"
        
        man_level["get_absolute_url"] = reverse(
            "zds.tutorial.views.view_part",
            args=[
                tutorial["pk"],
                tutorial["slug"],
                man_level["pk"],
                man_level["slug"]])

        if tutorial["on_line"]:
            man_level["get_absolute_url_online"] = reverse(
                "zds.tutorial.views.view_part_online",
                args=[
                    tutorial["pk"],
                    tutorial["slug"],
                    man_level["pk"],
                    man_level["slug"]])
        return man_level

def load_data_chapter(part, man_level):
        
        man_level["part"] = part
        man_level["path"] = part["path"]
        man_level["type"] = part["type"]
        man_level["slug"] = slugify(man_level['title'])
        man_level["get_absolute_url"] = part["get_absolute_url"] \
                + "{0}/{1}/".format(man_level["pk"], man_level["slug"])
        if part["tutorial"]["on_line"]:
            man_level["get_absolute_url_online"] = part["get_absolute_url_online"] \
            + "{0}/{1}/".format(man_level["pk"], man_level["slug"])
        
        return man_level

def load_data_extract(chapter, man_level):
        
        man_level["chapter"] = chapter
        man_level["path"] = chapter["path"]
        man_level["type"] = chapter["type"]
        man_level["slug"] = slugify(man_level['title'])
        
        return man_level