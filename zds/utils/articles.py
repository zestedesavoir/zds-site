# coding: utf-8

from collections import OrderedDict

import os


# Export-to-dict functions
def export_article(article):
    """Export an article to a dict."""
    # TODO: Thank you, Captain Obvious... WHY this export?!
    dct = OrderedDict()
    dct['title'] = article.title
    dct['description'] = article.description
    dct['type'] = 'article'
    dct['text'] = article.text
    if article.licence:
        dct['licence'] = article.licence.code

    return dct


def get_blob(tree, chemin):

    for blob in tree.blobs:
        if os.path.abspath(blob.path) == os.path.abspath(chemin):
            data = blob.data_stream.read()
            return data.decode('utf-8')
    if len(tree.trees) > 0:
        for tree_elem in tree.trees:
            result = get_blob(tree_elem, chemin)
            if result is not None:
                return result
        return None
    else:
        return None
