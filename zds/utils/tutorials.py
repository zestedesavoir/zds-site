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

    if tutorial.is_mini:
        # We export the chapter without its empty title if mini tutorial
        try :
            chapter = Chapter.objects.get(tutorial__pk=tutorial.pk)
            dct['chapter'] = export_chapter(chapter, export_all=False)
        except Chapter.DoesNotExist:
            chapter = None
    else:
        dct['parts'] = []
        parts = Part.objects\
            .filter(tutorial=tutorial)\
            .order_by('position_in_tutorial')
        for part in parts:
            dct['parts'].append(export_part(part))

    return dct
