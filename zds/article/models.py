# coding: utf-8

from cStringIO import StringIO
import json
from math import ceil
import os
import string
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from PIL import Image
from zds.utils import get_current_user, slugify
from zds.utils.articles import export_article
from zds.utils.models import SubCategory, Comment


IMAGE_MAX_WIDTH = 480
IMAGE_MAX_HEIGHT = 100


def image_path(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('articles', str(instance.pk), filename)


class Article(models.Model):

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    title = models.CharField('Titre', max_length=80)
    description = models.CharField('Description', max_length=200)
    slug = models.SlugField(max_length=80)

    authors = models.ManyToManyField(User, verbose_name='Auteurs')

    create_at = models.DateTimeField('Date de création')
    pubdate = models.DateTimeField(
        'Date de publication',
        blank=True,
        null=True)
    update = models.DateTimeField('Date de mise à jour',
                                  blank=True, null=True)

    subcategory = models.ManyToManyField(SubCategory,
                                         verbose_name='Sous-Catégorie',
                                         blank=True, null=True)

    image = models.ImageField(upload_to=image_path, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=image_path, blank=True, null=True)

    is_visible = models.BooleanField('Visible en rédaction', default=False)

    sha_public = models.CharField('Sha1 de la version publique',
                                  blank=True, null=True, max_length=80)
    sha_validation = models.CharField('Sha1 de la version en validation',
                                      blank=True, null=True, max_length=80)
    sha_draft = models.CharField('Sha1 de la version de rédaction',
                                 blank=True, null=True, max_length=80)

    text = models.CharField(
        'chemin relatif du texte',
        blank=True,
        null=True,
        max_length=200)

    last_reaction = models.ForeignKey('Reaction', blank=True, null=True,
                                      related_name='last_reaction',
                                      verbose_name='Derniere réaction')
    is_locked = models.BooleanField('Est verrouillé', default=False)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('zds.article.views.view',
                       kwargs={'article_pk': self.pk,
                               'article_slug': slugify(self.title)})

    def get_absolute_url_online(self):
        return reverse('zds.article.views.view_online',
                       kwargs={'article_pk': self.pk,
                               'article_slug': slugify(self.title)})

    def get_edit_url(self):
        return reverse('zds.article.views.edit') + '?article={0}'.format(self.pk)

    def on_line(self):
        return self.sha_public is not None

    def in_validation(self):
        return self.sha_validation is not None

    def is_draft(self):
        return self.sha_draft is not None

    def get_path(self, relative=False):
        if relative:
            return None
        else:
            return os.path.join(settings.REPO_ARTICLE_PATH, self.slug)

    def load_json(self, path=None, online=False):
        if path is None:
            man_path = os.path.join(self.get_path(), 'manifest.json')
        else:
            man_path = path
        if os.path.isfile(man_path):
            json_data = open(man_path)
            data = json.load(json_data)
            json_data.close()

            return data
        else:
            return None

    def dump_json(self, path=None):
        if path is None:
            man_path = os.path.join(self.get_path(), 'manifest.json')
        else:
            man_path = path

        dct = export_article(self)
        data = json.dumps(dct, indent=4, ensure_ascii=False)
        json_data = open(man_path, "w")
        json_data.write(data.encode('utf-8'))
        json_data.close()

    def get_text(self):
        path = os.path.join(self.get_path(), self.text)
        txt = open(path, "r")
        txt_contenu = txt.read()
        txt.close()

        return txt_contenu.decode('utf-8')

    def save(
            self,
            force_update=False,
            force_insert=False,
            thumb_size=(
                IMAGE_MAX_HEIGHT,
                IMAGE_MAX_WIDTH),
            *args,
            **kwargs):

        self.slug = slugify(self.title)

        if has_changed(self, 'image') and self.image:
            # TODO : delete old image

            image = Image.open(self.image)

            if image.mode not in ('L', 'RGB'):
                image = image.convert('RGB')

            image.thumbnail(thumb_size, Image.ANTIALIAS)

            # save the thumbnail to memory
            temp_handle = StringIO()
            image.save(temp_handle, 'png')
            temp_handle.seek(0)  # rewind the file

            # save to the thumbnail field
            suf = SimpleUploadedFile(os.path.split(self.image.name)[-1],
                                     temp_handle.read(),
                                     content_type='image/png')
            self.thumbnail.save(suf.name + '.png', suf, save=False)

            # save the image object
            super(Article, self).save(force_update, force_insert)
        else:
            super(Article, self).save()

    def get_reaction_count(self):
        """Return the number of reactions in the article."""
        return Reaction.objects.filter(article__pk=self.pk).count()

    def get_last_reaction(self):
        """Gets the last answer in the thread, if any."""
        try:
            last_reaction = Reaction.objects.all()\
                .filter(article__pk=self.pk)\
                .order_by('pubdate').last()
        except:
            last_reaction = None

        return last_reaction

    def first_reaction(self):
        """Return the first post of a topic, written by topic's author."""
        return Reaction.objects\
            .filter(article=self)\
            .order_by('pubdate')\
            .first()

    def last_read_reaction(self):
        """Return the last post the user has read."""
        try:
            return ArticleRead.objects\
                .select_related()\
                .filter(article=self, user=get_current_user())\
                .latest('reaction__pubdate').reaction
        except Reaction.DoesNotExist:
            return self.first_post()

    def antispam(self, user=None):
        """Check if the user is allowed to post in an article according to the
        SPAM_LIMIT_SECONDS value.

        If user shouldn't be able to reaction, then antispam is
        activated and this method returns True. Otherwise time elapsed
        between user's last reaction and now is enough, and the method
        will return False.

        """
        if user is None:
            user = get_current_user()

        last_user_reactions = Reaction.objects\
            .filter(article=self)\
            .filter(author=user.pk)\
            .order_by('-pubdate')

        if last_user_reactions and last_user_reactions[0] == self.last_reaction:
            last_user_reaction = last_user_reactions[0]
            t = timezone.now() - last_user_reaction.pubdate
            if t.total_seconds() < settings.SPAM_LIMIT_SECONDS:
                return True
        return False


def has_changed(instance, field, manager='objects'):
    """Returns true if a field has changed in a model May be used in a
    model.save() method."""
    if not instance.pk:
        return True
    manager = getattr(instance.__class__, manager)
    old = getattr(manager.get(pk=instance.pk), field)
    return not getattr(instance, field) == old


def get_last_articles():
    return Article.objects.all()\
        .exclude(sha_public__isnull=True)\
        .exclude(sha_public__exact='')\
        .order_by('-pubdate')[:5]


def get_prev_article(g_article):
    return Article.objects\
        .filter(sha_public__isnull=False)\
        .filter(pubdate__lt=g_article.pubdate)\
        .order_by('-pubdate')\
        .first()


def get_next_article(g_article):
    return Article.objects\
        .filter(sha_public__isnull=False)\
        .filter(pubdate__gt=g_article.pubdate)\
        .order_by('pubdate')\
        .first()

STATUS_CHOICES = (
    ('PENDING', 'En attente d\'un validateur'),
    ('RESERVED', 'En cours de validation'),
    ('PUBLISHED', 'Publié'),
    ('REJECTED', 'Rejeté')
)


class Reaction(Comment):

    """A reaction article written by an user."""
    article = models.ForeignKey(Article, verbose_name='Article')

    def __unicode__(self):
        """Textual form of a post."""
        return u'<Article pour "{0}", #{1}>'.format(self.article, self.pk)

    def get_absolute_url(self):
        page = int(ceil(float(self.position) / settings.POSTS_PER_PAGE))

        return '{0}?page={1}#p{2}'.format(
            self.article.get_absolute_url_online(),
            page,
            self.pk)


class ArticleRead(models.Model):

    """Small model which keeps track of the user viewing articles.

    It remembers the topic he looked and what was the last Reaction at
    this time.

    """
    class Meta:
        verbose_name = 'Article lu'
        verbose_name_plural = 'Articles lus'

    article = models.ForeignKey(Article)
    reaction = models.ForeignKey(Reaction)
    user = models.ForeignKey(User, related_name='reactions_read')

    def __unicode__(self):
        return u'<Article "{0}" lu par {1}, #{2}>'.format(self.article,
                                                          self.user,
                                                          self.reaction.pk)


def never_read(article, user=None):
    """Check if a topic has been read by an user since it last post was
    added."""
    if user is None:
        user = get_current_user()

    return ArticleRead.objects\
        .filter(reaction=article.last_reaction, article=article, user=user)\
        .count() == 0


def mark_read(article):
    """Mark a article as read for the user."""
    if article.last_reaction is not None:
        ArticleRead.objects.filter(
            article=article,
            user=get_current_user()).delete()
        a = ArticleRead(
            reaction=article.last_reaction,
            article=article,
            user=get_current_user())
        a.save()


class Validation(models.Model):

    """Article validation."""
    class Meta:
        verbose_name = 'Validation'
        verbose_name_plural = 'Validations'

    article = models.ForeignKey(Article, null=True, blank=True,
                                verbose_name='Article proposé')
    version = models.CharField('Sha1 de la version',
                               blank=True, null=True, max_length=80)
    date_proposition = models.DateTimeField('Date de proposition')
    comment_authors = models.TextField('Commentaire de l\'auteur')
    validator = models.ForeignKey(User,
                                  verbose_name='Validateur',
                                  related_name='articles_author_validations',
                                  blank=True, null=True)
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
        return self.article.title

    def is_pending(self):
        return self.status == 'PENDING'

    def is_pending_valid(self):
        return self.status == 'RESERVED'

    def is_accept(self):
        return self.status == 'PUBLISHED'

    def is_reject(self):
        return self.status == 'REJECTED'
