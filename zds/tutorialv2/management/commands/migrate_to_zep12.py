# coding: utf-8

try:
    from zds.article.models import Article, ArticleRead, Reaction
    from zds.article.models import Validation as ArticleValidation
    from zds.tutorial.models import Tutorial, Note, TutorialRead
    from zds.tutorial.models import Validation as TutorialValidation
except ImportError:
    print("The old stack is no more available on your zestedesavoir copy")
    exit()

import os
from os.path import join as file_join
from os.path import exists as file_exists
import shutil
import sys
from bs4 import BeautifulSoup as bs

from zds.forum.models import Topic
from zds.utils.templatetags.emarkdown import emarkdown_inline

from zds.tutorialv2.models.models_database import PublishableContent, ContentReaction, ContentRead, PublishedContent,\
    Validation

from zds.tutorialv2.utils import publish_content
from django.core.management.base import BaseCommand
from django.db import transaction
from zds.gallery.models import Gallery, UserGallery, Image
from zds.utils import slugify
from zds.utils.models import CommentLike, CommentDislike
from datetime import datetime

from easy_thumbnails.exceptions import InvalidImageFormatError
from zds.settings import MEDIA_ROOT
from git import Repo, InvalidGitRepositoryError


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


def export_comments(reacts, exported, read_class, old_last_note_pk):
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

        # because there is an `auto_now_add=True` on zds.utils.models.Comment.pubdate, we need to update those fields
        # after the first `save()`
        new_reac.pubdate = note.pubdate
        new_reac.update = note.update
        new_reac.save()

        export_read_for_note(note, new_reac, read_class)
        if note.pk == old_last_note_pk:
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

    if not os.path.exists(gal.get_gallery_path()):
        os.makedirs(gal.get_gallery_path())

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

    extract_text = u''
    extract_title = u''
    in_code = False

    # split
    for line in txt.split('\n'):
        if line[:3] == '```':
            in_code = not in_code

        if not len(line) == 0 and not in_code and line[0] == '#':
            title_level = 0

            for a in line:
                if a != '#':
                    break
                else:
                    title_level += 1

            title_content = line[title_level:].strip()  # get text right after the `#`
            title_content = bs(emarkdown_inline(title_content)).getText()  # remove markdown formatting !

            if title_level == 1 and title_content != '':
                extracts.append((extract_title, extract_text))
                extract_title = title_content
                extract_text = u''
            else:
                line = u''.join([u'#' for i in range(title_level - 1)]) + u' ' + title_content
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


def copy_and_clean_repo(path_from, path_to):
    """Try to clean the repository from old errors made in the past by previous code, then clone it to the new location

    :param path_from: old repository
    :param path_to: new repository
    :return: sha of the commit if a clean up has been done, `None` otherwise
    """

    old_repo = Repo(path_from)

    # look for files that are still in git but deleted in "real life"
    to_delete = []
    for entry in old_repo.index.entries:
        rel_path = entry[0]
        abs_path = os.path.join(path_from, rel_path)
        if not os.path.exists(abs_path):
            to_delete.append(rel_path)

    # clean up
    sha = None

    if len(to_delete) != 0:
        old_repo.index.remove(to_delete)
        sha = old_repo.index.commit('Nettoyage pré-migratoire')

    # then clone it to new repo
    old_repo.clone(path_to)

    return sha


def migrate_articles():
    articles = Article.objects.all()

    if len(articles) == 0:
        return
    for i in progressbar(xrange(len(articles)), "Exporting articles", 100):
        current = articles[i]
        if not os.path.exists(current.get_path(False)):
            sys.stderr.write('Invalid physical path to repository « {} », skipping\n'.format(current.get_path(False)))
            continue

        exported = PublishableContent()
        exported.slug = current.slug
        exported.type = "ARTICLE"
        exported.title = current.title
        exported.creation_date = current.create_at
        exported.description = current.description
        exported.sha_draft = current.sha_draft
        exported.sha_validation = current.sha_validation
        exported.licence = current.licence
        exported.js_support = current.js_support
        exported.pubdate = current.pubdate
        exported.save()  # before updating `ManyToMany` relation, we need to save !

        try:
            clean_commit = copy_and_clean_repo(current.get_path(False), exported.get_repo_path(False))
        except InvalidGitRepositoryError as e:
            exported.delete()
            sys.stderr.write('Repository in « {} » is invalid, skipping\n'.format(e))
            continue

        if clean_commit:
            exported.sha_draft = clean_commit

            # save clean up in old module to avoid any trouble
            current.sha_draft = clean_commit
            current.save()

        [exported.authors.add(author) for author in current.authors.all()]
        [exported.subcategory.add(category) for category in current.subcategory.all()]
        new_gallery = create_gallery_for_article(exported)

        if current.image:
            # migrate image using `Image()`
            try:
                path_to_image = current.image['article_illu'].url
            except InvalidImageFormatError:
                pass
            else:
                img = Image()

                # Create a new name for our image
                filename = os.path.basename(current.image['article_illu'].url)

                # Find original name
                split = filename.split('.')
                original_filename = split[0] + '.' + split[1]

                if "None" in path_to_image:

                    # Move image in the gallery folder
                    shutil.copyfile(os.path.join(MEDIA_ROOT, 'articles', 'None', original_filename),
                                    os.path.join(new_gallery.get_gallery_path(), original_filename))

                    # Update image information
                    img.physical = os.path.join('galleries', str(new_gallery.pk), original_filename)
                else:
                    # Move image in the gallery folder
                    shutil.copyfile(os.path.join(MEDIA_ROOT, 'articles', str(current.id), original_filename),
                                    os.path.join(new_gallery.get_gallery_path(), original_filename))

                    # Update image information
                    img.physical = os.path.join('galleries', str(new_gallery.pk), original_filename)

                img.title = 'icone de l\'article'
                img.slug = slugify(filename)
                img.pubdate = datetime.now()
                img.gallery = new_gallery
                img.save()
                exported.image = img

        # now, re create the manifest.json
        versioned = exported.load_version()
        versioned.type = "ARTICLE"

        if exported.licence:
            versioned.licence = exported.licence

        split_article_in_extracts(versioned)  # create extracts from text
        exported.sha_draft = versioned.commit_changes(u'Migration version 2')
        exported.old_pk = current.pk
        exported.save()

        reacts = Reaction.objects.filter(article__pk=current.pk)\
                                 .select_related("author")\
                                 .order_by("pubdate")\
                                 .all()
        if current.last_reaction:
            export_comments(reacts, exported, ArticleRead, current.last_reaction.pk)
        migrate_validation(exported, ArticleValidation.objects.filter(article__pk=current.pk))

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
            published = publish_content(exported, exported.load_version(exported.sha_draft), False)
            exported.pubdate = current.pubdate
            exported.update_date = current.update
            exported.sha_public = exported.sha_draft
            exported.public_version = published
            exported.save()
            published.content_public_slug = exported.slug
            published.publication_date = exported.pubdate
            published.save()
            # as we changed the structure we have to update the validation history. Yes, it's ugly.
            last_validation = Validation.objects.filter(content__pk=exported.pk).last()
            structure_validation = Validation(content=exported,
                                              version=exported.sha_public,
                                              comment_authors="Migration v2",
                                              comment_validator="yeah",
                                              status="ACCEPT",
                                              validator=last_validation.validator,
                                              date_proposition=datetime.now(),
                                              date_validation=datetime.now(),
                                              date_reserve=datetime.now())
            structure_validation.save()
        # fix strange notification bug
        authors = list(exported.authors.all())
        reads_to_delete = ContentRead.objects\
                                     .filter(content=exported)\
                                     .exclude(user__pk__in=ContentReaction.objects
                                                                          .filter(related_content=exported)
                                                                          .exclude(author__in=authors)
                                                                          .values_list("author__pk", flat=True))
        for read in reads_to_delete.all():
            read.delete()


def migrate_tuto(tutos, title="Exporting mini tuto"):

    if len(tutos) == 0:
        return

    for i in progressbar(xrange(len(tutos)), title, 100):
        current = tutos[i]
        if not os.path.exists(current.get_path(False)):
            sys.stderr.write('Invalid physical path to repository « {} », skipping\n'.format(current.get_path(False)))
            continue
        exported = PublishableContent()
        exported.slug = current.slug
        exported.type = "TUTORIAL"
        exported.title = current.title
        exported.sha_draft = current.sha_draft
        exported.sha_beta = current.sha_beta
        exported.sha_validation = current.sha_validation
        exported.licence = current.licence
        exported.update_date = current.update
        exported.creation_date = current.create_at
        exported.description = current.description
        exported.js_support = current.js_support
        exported.source = current.source
        exported.pubdate = current.pubdate
        exported.save()

        try:
            clean_commit = copy_and_clean_repo(current.get_path(False), exported.get_repo_path(False))
        except InvalidGitRepositoryError as e:
            exported.delete()
            sys.stderr.write('Repository in « {} » is invalid, skipping\n'.format(e))
            continue

        if clean_commit:
            exported.sha_draft = clean_commit

            # save clean up in old module to avoid any trouble
            current.sha_draft = clean_commit
            current.save()

        exported.gallery = current.gallery
        exported.image = current.image
        [exported.subcategory.add(category) for category in current.subcategory.all()]
        [exported.helps.add(help) for help in current.helps.all()]
        [exported.authors.add(author) for author in current.authors.all()]
        exported.save()

        # now, re create the manifest.json
        versioned = exported.load_version()

        # this loop is there because of old .tuto import that failed with their chapter intros
        for container in versioned.traverse(True):
            if container.parent is None:
                continue
            # in old .tuto file chapter intro are represented as chapter_slug/introduction.md
            # instead of part_slug/chapter_slug/introduction.md
            corrected_intro_path = file_join(container.get_path(relative=False), "introduction.md")
            corrected_ccl_path = file_join(container.get_path(relative=False), "conclusion.md")
            if container.get_path(True) not in container.introduction:
                if file_exists(corrected_intro_path):
                    container.introduction = file_join(container.get_path(relative=True), "introduction.md")
                else:
                    container.introduction = None
            if container.get_path(True) not in container.conclusion:
                if file_exists(corrected_ccl_path):
                    container.conclusion = file_join(container.get_path(relative=True), "conclusion.md")
                else:
                    container.conclusion = None

        versioned.licence = exported.licence
        versioned.type = "TUTORIAL"
        versioned.dump_json()
        versioned.repository.index.add(['manifest.json'])  # index new manifest before commit
        exported.sha_draft = versioned.commit_changes(u"Migration version 2")

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
            exported.beta_topic = former_topic
            exported.save()
        # extract notes
        reacts = Note.objects.filter(tutorial__pk=current.pk)\
                             .select_related("author")\
                             .order_by("pubdate")\
                             .all()
        migrate_validation(exported, TutorialValidation.objects.filter(tutorial__pk=current.pk))
        if current.last_note:
            export_comments(reacts, exported, TutorialRead, current.last_note.pk)
        if current.sha_public is not None and current.sha_public != "":
            published = publish_content(exported, exported.load_version(current.sha_public), False)
            exported.pubdate = current.pubdate
            exported.sha_public = current.sha_public
            exported.public_version = published
            exported.save()
            published.content_public_slug = exported.slug
            published.publication_date = current.pubdate

            published.save()
            # set mapping
            map_previous = PublishedContent()
            map_previous.content_public_slug = current.slug
            map_previous.content_pk = current.pk
            map_previous.content_type = 'TUTORIAL'
            map_previous.must_redirect = True  # will send HTTP 301 if visited !
            map_previous.content = exported
            map_previous.save()
        # fix strange notification bug
        authors = list(exported.authors.all())
        reads_to_delete = ContentRead.objects\
                                     .filter(content=exported)\
                                     .exclude(user__pk__in=ContentReaction.objects
                                                                          .filter(related_content=exported)
                                                                          .exclude(author__in=authors)
                                                                          .values_list("author__pk", flat=True))
        for read in reads_to_delete.all():
            read.delete()


@transaction.atomic
class Command(BaseCommand):
    help = 'Migrate old tutorial and article stack to ZEP 12 stack (tutorialv2)'

    def handle(self, *args, **options):
        types = ["big", "mini", "article"]
        if len(args) > 0:
            types = args
        if "article" in types:
            migrate_articles()
        if "mini" in types:
            migrate_tuto(Tutorial.objects.prefetch_related("licence").filter(type="MINI").all())
        if "big" in types:
            migrate_tuto(Tutorial.objects.prefetch_related("licence").filter(type="BIG").all(), "Exporting big tutos")
