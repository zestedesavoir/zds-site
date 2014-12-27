# coding: utf-8

from math import ceil
import shutil
try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

import json as json_writer
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from datetime import datetime
from git.repo import Repo

from zds.gallery.models import Image, Gallery
from zds.utils import slugify, get_current_user
from zds.utils.models import SubCategory, Licence, Comment
from zds.utils.tutorials import get_blob, export_tutorial
from zds.settings import ZDS_APP
from zds.utils.models import HelpWriting


TYPE_CHOICES = (
    ('TUTORIAL', 'Tutoriel'),
    ('ARTICLE', 'Article'),
)

STATUS_CHOICES = (
    ('PENDING', 'En attente d\'un validateur'),
    ('PENDING_V', 'En cours de validation'),
    ('ACCEPT', 'Publié'),
    ('REJECT', 'Rejeté'),
)


class InvalidOperationError(RuntimeError):
    pass


class Container(models.Model):
    """
    A container, which can have sub-Containers or Extracts.

    A Container has a title, a introduction and a conclusion, a parent (which can be None) and a position into this
    parent (which is 1 by default).

    It has also a tree depth.

    There is a `compatibility_pk` for compatibility with older versions.
    """
    class Meta:
        verbose_name = 'Container'
        verbose_name_plural = 'Containers'

    # TODO: clear all database related information ?

    title = models.CharField('Titre', max_length=80)

    slug = models.SlugField(max_length=80)

    introduction = models.CharField(
        'chemin relatif introduction',
        blank=True,
        null=True,
        max_length=200)

    conclusion = models.CharField(
        'chemin relatif conclusion',
        blank=True,
        null=True,
        max_length=200)

    parent = models.ForeignKey("self",
                               verbose_name='Conteneur parent',
                               blank=True, null=True,
                               on_delete=models.SET_NULL)

    position_in_parent = models.IntegerField(verbose_name='position dans le conteneur parent',
                                             blank=False,
                                             null=False,
                                             default=1)

    # TODO: thumbnails ?

    # integer key used to represent the tutorial or article old identifier for url compatibility
    compatibility_pk = models.IntegerField(null=False, default=0)

    def get_children(self):
        """
        :return: children of this container, ordered by position
        """
        if self.has_extract():
            return Extract.objects.filter(container_pk=self.pk)

        return Container.objects.filter(parent_pk=self.pk).order_by('position_in_parent')

    def has_extract(self):
        """
        :return: `True` if the container has extract as children, `False` otherwise.
        """
        return Extract.objects.filter(parent=self).count() > 0

    def has_sub_container(self):
        """
        :return: `True` if the container has other Containers as children, `False` otherwise.
        """
        return Container.objects.filter(container=self).count() > 0

    def get_last_child_position(self):
        """
        :return: the relative position of the last child
        """
        return Container.objects.filter(parent=self).count() + Extract.objects.filter(container=self).count()

    def get_tree_depth(self):
        """
        Tree depth is no more than 2, because there is 3 levels for Containers :
        - PublishableContent (0),
        - Part (1),
        - Chapter (2)
        Note that `'max_tree_depth` is `2` to ensure that there is no more than 3 levels
        :return: Tree depth
        """
        depth = 0
        current = self
        while current.parent is not None:
            current = current.parent
            depth += 1
        return depth

    def add_container(self, container):
        """
        Add a child Container, but only if no extract were previously added and tree depth is < 2.
        :param container: the new container
        """
        if not self.has_extract():
            if self.get_tree_depth() < ZDS_APP['tutorial']['max_tree_depth']:
                container.parent = self
                container.position_in_parent = container.get_last_child_position() + 1
                container.save()
            else:
                raise InvalidOperationError("Cannot add another level to this content")
        else:
            raise InvalidOperationError("Can't add a container if this container contains extracts.")
        # TODO: limitation if article ?

    def get_phy_slug(self):
        """
        The slugified title is used to store physically the information in filesystem.
        A "compatibility pk" can be used instead of real pk to ensure compatibility with previous versions.
        :return: the slugified title
        """
        base = ""
        if self.parent is not None:
            base = self.parent.get_phy_slug()

        used_pk = self.compatibility_pk
        if used_pk == 0:
            used_pk = self.pk

        return os.path.join(base, str(used_pk) + '_' + self.slug)

    def update_children(self):
        """
        Update all children of the container.
        """
        for child in self.get_children():
            if child is Container:
                self.introduction = os.path.join(self.get_phy_slug(), "introduction.md")
                self.conclusion = os.path.join(self.get_phy_slug(), "conclusion.md")
                self.save()
                child.update_children()
            else:
                child.text = child.get_path(relative=True)
            child.save()

    def add_extract(self, extract):
        """
        Add a child container, but only if no container were previously added
        :param extract: the new extract
        """
        if not self.has_sub_container():
            extract.container = self
            extract.save()
    # TODO:
    # - rewrite save()
    # - get_absolute_url_*() stuffs, get_path(), get_prod_path()
    # - __unicode__()
    # - get_introduction_*(), get_conclusion_*()
    # - a `top_parent()` function to access directly to the parent PublishableContent and avoid the
    #   `container.parent.parent.parent` stuff ?
    # - a nice `delete_entity_and_tree()` function ? (which also remove the file)
    # - the `maj_repo_*()` stuffs should probably be into the model ?


class PublishableContent(Container):
    """
    A tutorial whatever its size or an article.

    A PublishableContent is a tree depth 0 Container (no parent) with additional information, such as
    - authors, description, source (if the content comes from another website), subcategory and licence ;
    - Thumbnail and gallery ;
    - Creation, publication and update date ;
    - Public, beta, validation and draft sha, for versioning ;
    - Comment support ;
    - Type, which is either "ARTICLE" or "TUTORIAL"

    These are two repositories : draft and online.
    """
    class Meta:
        verbose_name = 'Tutoriel'
        verbose_name_plural = 'Tutoriels'
    # TODO: "Contenu" ?

    description = models.CharField('Description', max_length=200)
    source = models.CharField('Source', max_length=200)
    authors = models.ManyToManyField(User, verbose_name='Auteurs', db_index=True)

    subcategory = models.ManyToManyField(SubCategory,
                                         verbose_name='Sous-Catégorie',
                                         blank=True, null=True, db_index=True)

    # store the thumbnail for tutorial or article
    image = models.ForeignKey(Image,
                              verbose_name='Image du tutoriel',
                              blank=True, null=True,
                              on_delete=models.SET_NULL)

    # every publishable content has its own gallery to manage images
    gallery = models.ForeignKey(Gallery,
                                verbose_name='Galerie d\'images',
                                blank=True, null=True, db_index=True)

    creation_date = models.DateTimeField('Date de création')
    pubdate = models.DateTimeField('Date de publication',
                                   blank=True, null=True, db_index=True)
    update_date = models.DateTimeField('Date de mise à jour',
                                       blank=True, null=True)

    sha_public = models.CharField('Sha1 de la version publique',
                                  blank=True, null=True, max_length=80, db_index=True)
    sha_beta = models.CharField('Sha1 de la version beta publique',
                                blank=True, null=True, max_length=80, db_index=True)
    sha_validation = models.CharField('Sha1 de la version en validation',
                                      blank=True, null=True, max_length=80, db_index=True)
    sha_draft = models.CharField('Sha1 de la version de rédaction',
                                 blank=True, null=True, max_length=80, db_index=True)

    licence = models.ForeignKey(Licence,
                                verbose_name='Licence',
                                blank=True, null=True, db_index=True)
    # as of ZEP 12 this field is no longer the size but the type of content (article/tutorial)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)
    #zep03 field
    helps = models.ManyToManyField(HelpWriting, verbose_name='Aides', db_index=True)

    images = models.CharField(
        'chemin relatif images',
        blank=True,
        null=True,
        max_length=200)
    # TODO: rename this field ? (`relative_image_path` ?)

    last_note = models.ForeignKey('ContentReaction', blank=True, null=True,
                                  related_name='last_note',
                                  verbose_name='Derniere note')
    is_locked = models.BooleanField('Est verrouillé', default=False)
    js_support = models.BooleanField('Support du Javascript', default=False)

    # TODO : split this class in two part (one for the DB object, another one for JSON [versionned] file) ?

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """
        :return: the url to access the tutorial when offline
        """
        return reverse('zds.tutorialv2.views.view_tutorial', args=[self.pk, slugify(self.title)])

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        """
        return reverse('zds.tutorialv2.views.view_tutorial_online', args=[self.pk, slugify(self.title)])

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        """
        if self.sha_beta is not None:
            return self.get_absolute_url() + '?version=' + self.sha_beta
        else:
            return self.get_absolute_url()

    def get_edit_url(self):
        """
        :return: the url to edit the tutorial
        """
        return reverse('zds.tutorialv2.views.modify_tutorial') + '?tutorial={0}'.format(self.pk)

    def in_beta(self):
        """
        A tutorial is not in beta if sha_beta is `None` or empty
        :return: `True` if the tutorial is in beta, `False` otherwise
        """
        return (self.sha_beta is not None) and (self.sha_beta.strip() != '')

    def in_validation(self):
        """
        A tutorial is not in validation if sha_validation is `None` or empty
        :return: `True` if the tutorial is in validation, `False` otherwise
        """
        return (self.sha_validation is not None) and (self.sha_validation.strip() != '')

    def in_drafting(self):
        """
        A tutorial is not in draft if sha_draft is `None` or empty
        :return: `True` if the tutorial is in draft, `False` otherwise
        """
        # TODO: probably always True !!
        return (self.sha_draft is not None) and (self.sha_draft.strip() != '')

    def is_online(self):
        """
        A tutorial is not in on line if sha_public is `None` or empty
        :return: `True` if the tutorial is on line, `False` otherwise
        """
        # TODO: for the logic with previous method, why not `in_public()` ?
        return (self.sha_public is not None) and (self.sha_public.strip() != '')

    def is_article(self):
        """
        :return: `True` if article, `False` otherwise
        """
        return self.type == 'ARTICLE'

    def is_tutorial(self):
        """
        :return: `True` if tutorial, `False` otherwise
        """
        return self.type == 'TUTORIAL'

    def get_phy_slug(self):
        """
        :return: the physical slug, used to represent data in filesystem
        """
        return str(self.pk) + "_" + self.slug

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the Content.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        if relative:
            return ''
        else:
            # get the full path (with tutorial/article before it)
            return os.path.join(settings.ZDS_APP[self.type.lower()]['repo_path'], self.get_phy_slug())
        # TODO: versionning ?!?

    def get_prod_path(self, sha=None):
        """
        Get the physical path to the public version of the content
        :param sha: version of the content, if `None`, public version is used
        :return: physical path
        """
        data = self.load_json_for_public(sha)
        return os.path.join(
            settings.ZDS_APP[self.type.lower()]['repo_public_path'],
            str(self.pk) + '_' + slugify(data['title']))

    def load_dic(self, mandata, sha=None):
        """
        Fill mandata with information from database model and add 'slug', 'is_beta', 'is_validation', 'is_on_line'.
        :param mandata: a dictionary from JSON file
        :param sha: current version, used to fill the `is_*` fields by comparison with the corresponding `sha_*`
        """
        # TODO: give it a more explicit name such as `insert_data_in_json()` ?

        fns = [
            'is_big', 'is_mini', 'have_markdown', 'have_html', 'have_pdf', 'have_epub', 'get_path', 'in_beta',
            'in_validation', 'on_line'
        ]

        attrs = [
            'pk', 'authors', 'subcategory', 'image', 'pubdate', 'update', 'source', 'sha_draft', 'sha_beta',
            'sha_validation', 'sha_public'
        ]

        # load functions and attributs in tree
        for fn in fns:
            mandata[fn] = getattr(self, fn)
        for attr in attrs:
            mandata[attr] = getattr(self, attr)

        # general information
        mandata['slug'] = slugify(mandata['title'])
        mandata['is_beta'] = self.in_beta() and self.sha_beta == sha
        mandata['is_validation'] = self.in_validation() and self.sha_validation == sha
        mandata['is_on_line'] = self.is_online() and self.sha_public == sha

        # url:
        mandata['get_absolute_url'] = reverse('zds.tutorialv2.views.view_tutorial', args=[self.pk, mandata['slug']])

        if self.in_beta():
            mandata['get_absolute_url_beta'] = reverse(
                'zds.tutorialv2.views.view_tutorial',
                args=[self.pk, mandata['slug']]
            ) + '?version=' + self.sha_beta

        else:
            mandata['get_absolute_url_beta'] = reverse(
                'zds.tutorialv2.views.view_tutorial',
                args=[self.pk, mandata['slug']]
            )

        mandata['get_absolute_url_online'] = reverse(
            'zds.tutorialv2.views.view_tutorial_online',
            args=[self.pk, mandata['slug']]
        )

    def load_introduction_and_conclusion(self, mandata, sha=None, public=False):
        """
        Explicitly load introduction and conclusion to avoid useless disk access in `load_dic()`
        :param mandata: dictionary from JSON file
        :param sha: version
        :param public: if `True`, get introduction and conclusion from the public version instead of the draft one
        (`sha` is not used in this case)
        """

        if public:
            mandata['get_introduction_online'] = self.get_introduction_online()
            mandata['get_conclusion_online'] = self.get_conclusion_online()
        else:
            mandata['get_introduction'] = self.get_introduction(sha)
            mandata['get_conclusion'] = self.get_conclusion(sha)

    def load_json_for_public(self, sha=None):
        """
        Fetch the public version of the JSON file for this content.
        :param sha: version
        :return: a dictionary containing the structure of the JSON file.
        """
        if sha is None:
            sha = self.sha_public
        repo = Repo(self.get_path())  # should be `get_prod_path()` !?!
        mantuto = get_blob(repo.commit(sha).tree, 'manifest.json')
        data = json_reader.loads(mantuto)
        if 'licence' in data:
            data['licence'] = Licence.objects.filter(code=data['licence']).first()
        return data

    def dump_json(self, path=None):
        """
        Write the JSON into file
        :param path: path to the file. If `None`, use default path.
        """
        if path is None:
            man_path = os.path.join(self.get_path(), 'manifest.json')
        else:
            man_path = path

        dct = export_tutorial(self)
        data = json_writer.dumps(dct, indent=4, ensure_ascii=False)
        json_data = open(man_path, "w")
        json_data.write(data.encode('utf-8'))
        json_data.close()

    def get_introduction(self, sha=None):
        """
        Get the introduction content of a specific version
        :param sha: version, if `None`, use draft one
        :return: the introduction (as a string)
        """
        # find hash code
        if sha is None:
            sha = self.sha_draft
        repo = Repo(self.get_path())

        manifest = get_blob(repo.commit(sha).tree, "manifest.json")
        content_version = json_reader.loads(manifest)
        if "introduction" in content_version:
            path_content_intro = content_version["introduction"]

        if path_content_intro:
            return get_blob(repo.commit(sha).tree, path_content_intro)

    def get_introduction_online(self):
        """
        Get introduction content of the public version
        :return: the introduction (as a string)
        """
        if self.is_online():
            intro = open(
                os.path.join(
                    self.get_prod_path(),
                    self.introduction +
                    '.html'),
                "r")
            intro_contenu = intro.read()
            intro.close()

            return intro_contenu.decode('utf-8')

    def get_conclusion(self, sha=None):
        """
        Get the conclusion content of a specific version
        :param sha: version, if `None`, use draft one
        :return: the conclusion (as a string)
        """
        # find hash code
        if sha is None:
            sha = self.sha_draft
        repo = Repo(self.get_path())

        manifest = get_blob(repo.commit(sha).tree, "manifest.json")
        content_version = json_reader.loads(manifest)
        if "introduction" in content_version:
            path_content_ccl = content_version["conclusion"]

        if path_content_ccl:
            return get_blob(repo.commit(sha).tree, path_content_ccl)

    def get_conclusion_online(self):
        """
        Get conclusion content of the public version
        :return: the conclusion (as a string)
        """
        if self.is_online():
            conclusion = open(
                os.path.join(
                    self.get_prod_path(),
                    self.conclusion +
                    '.html'),
                "r")
            conlusion_content = conclusion.read()
            conclusion.close()

            return conlusion_content.decode('utf-8')

    def delete_entity_and_tree(self):
        """
        Delete the entities and their filesystem counterparts
        """
        shutil.rmtree(self.get_path(), 0)
        Validation.objects.filter(tutorial=self).delete()

        if self.gallery is not None:
            self.gallery.delete()
        if self.is_online():
            shutil.rmtree(self.get_prod_path())
        self.delete()
        # TODO: should use the "git" version of `delete()` !!!

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)

        super(PublishableContent, self).save(*args, **kwargs)

    def get_note_count(self):
        """
        :return : umber of notes in the tutorial.
        """
        return ContentReaction.objects.filter(tutorial__pk=self.pk).count()

    def get_last_note(self):
        """
        :return: the last answer in the thread, if any.
        """
        return ContentReaction.objects.all()\
            .filter(tutorial__pk=self.pk)\
            .order_by('-pubdate')\
            .first()

    def first_note(self):
        """
        :return: the first post of a topic, written by topic's author, if any.
        """
        return ContentReaction.objects\
            .filter(tutorial=self)\
            .order_by('pubdate')\
            .first()

    def last_read_note(self):
        """
        :return: the last post the user has read.
        """
        try:
            return ContentRead.objects\
                .select_related()\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note
        except ContentReaction.DoesNotExist:
            return self.first_post()

    def first_unread_note(self):
        """
        :return: Return the first note the user has unread.
        """
        try:
            last_note = ContentRead.objects\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note

            next_note = ContentReaction.objects.filter(
                tutorial__pk=self.pk,
                pubdate__gt=last_note.pubdate)\
                .select_related("author").first()
            return next_note
        except:  # TODO: `except:` is bad.
            return self.first_note()

    def antispam(self, user=None):
        """
        Check if the user is allowed to post in an tutorial according to the SPAM_LIMIT_SECONDS value.
        :param user: the user to check antispam. If `None`, current user is used.
        :return: `True` if the user is not able to note (the elapsed time is not enough), `False` otherwise.
        """
        if user is None:
            user = get_current_user()

        last_user_notes = ContentReaction.objects\
            .filter(tutorial=self)\
            .filter(author=user.pk)\
            .order_by('-position')

        if last_user_notes and last_user_notes[0] == self.last_note:
            last_user_note = last_user_notes[0]
            t = datetime.now() - last_user_note.pubdate
            if t.total_seconds() < settings.ZDS_APP['forum']['spam_limit_seconds']:
                return True
        return False

    def change_type(self, new_type):
        """
        Allow someone to change the content type, basically from tutorial to article
        :param new_type: the new type, either `"ARTICLE"` or `"TUTORIAL"`
        """
        if new_type not in TYPE_CHOICES:
            raise ValueError("This type of content does not exist")
        self.type = new_type

    def have_markdown(self):
        """
        Check if the markdown zip archive is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".md"))

    def have_html(self):
        """
        Check if the html version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".html"))

    def have_pdf(self):
        """
        Check if the pdf version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".pdf"))

    def have_epub(self):
        """
        Check if the standard epub version of the content is available
        :return: `True` if available, `False` otherwise
        """
        return os.path.isfile(os.path.join(self.get_prod_path(), self.slug + ".epub"))


class ContentReaction(Comment):
    """
    A comment written by any user about a PublishableContent he just read.
    """
    class Meta:
        verbose_name = 'note sur un contenu'
        verbose_name_plural = 'notes sur un contenu'

    related_content = models.ForeignKey(PublishableContent, verbose_name='Contenu',
                                        related_name="related_content_note", db_index=True)

    def __unicode__(self):
        return u'<Tutorial pour "{0}", #{1}>'.format(self.related_content, self.pk)

    def get_absolute_url(self):
        """
        :return: the url of the comment
        """
        page = int(ceil(float(self.position) / settings.ZDS_APP['forum']['posts_per_page']))
        return '{0}?page={1}#p{2}'.format(self.related_content.get_absolute_url_online(), page, self.pk)


class ContentRead(models.Model):
    """
    Small model which keeps track of the user viewing tutorials.

    It remembers the PublishableContent he looked and what was the last Note at this time.
    """
    class Meta:
        verbose_name = 'Contenu lu'
        verbose_name_plural = 'Contenu lus'

    content = models.ForeignKey(PublishableContent, db_index=True)
    note = models.ForeignKey(ContentReaction, db_index=True)
    user = models.ForeignKey(User, related_name='content_notes_read', db_index=True)

    def __unicode__(self):
        return u'<Tutoriel "{0}" lu par {1}, #{2}>'.format(self.content,  self.user, self.note.pk)


class Extract(models.Model):
    """
    A content extract from a Container.

    It has a title, a position in the parent container and a text.
    """
    class Meta:
        verbose_name = 'Extrait'
        verbose_name_plural = 'Extraits'

    # TODO: clear all database related information ?

    title = models.CharField('Titre', max_length=80)
    container = models.ForeignKey(Container, verbose_name='Chapitre parent', db_index=True)
    position_in_container = models.IntegerField('Position dans le parent', db_index=True)

    text = models.CharField(
        'chemin relatif du texte',
        blank=True,
        null=True,
        max_length=200)

    def __unicode__(self):
        return u'<extrait \'{0}\'>'.format(self.title)

    def get_absolute_url(self):
        """
        :return: the url to access the tutorial offline
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url(),
            self.position_in_container,
            slugify(self.title)
        )

    def get_absolute_url_online(self):
        """
        :return: the url to access the tutorial when online
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url_online(),
            self.position_in_container,
            slugify(self.title)
        )

    def get_absolute_url_beta(self):
        """
        :return: the url to access the tutorial when in beta
        """
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url_beta(),
            self.position_in_container,
            slugify(self.title)
        )

    def get_phy_slug(self):
        """
        :return: the physical slug
        """
        return str(self.pk) + '_' + slugify(self.title)

    def get_path(self, relative=False):
        """
        Get the physical path to the draft version of the extract.
        :param relative: if `True`, the path will be relative, absolute otherwise.
        :return: physical path
        """
        return os.path.join(self.container.get_path(relative=relative), self.get_phy_slug()) + '.md'
        # TODO: versionning ?

    def get_prod_path(self, sha=None):
        """
        Get the physical path to the public version of a specific version of the extract.
        :param sha: version of the content, if `None`, `sha_public` is used
        :return: physical path
        """
        return os.path.join(self.container.get_prod_path(sha), self.get_phy_slug()) + '.md.html'

    def get_text(self, sha=None):

        if self.container.tutorial:
            tutorial = self.container.tutorial
        else:
            tutorial = self.container.part.tutorial
        repo = Repo(tutorial.get_path())

        # find hash code
        if sha is None:
            sha = tutorial.sha_draft

        manifest = get_blob(repo.commit(sha).tree, "manifest.json")
        tutorial_version = json_reader.loads(manifest)
        if "parts" in tutorial_version:
            for part in tutorial_version["parts"]:
                if "chapters" in part:
                    for chapter in part["chapters"]:
                        if "extracts" in chapter:
                            for extract in chapter["extracts"]:
                                if extract["pk"] == self.pk:
                                    path_ext = extract["text"]
                                    break
        if "chapter" in tutorial_version:
            chapter = tutorial_version["chapter"]
            if "extracts" in chapter:
                for extract in chapter["extracts"]:
                    if extract["pk"] == self.pk:
                        path_ext = extract["text"]
                        break

        if path_ext:
            return get_blob(repo.commit(sha).tree, path_ext)
        else:
            return None

    def get_text_online(self):

        if self.container.tutorial:
            path = os.path.join(
                self.container.tutorial.get_prod_path(),
                self.text +
                '.html')
        else:
            path = os.path.join(
                self.container.part.tutorial.get_prod_path(),
                self.text +
                '.html')

        if os.path.isfile(path):
            text = open(path, "r")
            text_contenu = text.read()
            text.close()

            return text_contenu.decode('utf-8')
        else:
            return None


class Validation(models.Model):
    """
    Content validation.
    """
    class Meta:
        verbose_name = 'Validation'
        verbose_name_plural = 'Validations'

    content = models.ForeignKey(PublishableContent, null=True, blank=True,
                                verbose_name='Contenu proposé', db_index=True)
    version = models.CharField('Sha1 de la version',
                               blank=True, null=True, max_length=80, db_index=True)
    date_proposition = models.DateTimeField('Date de proposition', db_index=True)
    comment_authors = models.TextField('Commentaire de l\'auteur')
    validator = models.ForeignKey(User,
                                  verbose_name='Validateur',
                                  related_name='author_content_validations',
                                  blank=True, null=True, db_index=True)
    date_reserve = models.DateTimeField('Date de réservation',
                                        blank=True, null=True)
    date_validation = models.DateTimeField('Date de validation',
                                           blank=True, null=True)
    comment_validator = models.TextField('Commentaire du validateur',
                                         blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING')

    def __unicode__(self):
        return self.content.title

    def is_pending(self):
        """
        Check if the validation is pending
        :return: `True` if status is pending, `False` otherwise
        """
        return self.status == 'PENDING'

    def is_pending_valid(self):
        """
        Check if the validation is pending (but there is a validator)
        :return: `True` if status is pending, `False` otherwise
        """
        return self.status == 'PENDING_V'

    def is_accept(self):
        """
        Check if the content is accepted
        :return: `True` if status is accepted, `False` otherwise
        """
        return self.status == 'ACCEPT'

    def is_reject(self):
        """
        Check if the content is rejected
        :return: `True` if status is rejected, `False` otherwise
        """
        return self.status == 'REJECT'
