# coding: utf-8

from collections import OrderedDict
import os

from zds.utils import slugify
from git import *

# Export-to-dict functions
def export_article(article):
    from zds.article.models import Article
    '''
    Export an article to a dict
    '''
    dct = OrderedDict()
    dct['title'] = article.title
    dct['description'] = article.description
    dct['type'] = 'article'
    dct['text'] = article.text

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