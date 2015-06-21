try:
    from zds.article.models import Article, ArticleRead, Reaction
    from zds.article.models import Validation as ArticleValidation
    from zds.tutorial.models import Tutorial, Part, Chapter, Note, TutorialRead
    from zds.tutorial.models import Validation as TutorialValidation
    from zds.tutorial.models import Extract as OldExtract
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
from zds.tutorialv2.models.models_versioned import Extract, Container
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


def migrate_mini_tuto():
    mini_tutos = Tutorial.objects.prefetch_related("licence").filter(type="MINI").all()
    for i in progressbar(xrange(len(mini_tutos)), "Exporting mini tuto", 100):
        current = mini_tutos[i]
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

        for extract in OldExtract.objects.filter(chapter=current.get_chapter()):
            minituto_extract = Extract(extract.title, slugify(extract.title))
            minituto_extract.text = extract.text
            versioned.add_extract(minituto_extract, generate_slug=True)
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


def migrate_big_tuto():
    big_tutos = Tutorial.objects.prefetch_related("licence").filter(type="BIG").all()
    for i in progressbar(xrange(len(big_tutos)), "Exporting big tutos", 100):
        current = big_tutos[i]
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
        exported.old_pk = current.pk
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

        # todo: handle publication, notes etc.
    reacts = Note.objects.filter(tutorial__pk=current.pk)\
        .select_related("author")\
        .order_by("pubdate")\
        .all()
    export_comments(reacts, exported, TutorialRead)
    migrate_validation(exported, TutorialValidation.objects.filter(tutorial=current))
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
        migrate_mini_tuto()
        migrate_big_tuto()
