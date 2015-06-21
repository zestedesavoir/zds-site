try:
    from zds.article.models import Article, ArticleRead, Reaction
    from zds.article.models import Validation as ArticleValidation
    from zds.tutorial.models import Tutorial, Note, TutorialRead
    from zds.tutorial.models import Validation as TutorialValidation
except ImportError:
    print("The old stack is no more available on your zestedesavoir copy")
    exit()

import os
import shutil
import sys

from zds.forum.models import Topic
from django.conf import settings

from zds.tutorialv2.models.models_database import PublishableContent, ContentReaction, ContentRead, PublishedContent,\
    Validation

from zds.tutorialv2.utils import publish_content
from django.core.management.base import BaseCommand
from django.db import transaction
from zds.gallery.models import Gallery, UserGallery, Image
from zds.utils import slugify
from zds.utils.models import Licence, CommentLike, CommentDislike
from datetime import datetime

from easy_thumbnails.exceptions import InvalidImageFormatError


def export_read_for_note(old_note, new_note, read_class):
    queryset = read_class.objects
    if read_class == ArticleRead:
        queryset = queryset.filter(reaction__pk=old_note.pk)
    else:
        queryset = queryset.filter(note__pk=old_note.pk)
    for read in queryset.all():
        new_read = ContentRead()
        new_read.content = new_note.related_content
        new_read.note = new_note
        new_read.user = read.user
        new_read.save()


def migrate_validation(exported_content, validation_queryset):

    for old_validation in validation_queryset.all():
        exported_validation = Validation(content=exported_content,
                                         version=old_validation.version,
                                         comment_authors=old_validation.comment_authors,
                                         comment_validator=old_validation.comment_validator,
                                         status=old_validation.status,
                                         validator=old_validation.validator,
                                         date_proposition=old_validation.date_proposition,
                                         date_validation=old_validation.date_validation,
                                         date_reserve=old_validation.date_reserve)
        exported_validation.save()


def export_comments(reacts, exported, read_class):
    c = 0
    for note in reacts:
        new_reac = ContentReaction()
        new_reac.pubdate = note.pubdate
        new_reac.author = note.author
        c += 1
        new_reac.position = c
        new_reac.related_content = exported

        new_reac.update_content(note.text)
        new_reac.ip_address = note.ip_address
        new_reac.like = note.like
        new_reac.dislike = note.dislike
        new_reac.save()

        export_read_for_note(note, new_reac, read_class)
        exported.last_note = new_reac
        for like in CommentLike.objects.filter(comments__pk=note.pk).all():
            like.comments = new_reac
            like.save()
        for dislike in CommentDislike.objects.filter(comments__pk=note.pk).all():
            dislike.comments = new_reac
            dislike.save()
        exported.save()


def progressbar(it, prefix="", size=60):
    count = len(it)

    def _show(_i):
        x = int(size * _i / count)
        sys.stdout.write("%s[%s%s] %i/%i\r" % (prefix, "#" * x, "." * (size - x), _i, count))
        sys.stdout.flush()

    _show(0)
    for i, item in enumerate(it):
        yield item
        _show(i + 1)
    sys.stdout.write("\n")
    sys.stdout.flush()


def create_gallery_for_article(content):
    # Creating the gallery
    gal = Gallery()
    gal.title = content.title
    gal.slug = slugify(content.title)
    gal.pubdate = datetime.now()
    gal.save()

    # Attach user to gallery
    for user in content.authors.all():
        userg = UserGallery()
        userg.gallery = gal
        userg.mode = "W"  # write mode
        userg.user = user
        userg.save()
    content.gallery = gal

    return gal


def split_article_in_extracts(article):
    """Split a text into extracts according to titles (create a new extract if level 1, remove a level otherwise)

    Note that this function generate no commit

    :param article: An article
    :type article: VersionedContent
    """

    txt = article.children[0].get_text()
    article.children[0].repo_delete(do_commit=False)  # remove old extract

    extracts = []

    extract_text = ''
    extract_title = ''
    in_code = False

    # split
    for line in txt.split('\n'):
        if line[:3] == '```':
            in_code = not in_code

        if not in_code and line[0] == '#':
            title_level = 0

            for a in line:
                if a != '#':
                    break
                else:
                    title_level += 1

            title_content = line[title_level:].strip()  # get text right after the `#`

            if title_level == 1 and title_content != '':
                extracts.append((extract_title, extract_text))
                extract_title = title_content
                extract_text = u''
            else:
                line = ''.join(['#' for i in range(title_level-1)]) + ' ' + title_content
                extract_text += line + '\n'

        else:
            extract_text += line + '\n'

    # add last
    extracts.append((extract_title, extract_text))

    # create extracts
    for num, definition in enumerate(extracts):
        title, text = definition
        if num == 0:
            article.repo_update(article.title, text, '', do_commit=False)
        else:
            article.repo_add_extract(title, text, do_commit=False)


def migrate_articles():
    articles = Article.objects.all()
    if len(articles) == 0:
        return
    for i in progressbar(xrange(len(articles)), "Exporting articles", 100):
        current = articles[i]
        if not os.path.exists(current.get_path(False)):
            print(u'Le chemin physique vers {} n\'existe plus.'.format(current.get_path(False)))
            continue
        exported = PublishableContent()
        exported.slug = current.slug
        exported.type = "ARTICLE"
        exported.title = current.title
        exported.creation_date = current.create_at
        exported.description = current.description
        exported.sha_draft = current.sha_draft
        exported.licence = current.licence
        exported.js_support = current.js_support  # todo: check articles have js_support

        exported.save()  # before updating `ManyToMany` relation, we need to save !

        [exported.authors.add(author) for author in current.authors.all()]
        new_gallery = create_gallery_for_article(exported)

        if current.image:
            # migrate image using `Image()`
            try:
                path_to_image = current.image['article_illu'].url
            except InvalidImageFormatError:
                pass
            else:
                img = Image()
                img.physical = os.path.join(settings.BASE_DIR, path_to_image)
                img.gallery = new_gallery
                img.title = path_to_image
                img.slug = slugify(path_to_image)
                img.pubdate = datetime.now()
                img.save()
                exported.image = img

        # todo: migrate categories !!
        shutil.copytree(current.get_path(False), exported.get_repo_path(False))
        # now, re create the manifest.json
        versioned = exported.load_version()
        versioned.type = "ARTICLE"

        if exported.licence:
            versioned.licence = exported.licence

        split_article_in_extracts(versioned)  # create extracts from text

        versioned.dump_json()
        exported.sha_draft = versioned.commit_changes(u"Migration version 2")
        exported.old_pk = current.pk
        exported.save()
        # todo  : generate mapping
        # todo: handle notes
        reacts = Reaction.objects.filter(article__pk=current.pk)\
                                 .select_related("author")\
                                 .order_by("pubdate")\
                                 .all()
        export_comments(reacts, exported, ArticleRead)
        migrate_validation(exported, ArticleValidation.objects.filter(article=current))
        # todo: handle publication
        if current.sha_public is not None and current.sha_public != "":
            # set mapping
            map_previous = PublishedContent()
            map_previous.content_public_slug = current.slug
            map_previous.content_pk = current.pk
            map_previous.content_type = 'ARTICLE'
            map_previous.must_redirect = True  # will send HTTP 301 if visited !
            map_previous.content = exported
            map_previous.save()

            # publish the article !
            published = publish_content(exported, exported.load_version(current.sha_public), False)
            exported.pubdate = current.pubdate
            exported.sha_public = current.sha_public
            exported.public_version = published
            exported.save()
            published.content_public_slug = current.slug
            published.publication_date = current.pubdate
            published.save()


def migrate_tuto(tutos, title="Exporting mini tuto"):
    for i in progressbar(xrange(len(tutos)), title, 100):
        current = tutos[i]
        if not os.path.exists(current.get_path(False)):
            print(u'Le chemin physique vers {} n\'existe plus.'.format(current.get_path(False)))
            continue
        exported = PublishableContent()
        exported.slug = current.slug
        exported.type = "TUTORIAL"
        exported.title = current.title
        exported.sha_draft = current.sha_draft
        exported.licence = Licence.objects.filter(code=current.licence).first()

        exported.creation_date = current.create_at
        exported.image = current.image
        exported.description = current.description
        exported.js_support = current.js_support
        exported.save()
        [exported.subcategory.add(category) for category in current.subcategory.all()]
        [exported.helps.add(help) for help in current.helps.all()]
        [exported.authors.add(author) for author in current.authors.all()]
        shutil.copytree(current.get_path(False), exported.get_repo_path(False))
        # now, re create the manifest.json
        versioned = exported.load_version()
        versioned.licence = exported.licence
        exported.gallery = current.gallery

        versioned.type = "TUTORIAL"
        versioned.dump_json()

        exported.sha_draft = versioned.commit_changes(u"Migration version 2")
        if current.in_beta():
            exported.sha_beta = exported.sha_draft
            exported.beta_topic = Topic.objects.get(key=current.pk).first()

        exported.old_pk = current.pk
        exported.save()
        # export beta forum post
        former_topic = Topic.objects.filter(key=current.pk).first()
        if former_topic is not None:
            former_topic.related_publishable_content = exported
            former_topic.save()
            former_first_post = former_topic.first_post()
            text = former_first_post.text
            text = text.replace(current.get_absolute_url_beta(), exported.get_absolute_url_beta())
            former_first_post.update_content(text)
            former_first_post.save()
        # extract notes
        reacts = Note.objects.filter(tutorial__pk=current.pk)\
                             .select_related("author")\
                             .order_by("pubdate")\
                             .all()
        migrate_validation(exported, TutorialValidation.objects.filter(tutorial=current))
        export_comments(reacts, exported, TutorialRead)
        if current.sha_public is not None and current.sha_public != "":
            published = publish_content(exported, exported.load_version(current.sha_public), False)
            exported.pubdate = current.pubdate
            exported.sha_public = current.sha_public
            exported.public_version = published
            exported.save()
            exported.public_version.content_public_slug = current.slug
            exported.public_version.publication_date = current.pubdate

            exported.public_version.save()
            # set mapping
            map_previous = PublishedContent()
            map_previous.content_public_slug = current.slug
            map_previous.content_pk = current.pk
            map_previous.content_type = 'TUTORIAL'
            map_previous.must_redirect = True  # will send HTTP 301 if visited !
            map_previous.content = exported
            map_previous.save()


@transaction.atomic
class Command(BaseCommand):
    help = 'Migrate old tutorial and article stack to ZEP 12 stack (tutorialv2)'

    def handle(self, *args, **options):
        migrate_articles()
        migrate_tuto(Tutorial.objects.prefetch_related("licence").filter(type="MINI").all())
        migrate_tuto(Tutorial.objects.prefetch_related("licence").filter(type="BIG").all(), "Exporting big tutos")
