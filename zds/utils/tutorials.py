import os


# Used for indexing tutorials, we need to parse each manifest to know which content have been published
class GetPublished:

    published_part = []
    published_chapter = []
    published_extract = []

    def __init__(self):
        pass

    @classmethod
    def get_published_content(cls):
        # If all array are empty load_it
        if not len(GetPublished.published_part) and \
           not len(GetPublished.published_chapter) and \
           not len(GetPublished.published_extract):

            # Get all published tutorials
            from zds.tutorial.models import Tutorial
            tutorials_database = Tutorial.objects.filter(sha_public__isnull=False).all()

            for tutorial in tutorials_database:
                # Load Manifest
                json = tutorial.load_json_for_public()

                # Parse it
                GetPublished.load_tutorial(json)

        return {'parts': GetPublished.published_part,
                'chapters': GetPublished.published_chapter,
                'extracts': GetPublished.published_extract}

    @classmethod
    def load_tutorial(cls, json):
        # Load parts, chapter and extract
        if 'parts' in json:
            for part_json in json['parts']:

                # If inside of parts we have chapters, load it
                GetPublished.load_chapters(part_json)
                GetPublished.load_extracts(part_json)

                GetPublished.published_part.append(part_json['pk'])

        GetPublished.load_chapters(json)
        GetPublished.load_extracts(json)

    @classmethod
    def load_chapters(cls, json):
        if 'chapters' in json:
            for chapters_json in json['chapters']:

                GetPublished.published_chapter.append(chapters_json['pk'])
                GetPublished.load_extracts(chapters_json)

        return GetPublished.published_chapter

    @classmethod
    def load_extracts(cls, json):
        if 'extracts' in json:
            for extract_json in json['extracts']:
                GetPublished.published_extract.append(extract_json['pk'])

        return GetPublished.published_extract


def get_blob(tree, chemin):
    for blob in tree.blobs:
        try:
            if os.path.abspath(blob.path) == os.path.abspath(chemin):
                data = blob.data_stream.read()
                return data.decode('utf-8')
        except OSError:
            return ''
    if len(tree.trees) > 0:
        for atree in tree.trees:
            result = get_blob(atree, chemin)
            if result is not None:
                return result
        return None
    else:
        return None
