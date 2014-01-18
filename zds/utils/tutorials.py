# coding: utf-8

from collections import OrderedDict
from django.template.loader import get_template
import os

from git import *
from zds.utils import slugify
from django.template import Context

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
        try :
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
        if bl.path==chemin:
            data = bl.data_stream.read()
            return data.decode('utf-8')
    if len(tree.trees) > 0:
        for tr in tree.trees:
            result = get_blob(tr, chemin)
            if result != None:
                return result
        return None
    else:
        return None

def export_tutorial_to_html(tutorial):
    # Two variables to handle two distinct cases (large/small tutorial)
    chapter = None
    parts = None
    tuto = OrderedDict()
    
    i = open(os.path.join(tutorial.get_prod_path(), tutorial.introduction), "r")
    i_contenu = i.read()
    i.close()
    tuto['intro'] = i_contenu.decode('utf-8')

    c = open(os.path.join(tutorial.get_prod_path(), tutorial.conclusion), "r")
    c_contenu = c.read()
    c.close()
    tuto['conclu'] = c_contenu.decode('utf-8')
    tuto['image'] = tutorial.image
    tuto['is_mini'] = tutorial.is_mini()
    tuto['authors'] = tutorial.authors
    tuto['subcategory'] = tutorial.subcategory
    tuto['pk'] = tutorial.pk
    tuto['slug'] = tutorial.slug
     
    #find the good manifest file
    mandata = tutorial.load_json(online=True)
    
    # If it's a small tutorial, fetch its chapter
    if tutorial.type == 'MINI':
        if 'chapter' in mandata:
            chapter = mandata['chapter']
            chapter['path'] = tutorial.get_prod_path()
            chapter['type'] = 'MINI'
            intro = open(os.path.join(tutorial.get_prod_path(), mandata['introduction']), "r")
            chapter['intro'] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(), mandata['conclusion']), "r")
            chapter['conclu'] = conclu.read()
            conclu.close()
            cpt=1
            for ext in chapter['extracts'] :
                ext['position_in_chapter'] = cpt
                ext['path'] = tutorial.get_prod_path()
                text = open(os.path.join(tutorial.get_prod_path(), ext['text']), "r")
                ext['txt'] = text.read()
                text.close()
                cpt+=1
        else:
            chapter = None
    else:
        parts = mandata['parts']
        cpt_p=1
        for part in parts :
            part['tutorial'] = tutorial
            part['path'] = tutorial.get_path()
            part['slug'] = slugify(part['title'])
            part['position_in_tutorial'] = cpt_p
            intro = open(os.path.join(tutorial.get_prod_path(), part['introduction']), "r")
            part['intro'] = intro.read()
            intro.close()
            conclu = open(os.path.join(tutorial.get_prod_path(), part['conclusion']), "r")
            part['conclu'] = conclu.read()
            conclu.close()

            cpt_c=1
            for chapter in part['chapters'] :
                chapter['part'] = part
                chapter['path'] = tutorial.get_path()
                chapter['slug'] = slugify(chapter['title'])
                chapter['type'] = 'BIG'
                chapter['position_in_part'] = cpt_c
                chapter['position_in_tutorial'] = cpt_c * cpt_p
                intro = open(os.path.join(tutorial.get_prod_path(), chapter['introduction']), "r")
                chapter['intro'] = intro.read()
                intro.close()
                conclu = open(os.path.join(tutorial.get_prod_path(), chapter['conclusion']), "r")
                chapter['conclu'] = conclu.read()
                cpt_e=1
                for ext in chapter['extracts'] :
                    ext['chapter'] = chapter
                    ext['position_in_chapter'] = cpt_e
                    ext['path'] = tutorial.get_path()
                    text = open(os.path.join(tutorial.get_prod_path(), ext['text']), "r")
                    ext['txt'] = text.read()
                    text.close()
                    cpt_e+=1
                cpt_c+=1
                
            cpt_p+=1
    
    contenu_html = get_template('tutorial/export.md').render(
                            Context({
                                'chapter': chapter,
                                'parts': parts,
                                'tutorial': tuto,
                            })
                        )
    
    return contenu_html