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
from django.utils import timezone
from git.repo import Repo

from zds.gallery.models import Image, Gallery
from zds.utils import slugify, get_current_user
from zds.utils.models import SubCategory, Licence, Comment
from zds.utils.tutorials import get_blob, export_tutorial


TYPE_CHOICES = (
    ('MINI', 'Mini-tuto'),
    ('BIG', 'Big-tuto'),
)

STATUS_CHOICES = (
    ('PENDING', 'En attente d\'un validateur'),
    ('PENDING_V', 'En cours de validation'),
    ('ACCEPT', 'Publié'),
    ('REJECT', 'Rejeté'),
)


class Tutorial(models.Model):

    """A tutorial, large or small."""
    class Meta:
        verbose_name = 'Tutoriel'
        verbose_name_plural = 'Tutoriels'

    title = models.CharField('Titre', max_length=80)
    description = models.CharField('Description', max_length=200)
    source = models.CharField('Source', max_length=200)
    authors = models.ManyToManyField(User, verbose_name='Auteurs', db_index=True)

    subcategory = models.ManyToManyField(SubCategory,
                                         verbose_name='Sous-Catégorie',
                                         blank=True, null=True, db_index=True)

    slug = models.SlugField(max_length=80)

    image = models.ForeignKey(Image,
                              verbose_name='Image du tutoriel',
                              blank=True, null=True,
                              on_delete=models.SET_NULL)

    gallery = models.ForeignKey(Gallery,
                                verbose_name='Galerie d\'images',
                                blank=True, null=True, db_index=True)

    create_at = models.DateTimeField('Date de création')
    pubdate = models.DateTimeField('Date de publication',
                                   blank=True, null=True, db_index=True)
    update = models.DateTimeField('Date de mise à jour',
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

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, db_index=True)

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

    images = models.CharField(
        'chemin relatif images',
        blank=True,
        null=True,
        max_length=200)

    last_note = models.ForeignKey('Note', blank=True, null=True,
                                  related_name='last_note',
                                  verbose_name='Derniere note')
    is_locked = models.BooleanField('Est verrouillé', default=False)

    def __unicode__(self):
        return self.title

    def get_phy_slug(self):
        return str(self.pk) + "_" + self.slug

    def get_absolute_url(self):
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

    def get_parts(self):
        return Part.objects.all()\
            .filter(tutorial__pk=self.pk)\
            .order_by('position_in_tutorial')

    def get_chapter(self):
        """Gets the chapter associated with the tutorial if it's small."""
        # We can use get since we know there'll only be one chapter
        try:
            return Chapter.objects.get(tutorial__pk=self.pk)
        except Chapter.DoesNotExist:
            return None

    def in_beta(self):
        return (self.sha_beta is not None) and (self.sha_beta.strip() != '')

    def in_validation(self):
        return (self.sha_validation is not None) and (self.sha_validation.strip() != '')

    def in_drafting(self):
        return (self.sha_draft is not None) and (self.sha_draft.strip() != '')

    def on_line(self):
        return (self.sha_public is not None) and (self.sha_public.strip() != '')

    def is_mini(self):
        return self.type == 'MINI'

    def is_big(self):
        return self.type == 'BIG'

    def get_path(self, relative=False):
        if relative:
            return ''
        else:
            return os.path.join(settings.REPO_PATH, self.get_phy_slug())

    def get_prod_path(self):
        data = self.load_json_for_public()
        return os.path.join(
            settings.REPO_PATH_PROD,
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
        tutorial_version = json_reader.loads(manifest)
        if "introduction" in tutorial_version:
            path_tuto = tutorial_version["introduction"]

        if path_tuto:
            return get_blob(repo.commit(sha).tree, path_tuto)

    def get_introduction_online(self):
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
        # find hash code
        if sha is None:
            sha = self.sha_draft
        repo = Repo(self.get_path())

        manifest = get_blob(repo.commit(sha).tree, "manifest.json")
        tutorial_version = json_reader.loads(manifest)
        if "introduction" in tutorial_version:
            path_tuto = tutorial_version["conclusion"]

        if path_tuto:
            return get_blob(repo.commit(sha).tree, path_tuto)

    def get_conclusion_online(self):
        if self.on_line():
            conclu = open(
                os.path.join(
                    self.get_prod_path(),
                    self.conclusion +
                    '.html'),
                "r")
            conclu_contenu = conclu.read()
            conclu.close()

            return conclu_contenu.decode('utf-8')

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

        super(Tutorial, self).save(*args, **kwargs)

    def get_note_count(self):
        """Return the number of notes in the tutorial."""
        return Note.objects.filter(tutorial__pk=self.pk).count()

    def get_last_note(self):
        """Gets the last answer in the thread, if any."""
        return Note.objects.all()\
            .filter(tutorial__pk=self.pk)\
            .order_by('-pubdate')\
            .first()

    def first_note(self):
        """Return the first post of a topic, written by topic's author."""
        return Note.objects\
            .filter(tutorial=self)\
            .order_by('pubdate')\
            .first()

    def last_read_note(self):
        """Return the last post the user has read."""
        try:
            return TutorialRead.objects\
                .select_related()\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note
        except Note.DoesNotExist:
            return self.first_post()

    def first_unread_note(self):
        """Return the first note the user has unread."""
        try:
            last_note = TutorialRead.objects\
                .filter(tutorial=self, user=get_current_user())\
                .latest('note__pubdate').note

            next_note = Note.objects.filter(
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

        last_user_notes = Note.objects\
            .filter(tutorial=self)\
            .filter(author=user.pk)\
            .order_by('-pubdate')

        if last_user_notes and last_user_notes[0] == self.last_note:
            last_user_note = last_user_notes[0]
            t = timezone.now() - last_user_note.pubdate
            if t.total_seconds() < settings.SPAM_LIMIT_SECONDS:
                return True
        return False

    def update_children(self):
        for part in self.get_parts():
            part.update_children()

        chapter = self.get_chapter()
        if chapter:
            chapter.update_children()

    def have_markdown(self):
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".md"))

    def have_html(self):
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".html"))

    def have_pdf(self):
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".pdf"))

    def have_epub(self):
        return os.path.isfile(os.path.join(self.get_prod_path(),
                                           self.slug +
                                           ".epub"))


def get_last_tutorials():
    tutorials = Tutorial.objects.all()\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:5]

    return tutorials


class Note(Comment):

    """A note tutorial written by an user."""
    class Meta:
        verbose_name = 'note sur un tutoriel'
        verbose_name_plural = 'notes sur un tutoriel'

    tutorial = models.ForeignKey(Tutorial, verbose_name='Tutoriel', db_index=True)

    def __unicode__(self):
        """Textual form of a post."""
        return u'<Tutorial pour "{0}", #{1}>'.format(self.tutorial, self.pk)

    def get_absolute_url(self):
        page = int(ceil(float(self.position) / settings.POSTS_PER_PAGE))

        return '{0}?page={1}#p{2}'.format(
            self.tutorial.get_absolute_url_online(),
            page,
            self.pk)


class TutorialRead(models.Model):

    """Small model which keeps track of the user viewing tutorials.

    It remembers the topic he looked and what was the last Note at this
    time.

    """
    class Meta:
        verbose_name = 'Tutoriel lu'
        verbose_name_plural = 'Tutoriels lus'

    tutorial = models.ForeignKey(Tutorial, db_index=True)
    note = models.ForeignKey(Note, db_index=True)
    user = models.ForeignKey(User, related_name='tuto_notes_read', db_index=True)

    def __unicode__(self):
        return u'<Tutoriel "{0}" lu par {1}, #{2}>'.format(self.tutorial,
                                                           self.user,
                                                           self.note.pk)


def never_read(tutorial, user=None):
    """Check if a topic has been read by an user since it last post was
    added."""
    if user is None:
        user = get_current_user()

    return TutorialRead.objects\
        .filter(note=tutorial.last_note, tutorial=tutorial, user=user)\
        .count() == 0


def mark_read(tutorial):
    """Mark a tutorial as read for the user."""
    if tutorial.last_note is not None:
        TutorialRead.objects.filter(
            tutorial=tutorial,
            user=get_current_user()).delete()
        a = TutorialRead(
            note=tutorial.last_note,
            tutorial=tutorial,
            user=get_current_user())
        a.save()


class Part(models.Model):

    """A part, containing chapters."""
    class Meta:
        verbose_name = 'Partie'
        verbose_name_plural = 'Parties'

    # A part has to belong to a tutorial, since only tutorials with parts
    # are large tutorials
    tutorial = models.ForeignKey(Tutorial, verbose_name='Tutoriel parent', db_index=True)
    position_in_tutorial = models.IntegerField('Position dans le tutoriel', db_index=True)

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

    # The list of chapters is shown between introduction and conclusion

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Part, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'<Partie pour {0}, {1}>' \
            .format(self.tutorial.title, self.position_in_tutorial)

    def get_phy_slug(self):
        return str(self.pk) + "_" + self.slug

    def get_absolute_url(self):
        return reverse('zds.tutorial.views.view_part', args=[
            self.tutorial.pk,
            self.tutorial.slug,
            self.pk,
            self.slug,
        ])

    def get_absolute_url_online(self):
        return reverse('zds.tutorial.views.view_part_online', args=[
            self.tutorial.pk,
            self.tutorial.slug,
            self.pk,
            self.slug,
        ])

    def get_chapters(self):
        return Chapter.objects.all()\
            .filter(part=self).order_by('position_in_part')

    def get_path(self, relative=False):
        if relative:
            return self.get_phy_slug()
        else:
            return os.path.join(settings.REPO_PATH, self.tutorial.get_phy_slug(), self.get_phy_slug())

    def get_introduction(self, sha=None):

        tutorial = self.tutorial

        # find hash code
        if sha is None:
            sha = tutorial.sha_draft
        repo = Repo(tutorial.get_path())

        manifest = get_blob(repo.commit(sha).tree, "manifest.json")
        tutorial_version = json_reader.loads(manifest)
        if "parts" in tutorial_version:
            for part in tutorial_version["parts"]:
                if part["pk"] == self.pk:
                    path_part = part["introduction"]
                    break

        if path_part:
            return get_blob(repo.commit(sha).tree, path_part)
        else:
            return None

    def get_introduction_online(self):
        intro = open(
            os.path.join(
                self.tutorial.get_prod_path(),
                self.introduction +
                '.html'),
            "r")
        intro_contenu = intro.read()
        intro.close()

        return intro_contenu.decode('utf-8')

    def get_conclusion(self, sha=None):

        tutorial = self.tutorial

        # find hash code
        if sha is None:
            sha = tutorial.sha_draft
        repo = Repo(tutorial.get_path())

        manifest = get_blob(repo.commit(sha).tree, "manifest.json")
        tutorial_version = json_reader.loads(manifest)
        if "parts" in tutorial_version:
            for part in tutorial_version["parts"]:
                if part["pk"] == self.pk:
                    path_part = part["conclusion"]
                    break

        if path_part:
            return get_blob(repo.commit(sha).tree, path_part)
        else:
            return None

    def get_conclusion_online(self):
        conclu = open(
            os.path.join(
                self.tutorial.get_prod_path(),
                self.conclusion +
                '.html'),
            "r")
        conclu_contenu = conclu.read()
        conclu.close()

        return conclu_contenu.decode('utf-8')

    def update_children(self):
        self.introduction = os.path.join(self.get_phy_slug(), "introduction.md")
        self.conclusion = os.path.join(self.get_phy_slug(), "conclusion.md")
        self.save()
        for chapter in self.get_chapters():
            chapter.update_children()


class Chapter(models.Model):

    """A chapter, containing text."""
    class Meta:
        verbose_name = 'Chapitre'
        verbose_name_plural = 'Chapitres'

    # A chapter may belong to a part, that's where the difference between large
    # and small tutorials is.
    part = models.ForeignKey(Part, null=True, blank=True,
                             verbose_name='Partie parente', db_index=True)

    position_in_part = models.IntegerField('Position dans la partie',
                                           null=True, blank=True, db_index=True)

    image = models.ForeignKey(Image,
                              verbose_name='Image du chapitre',
                              blank=True, null=True)
    # This field is required in order to use pagination in chapters, see the
    # update_position_in_tutorial() method.
    position_in_tutorial = models.IntegerField('Position dans le tutoriel',
                                               null=True, blank=True)

    # If the chapter doesn't belong to a part, it's a small tutorial; we need
    # to bind informations about said tutorial directly
    tutorial = models.ForeignKey(Tutorial, null=True, blank=True,
                                 verbose_name='Tutoriel parent', db_index=True)

    title = models.CharField('Titre', max_length=80, blank=True)

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

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Chapter, self).save(*args, **kwargs)

    def __unicode__(self):
        if self.tutorial:
            return u'<minituto \'{0}\'>'.format(self.tutorial.title)
        elif self.part:
            return u'<bigtuto \'{0}\', \'{1}\'>' \
                .format(self.part.tutorial.title, self.title)
        else:
            return u'<orphelin>'

    def get_phy_slug(self):
        return str(self.pk) + "_" + self.slug

    def get_absolute_url(self):
        if self.tutorial:
            return self.tutorial.get_absolute_url()

        elif self.part:
            return self.part.get_absolute_url() + '{0}/{1}/'.format(self.pk, self.slug)

        else:
            return reverse('zds.tutorial.views.index')

    def get_absolute_url_online(self):
        if self.tutorial:
            return self.tutorial.get_absolute_url_online()

        elif self.part:
            return self.part.get_absolute_url_online(
            ) + '{0}/{1}/'.format(self.pk, self.slug)

        else:
            return reverse('zds.tutorial.views.index')

    def get_extract_count(self):
        return Extract.objects.all().filter(chapter__pk=self.pk).count()

    def get_extracts(self):
        return Extract.objects.all()\
            .filter(chapter__pk=self.pk)\
            .order_by('position_in_chapter')

    def get_tutorial(self):
        if self.part:
            return self.part.tutorial
        return self.tutorial

    def update_position_in_tutorial(self):
        """Update the position_in_tutorial field, but don't save it ; you have
        to call save() method manually if you want to save the new computed
        position."""
        position = 1
        for part in self.part.tutorial.get_parts():
            if part.position_in_tutorial < self.part.position_in_tutorial:
                for chapter in part.get_chapters():
                    position += 1
            elif part == self.part:
                for chapter in part.get_chapters():
                    if chapter.position_in_part < self.position_in_part:
                        position += 1
        self.position_in_tutorial = position

    def get_path(self, relative=False):
        if relative:
            if self.tutorial:
                chapter_path = self.get_phy_slug()
            else:
                chapter_path = os.path.join(self.part.get_phy_slug(), self.get_phy_slug())
        else:
            if self.tutorial:
                chapter_path = os.path.join(settings.REPO_PATH, self.tutorial.get_phy_slug(), self.get_phy_slug())
            else:
                chapter_path = os.path.join(settings.REPO_PATH,
                                            self.part.tutorial.get_phy_slug(),
                                            self.part.get_phy_slug(),
                                            self.get_phy_slug())

        return chapter_path

    def get_introduction(self, sha=None):

        if self.tutorial:
            tutorial = self.tutorial
        else:
            tutorial = self.part.tutorial
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
                        if chapter["pk"] == self.pk:
                            path_chap = chapter["introduction"]
                            break
        if "chapter" in tutorial_version:
            chapter = tutorial_version["chapter"]
            if chapter["pk"] == self.pk:
                path_chap = chapter["introduction"]

        if path_chap:
            return get_blob(repo.commit(sha).tree, path_chap)
        else:
            return None

    def get_introduction_online(self):
        if self.introduction:
            if self.tutorial:
                path = os.path.join(
                    self.tutorial.get_path(),
                    self.introduction +
                    '.html')
            else:
                path = os.path.join(
                    self.part.tutorial.get_path(),
                    self.introduction +
                    '.html')

            if os.path.isfile(path):
                intro = open(path, "r")
                intro_contenu = intro.read()
                intro.close()

                return intro_contenu.decode('utf-8')
            else:
                return None
        else:
            return None

    def get_conclusion(self, sha=None):

        if self.tutorial:
            tutorial = self.tutorial
        else:
            tutorial = self.part.tutorial
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
                        if chapter["pk"] == self.pk:
                            path_chap = chapter["conclusion"]
                            break
        if "chapter" in tutorial_version:
            chapter = tutorial_version["chapter"]
            if chapter["pk"] == self.pk:
                path_chap = chapter["conclusion"]

        if path_chap:
            return get_blob(repo.commit(sha).tree, path_chap)
        else:
            return None

    def get_conclusion_online(self):
        if self.conclusion:
            if self.tutorial:
                path = os.path.join(
                    self.tutorial.get_path(),
                    self.conclusion +
                    '.html')
            else:
                path = os.path.join(
                    self.part.tutorial.get_path(),
                    self.conclusion +
                    '.html')

            if os.path.isfile(path):
                conclu = open(path, "r")
                conclu_contenu = conclu.read()
                conclu.close()

                return conclu_contenu.decode('utf-8')
            else:
                return None

            return conclu_contenu.decode('utf-8')
        else:
            return None

    def update_children(self):
        if self.part:
            self.introduction = os.path.join(self.part.get_phy_slug(), self.get_phy_slug(), "introduction.md")
            self.conclusion = os.path.join(self.part.get_phy_slug(), self.get_phy_slug(), "conclusion.md")
        else:
            self.introduction = os.path.join("introduction.md")
            self.conclusion = os.path.join("conclusion.md")
        self.save()

        for extract in self.get_extracts():
            extract.text = extract.get_path(relative=True)
            extract.save()


class Extract(models.Model):

    """A content extract from a chapter."""
    class Meta:
        verbose_name = 'Extrait'
        verbose_name_plural = 'Extraits'

    title = models.CharField('Titre', max_length=80)
    chapter = models.ForeignKey(Chapter, verbose_name='Chapitre parent', db_index=True)
    position_in_chapter = models.IntegerField('Position dans le chapitre', db_index=True)

    text = models.CharField(
        'chemin relatif du texte',
        blank=True,
        null=True,
        max_length=200)

    def __unicode__(self):
        return u'<extrait \'{0}\'>'.format(self.title)

    def get_absolute_url(self):
        return '{0}#{1}-{2}'.format(
            self.chapter.get_absolute_url(),
            self.position_in_chapter,
            slugify(self.title)
        )

    def get_absolute_url_online(self):
        return '{0}#{1}-{2}'.format(
            self.chapter.get_absolute_url_online(),
            self.position_in_chapter,
            slugify(self.title)
        )

    def get_path(self, relative=False):
        if relative:
            if self.chapter.tutorial:
                chapter_path = ''
            else:
                chapter_path = os.path.join(
                    self.chapter.part.get_phy_slug(),
                    self.chapter.get_phy_slug())
        else:
            if self.chapter.tutorial:
                chapter_path = os.path.join(settings.REPO_PATH, self.chapter.tutorial.get_phy_slug())
            else:
                chapter_path = os.path.join(settings.REPO_PATH,
                                            self.chapter.part.tutorial.get_phy_slug(),
                                            self.chapter.part.get_phy_slug(),
                                            self.chapter.get_phy_slug())

        return os.path.join(chapter_path, str(self.pk) + "_" + slugify(self.title)) + '.md'

    def get_prod_path(self):

        if self.chapter.tutorial:
            data = self.chapter.tutorial.load_json_for_public()
            mandata = self.chapter.tutorial.load_dic(data)
            if "chapter" in mandata:
                for ext in mandata["chapter"]["extracts"]:
                    if ext['pk'] == self.pk:
                        return os.path.join(settings.REPO_PATH_PROD,
                                            str(self.chapter.tutorial.pk) + '_' + slugify(mandata['title']),
                                            str(ext['pk']) + "_" + slugify(ext['title'])) \
                            + '.md.html'
        else:
            data = self.chapter.part.tutorial.load_json_for_public()
            mandata = self.chapter.part.tutorial.load_dic(data)
            for part in mandata["parts"]:
                for chapter in part["chapters"]:
                    for ext in chapter["extracts"]:
                        if ext['pk'] == self.pk:
                            return os.path.join(settings.REPO_PATH_PROD,
                                                str(mandata['pk']) + '_' + slugify(mandata['title']),
                                                str(part['pk']) + "_" + slugify(part['title']),
                                                str(chapter['pk']) + "_" + slugify(chapter['title']),
                                                str(ext['pk']) + "_" + slugify(ext['title'])) \
                                + '.md.html'

    def get_text(self, sha=None):

        if self.chapter.tutorial:
            tutorial = self.chapter.tutorial
        else:
            tutorial = self.chapter.part.tutorial
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

        if self.chapter.tutorial:
            path = os.path.join(
                self.chapter.tutorial.get_prod_path(),
                self.text +
                '.html')
        else:
            path = os.path.join(
                self.chapter.part.tutorial.get_prod_path(),
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

    tutorial = models.ForeignKey(Tutorial, null=True, blank=True,
                                 verbose_name='Tutoriel proposé', db_index=True)
    version = models.CharField('Sha1 de la version',
                               blank=True, null=True, max_length=80, db_index=True)
    date_proposition = models.DateTimeField('Date de proposition', db_index=True)
    comment_authors = models.TextField('Commentaire de l\'auteur')
    validator = models.ForeignKey(User,
                                  verbose_name='Validateur',
                                  related_name='author_validations',
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
