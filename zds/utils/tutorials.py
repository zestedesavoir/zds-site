# coding: utf-8

from collections import OrderedDict
import os

from zds.utils import slugify


# Export-to-dict functions

def export_chapter(chapter, export_all=True):
    from zds.tutorial.models import Extract
    '''
    Export a chapter to a dict
    '''
    dct = OrderedDict()
    if export_all:
        dct['title'] = chapter.title
        dct['introduction'] = os.path.join(chapter.get_path(relative=True),'introduction.md')
        dct['conclusion'] = os.path.join(chapter.get_path(relative=True),'conclusion.md')
    dct['extracts'] = []

    extracts = Extract.objects.filter(chapter=chapter)\
        .order_by('position_in_chapter')

    for extract in extracts:
        extract_dct = OrderedDict()
        extract_dct['title'] = extract.title
        extract_dct['text'] = os.path.join(chapter.get_path(relative=True), slugify(extract.title))
        dct['extracts'].append(extract_dct)

    return dct


def export_part(part):
    from zds.tutorial.models import Chapter
    '''
    Export a part to a dict
    '''
    dct = OrderedDict()
    dct['title'] = part.title
    dct['introduction'] = os.path.join(part.get_path(relative=True),'introduction.md')
    dct['conclusion'] = os.path.join(part.get_path(relative=True),'conclusion.md')
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
    dct['introduction'] = os.path.join(tutorial.get_path(relative=True),'introduction.md')
    dct['conclusion'] = os.path.join(tutorial.get_path(relative=True),'conclusion.md')

    if tutorial.is_mini:
        # We export the chapter without its empty title if mini tutorial
        chapter = Chapter.objects.get(tutorial=tutorial)
        dct['chapter'] = export_chapter(chapter, export_all=False)
    else:
        dct['parts'] = []
        parts = Part.objects\
            .filter(tutorial=tutorial)\
            .order_by('position_in_tutorial')
        for part in parts:
            dct['parts'].append(export_part(part))

    return dct
