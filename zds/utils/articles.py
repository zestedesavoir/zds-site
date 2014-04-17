# coding: utf-8

from collections import OrderedDict

from git import *


# Export-to-dict functions
def export_article(article):
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
        if os.path.abspath(bl.path)==os.path.abspath(chemin):
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