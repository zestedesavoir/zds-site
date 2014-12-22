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


TYPE_CHOICES = (
    ('TUTO', 'Tutoriel'),
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

    """A container (tuto/article, part, chapter)."""
    class Meta:
        verbose_name = 'Container'
        verbose_name_plural = 'Containers'

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

    #integer key used to represent the tutorial or article old identifier for url compatibility
    compatibility_pk = models.IntegerField(null=False, default=0)

    def get_children(self):
        """get this container children"""
        if self.has_extract():
            return Extract.objects.filter(container_pk=self.pk)

        return Container.objects.filter(parent_pk=self.pk)

    def has_extract(self):
        """Check this container has content extracts"""
        return Extract.objects.filter(chapter=self).count() > 0

    def has_sub_part(self):
        """Check this container has a sub container"""
        return Container.objects.filter(parent=self).count() > 0

    def get_last_child_position(self):
        """Get the relative position of the last child"""
        return Container.objects.filter(parent=self).count() + Extract.objects.filter(chapter=self).count()

    def get_tree_depth(self):
        """get the tree depth, basically you don't want to have more than 3 levels :
        - tutorial/article
        - Part
        - Chapter
        """
        depth = 0
        current = self
        while current.parent is not None:
            current = current.parent
            depth += 1

        return depth

    def add_container(self, container):
        """add a child container. A container can only be added if
        no extract had already been added in this container"""
        if not self.has_extract() and self.get_tree_depth() == ZDS_APP['tutorial']['max_tree_depth']:
            container.parent = self
            container.position_in_parent = container.get_last_child_position() + 1
            container.save()
        else:
            raise InvalidOperationError("Can't add a container if this container contains extracts.")

    def get_phy_slug(self):
        """gets the slugified title that is used to store the content into the filesystem"""
        base = ""
        if self.parent is not None:
            base = self.parent.get_phy_slug()

        used_pk = self.compatibility_pk
        if used_pk == 0:
            used_pk = self.pk

        return os.path.join(base,used_pk + '_' + self.slug)

    def update_children(self):
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
        if not self.has_sub_part():
            extract.chapter = self



class PublishableContent(Container):

    """A tutorial whatever its size or an aticle."""
    class Meta:
        verbose_name = 'Tutoriel'
        verbose_name_plural = 'Tutoriels'


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
    # as of ZEP 12 this fiels is no longer the size but the type of content (article/tutorial)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)

    images = models.CharField(
        'chemin relatif images',
        blank=True,
        null=True,
        max_length=200)

    last_note = models.ForeignKey('ContentReaction', blank=True, null=True,
                                  related_name='last_note',
                                  verbose_name='Derniere note')
    is_locked = models.BooleanField('Est verrouillé', default=False)
    js_support = models.BooleanField('Support du Javascript', default=False)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """gets the url to access the tutorial when offline"""
        return reverse('zds.tutorial.views.view_tutorial', args=[
            self.pk, slugify(self.title)
        ])

    def get_absolute_url_online(self):
        return reverse('zds.tutorial.views.view_tutorial_online', args=[
            self.pk, slugify(self.title)
        ])

    def get_absolute_url_beta(self):
        if self.sha_beta is not None:
            return reverse('zds.tutorial.views.view_tutorial', args=[
                self.pk, slugify(self.title)
            ]) + '?version=' + self.sha_beta
        else:
            return self.get_absolute_url()

    def get_edit_url(self):
        return reverse('zds.tutorial.views.modify_tutorial') + \
            '?tutorial={0}'.format(self.pk)

    def in_beta(self):
        return (self.sha_beta is not None) and (self.sha_beta.strip() != '')

    def in_validation(self):
        return (self.sha_validation is not None) and (self.sha_validation.strip() != '')

    def in_drafting(self):
        return (self.sha_draft is not None) and (self.sha_draft.strip() != '')

    def on_line(self):
        return (self.sha_public is not None) and (self.sha_public.strip() != '')

    def is_article(self):
        return self.type == 'ARTICLE'

    def is_tutorial(self):
        return self.type == 'TUTO'

    def get_path(self, relative=False):
        if relative:
            return ''
        else:
            # get the full path (with tutorial/article before it)
            return os.path.join(settings.ZDS_APP[self.type.lower()]['repo_path'], self.get_phy_slug())

    def get_prod_path(self, sha=None):
        data = self.load_json_for_public(sha)
        return os.path.join(
            settings.ZDS_APP['tutorial']['repo_public_path'],
            str(self.pk) + '_' + slugify(data['title']))

    def load_dic(self, mandata, sha=None):
        '''fill mandata with informations from database model'''

        fns = [
            'is_big', 'is_mini', 'have_markdown', 'have_html', 'have_pdf',
            'have_epub', 'get_path', 'in_beta', 'in_validation', 'on_line'
        ]

        attrs = [
            'pk', 'authors', 'subcategory', 'image', 'pubdate', 'update',
            'source', 'sha_draft', 'sha_beta', 'sha_validation', 'sha_public'
        ]

        # load functions and attributs in tree
        for fn in fns:
            mandata[fn] = getattr(self, fn)
        for attr in attrs:
            mandata[attr] = getattr(self, attr)

        # general information
        mandata['slug'] = slugify(mandata['title'])
        mandata['is_beta'] = self.in_beta() and self.sha_beta == sha
        mandata['is_validation'] = self.in_validation() \
            and self.sha_validation == sha
        mandata['is_on_line'] = self.on_line() and self.sha_public == sha

        # url:
        mandata['get_absolute_url'] = reverse(
            'zds.tutorial.views.view_tutorial',
            args=[self.pk, mandata['slug']]
        )

        if self.in_beta():
            mandata['get_absolute_url_beta'] = reverse(
                'zds.tutorial.views.view_tutorial',
                args=[self.pk, mandata['slug']]
            ) + '?version=' + self.sha_beta

        else:
            mandata['get_absolute_url_beta'] = reverse(
                'zds.tutorial.views.view_tutorial',
                args=[self.pk, mandata['slug']]
            )

        mandata['get_absolute_url_online'] = reverse(
            'zds.tutorial.views.view_tutorial_online',
            args=[self.pk, mandata['slug']]
        )

    def load_introduction_and_conclusion(self, mandata, sha=None, public=False):
        '''Explicitly load introduction and conclusion to avoid useless disk
        access in load_dic()
        '''

        if public:
            mandata['get_introduction_online'] = self.get_introduction_online()
            mandata['get_conclusion_online'] = self.get_conclusion_online()
        else:
            mandata['get_introduction'] = self.get_introduction(sha)
            mandata['get_conclusion'] = self.get_conclusion(sha)

    def load_json_for_public(self, sha=None):
        if sha is None:
            sha = self.sha_public
        repo = Repo(self.get_path())
        mantuto = get_blob(repo.commit(sha).tree, 'manifest.json')
        data = json_reader.loads(mantuto)
        if 'licence' in data:
            data['licence'] = Licence.objects.filter(code=data['licence']).first()
        return data

    def load_json(self, path=None, online=False):

        if path is None:
            if online:
                man_path = os.path.join(self.get_prod_path(), 'manifest.json')
            else:
                man_path = os.path.join(self.get_path(), 'manifest.json')
        else:
            man_path = path

        if os.path.isfile(man_path):
            json_data = open(man_path)
            data = json_reader.load(json_data)
            json_data.close()
            if 'licence' in data:
                data['licence'] = Licence.objects.filter(code=data['licence']).first()
            return data

    def dump_json(self, path=None):
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
        """get the introduction content for a particular version if sha is not None"""
        if self.on_line():
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
        """get the conclusion content for a particular version if sha is not None"""
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
        """get the conclusion content for the online version of the current publiable content"""
        if self.on_line():
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
        """deletes the entity and its filesystem counterpart"""
        shutil.rmtree(self.get_path(), 0)
        Validation.objects.filter(tutorial=self).delete()

        if self.gallery is not None:
            self.gallery.delete()
        if self.on_line():
            shutil.rmtree(self.get_prod_path())
        self.delete()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)

        super(PublishableContent, self).save(*args, **kwargs)

    def get_note_count(self):
        """Return the number of notes in the tutorial."""
        return ContentReaction.objects.filter(tutorial__pk=self.pk).count()

    def get_last_note(self):
        """Gets the last answer in the thread, if any."""
        return ContentReaction.objects.all()\
            .filter(tutorial__pk=self.pk)\
            .order_by('-pubdate')\
            .first()

    def first_note(self):
        """Return the first post of a topic, written by topic's author."""
        return ContentReaction.objects\
            .filter(tutorial=self)\
            .order_by('pubdate')\
            .first()

    def last_read_note(self):
        """Return the last post the user has read."""
        try:
            return ContentRead.objects\
                .select_related()\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note
        except ContentReaction.DoesNotExist:
            return self.first_post()

    def first_unread_note(self):
        """Return the first note the user has unread."""
        try:
            last_note = ContentRead.objects\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note

            next_note = ContentReaction.objects.filter(
                tutorial__pk=self.pk,
                pubdate__gt=last_note.pubdate)\
                .select_related("author").first()

            return next_note
        except:
            return self.first_note()

    def antispam(self, user=None):
        """Check if the user is allowed to post in an tutorial according to the
        SPAM_LIMIT_SECONDS value.

        If user shouldn't be able to note, then antispam is activated
        and this method returns True. Otherwise time elapsed between
        user's last note and now is enough, and the method will return
        False.

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
        """Allow someone to change the content type, basicaly from tutorial to article"""
        if new_type not in TYPE_CHOICES:
            raise ValueError("This type of content does not exist")

        self.type = new_type


    def have_markdown(self):
        """Check the markdown zip archive is available"""
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".md"))

    def have_html(self):
        """Check the html version of the content is available"""
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".html"))

    def have_pdf(self):
        """Check the pdf version of the content is available"""
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".pdf"))

    def have_epub(self):
        """Check the standard epub version of the content is available"""
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".epub"))


class ContentReaction(Comment):

    """A comment written by an user about a Publiable content he just read."""
    class Meta:
        verbose_name = 'note sur un contenu'
        verbose_name_plural = 'notes sur un contenu'

    related_content = models.ForeignKey(PublishableContent, verbose_name='Contenu',
                                        related_name="related_content_note", db_index=True)

    def __unicode__(self):
        """Textual form of a post."""
        return u'<Tutorial pour "{0}", #{1}>'.format(self.related_content, self.pk)

    def get_absolute_url(self):
        page = int(ceil(float(self.position) / settings.ZDS_APP['forum']['posts_per_page']))

        return '{0}?page={1}#p{2}'.format(
            self.related_content.get_absolute_url_online(),
            page,
            self.pk)


class ContentRead(models.Model):

    """Small model which keeps track of the user viewing tutorials.

    It remembers the topic he looked and what was the last Note at this
    time.

    """
    class Meta:
        verbose_name = 'Contenu lu'
        verbose_name_plural = 'Contenu lus'

    tutorial = models.ForeignKey(PublishableContent, db_index=True)
    note = models.ForeignKey(ContentReaction, db_index=True)
    user = models.ForeignKey(User, related_name='content_notes_read', db_index=True)

    def __unicode__(self):
        return u'<Tutoriel "{0}" lu par {1}, #{2}>'.format(self.tutorial,
                                                           self.user,
                                                           self.note.pk)


class Extract(models.Model):

    """A content extract from a chapter."""
    class Meta:
        verbose_name = 'Extrait'
        verbose_name_plural = 'Extraits'

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
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url(),
            self.position_in_chapter,
            slugify(self.title)
        )

    def get_absolute_url_online(self):
        return '{0}#{1}-{2}'.format(
            self.container.get_absolute_url_online(),
            self.position_in_chapter,
            slugify(self.title)
        )

    def get_path(self, relative=False):
        if relative:
            if self.container.tutorial:
                chapter_path = ''
            else:
                chapter_path = os.path.join(
                    self.container.part.get_phy_slug(),
                    self.container.get_phy_slug())
        else:
            if self.container.tutorial:
                chapter_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                            self.container.tutorial.get_phy_slug())
            else:
                chapter_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'],
                                            self.container.part.tutorial.get_phy_slug(),
                                            self.container.part.get_phy_slug(),
                                            self.container.get_phy_slug())

        return os.path.join(chapter_path, str(self.pk) + "_" + slugify(self.title)) + '.md'

    def get_prod_path(self):

        if self.container.tutorial:
            data = self.container.tutorial.load_json_for_public()
            mandata = self.container.tutorial.load_dic(data)
            if "chapter" in mandata:
                for ext in mandata["chapter"]["extracts"]:
                    if ext['pk'] == self.pk:
                        return os.path.join(settings.ZDS_APP['tutorial']['repo_public_path'],
                                            str(self.container.tutorial.pk) + '_' + slugify(mandata['title']),
                                            str(ext['pk']) + "_" + slugify(ext['title'])) \
                            + '.md.html'
        else:
            data = self.container.part.tutorial.load_json_for_public()
            mandata = self.container.part.tutorial.load_dic(data)
            for part in mandata["parts"]:
                for chapter in part["chapters"]:
                    for ext in chapter["extracts"]:
                        if ext['pk'] == self.pk:
                            return os.path.join(settings.ZDS_APP['tutorial']['repo_public_path'],
                                                str(mandata['pk']) + '_' + slugify(mandata['title']),
                                                str(part['pk']) + "_" + slugify(part['title']),
                                                str(chapter['pk']) + "_" + slugify(chapter['title']),
                                                str(ext['pk']) + "_" + slugify(ext['title'])) \
                                + '.md.html'

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

    """Tutorial validation."""
    class Meta:
        verbose_name = 'Validation'
        verbose_name_plural = 'Validations'

    tutorial = models.ForeignKey(PublishableContent, null=True, blank=True,
                                 verbose_name='Tutoriel proposé', db_index=True)
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
        return self.tutorial.title

    def is_pending(self):
        return self.status == 'PENDING'

    def is_pending_valid(self):
        return self.status == 'PENDING_V'

    def is_accept(self):
        return self.status == 'ACCEPT'

    def is_reject(self):
        return self.status == 'REJECT'
