# coding: utf-8

from difflib import HtmlDiff
from django import template

from git import *

from zds.utils import slugify


register = template.Library()


@register.filter('repo_tuto')
def repo_tuto(tutorial, sha=None):
    if sha is None:

        return {'introduction': tutorial.get_introduction(),
                'conclusion': tutorial.get_conclusion()}
    else:
        repo = Repo(tutorial.get_path())
        bls = repo.commit(sha).tree.blobs
        for bl in bls:
            if bl.path == 'introduction.md':
                intro = bl.data_stream.read()
            if bl.path == 'conclusion.md':
                conclu = bl.data_stream.read()

        return {
            'introduction': intro.decode('utf-8'),
            'conclusion': conclu.decode('utf-8')}


@register.filter('repo_part')
def repo_part(part, sha=None):
    if sha is None:
        return {'introduction': part.get_introduction(),
                'conclusion': part.get_conclusion()}
    else:
        repo = Repo(part['path'])
        bls = repo.commit(sha).tree.blobs
        for bl in bls:
            if bl.path == 'introduction.md':
                intro = bl.data_stream.read()
            if bl.path == 'conclusion.md':
                conclu = bl.data_stream.read()

        return {
            'introduction': intro.decode('utf-8'),
            'conclusion': conclu.decode('utf-8')}


@register.filter('repo_chapter')
def repo_chapter(chapter, sha=None):
    if sha is None:
        return {'introduction': chapter.get_introduction(),
                'conclusion': chapter.get_conclusion()}
    else:
        repo = Repo(chapter['path'])
        if chapter['type'] == 'MINI':
            return {'introduction': None, 'conclusion': None}
        else:
            bls = repo.commit(sha).tree.blobs
            for bl in bls:
                if bl.path == 'introduction.md':
                    intro = bl.data_stream.read()
                if bl.path == 'conclusion.md':
                    conclu = bl.data_stream.read()
            return {
                'introduction': intro.decode('utf-8'),
                'conclusion': conclu.decode('utf-8')}


@register.filter('repo_extract')
def repo_extract(extract, sha=None):
    if sha is None:
        return {'text': extract.get_text()}
    else:
        repo_e = Repo(extract['path'])
        bls_e = repo_e.commit(sha).tree.blobs

        for bl in bls_e:
            if bl.path == slugify(extract['title']) + '.md':
                text = bl.data_stream.read()
                return {'text': text.decode('utf-8')}
    return {'text': ''}


@register.filter('repo_blob')
def repo_blob(blob):
    contenu = blob.data_stream.read()

    return contenu.decode('utf-8')


@register.filter('diff_text')
def diff_text(text1, text2="", title1="", title2=""):
    txt1 = text1.splitlines(1)
    txt2 = text2.splitlines(1)

    d = HtmlDiff()
    result = d.make_file(txt1, txt2, title1, title2, context=True)

    return result
