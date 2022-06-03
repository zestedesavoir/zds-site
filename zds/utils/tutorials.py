import os


def get_blob(tree, chemin):
    for blob in tree.blobs:
        try:
            if os.path.abspath(blob.path) == os.path.abspath(chemin):
                data = blob.data_stream.read()
                return data.decode("utf-8")
        except OSError:
            return ""
    if len(tree.trees) > 0:
        for atree in tree.trees:
            result = get_blob(atree, chemin)
            if result is not None:
                return result
        return None
    else:
        return None
