# coding: utf-8

from difflib import HtmlDiff
from django import template

from git import *

from zds.utils import slugify


register = template.Library()

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
