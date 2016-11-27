# coding: utf-8
import os
import string
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from model_utils.managers import InheritanceManager

from zds.mp.models import PrivateTopic
from zds.tutorialv2.models import TYPE_CHOICES
from zds.utils import slugify
from zds.utils.mps import send_mp
from zds.utils.templatetags.emarkdown import emarkdown


def image_path_category(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('categorie/normal', str(instance.pk), filename)


def image_path_help(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('helps/normal', str(instance.pk), filename)


class Category(models.Model):

    """Common category for several concepts of the application."""
    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'

    title = models.CharField('Titre', unique=True, max_length=80)
    description = models.TextField('Description')
    position = models.IntegerField('Position', default=0)

    slug = models.SlugField(max_length=80, unique=True)

    def __unicode__(self):
        """Textual Category Form."""
        return self.title


class SubCategory(models.Model):

    """Common subcategory for several concepts of the application."""
    class Meta:
        verbose_name = 'Sous-categorie'
        verbose_name_plural = 'Sous-categories'

    title = models.CharField('Titre', max_length=80, unique=True)
    subtitle = models.CharField('Sous-titre', max_length=200)

    image = models.ImageField(
        upload_to=image_path_category,
        blank=True,
        null=True)

    slug = models.SlugField(max_length=80, unique=True)

    def __unicode__(self):
        """Textual Category Form."""
        return self.title

    def get_absolute_url_tutorial(self):
        url = reverse('tutorial-index')
        url = url + '?tag={}'.format(self.slug)
        return url

    def get_absolute_url_article(self):
        url = reverse('article-index')
        url = url + '?tag={}'.format(self.slug)
        return url

    def get_parent_category(self):
        """
        Get the parent of the category.

        :return: the parent category.
        :rtype: Category
        """
        try:
            return CategorySubCategory.objects.filter(subcategory=self).last().category
        except AttributeError:  # no CategorySubCategory
            return None


class CategorySubCategory(models.Model):

    """ManyToMany between Category and SubCategory but save a boolean to know
    if category is his main category."""
    class Meta:
        verbose_name = 'Hierarchie catégorie'
        verbose_name_plural = 'Hierarchies catégories'

    category = models.ForeignKey(Category, verbose_name='Catégorie', db_index=True)
    subcategory = models.ForeignKey(SubCategory, verbose_name='Sous-Catégorie', db_index=True)
    is_main = models.BooleanField('Est la catégorie principale', default=True, db_index=True)

    def __unicode__(self):
        """Textual Link Form."""
        if self.is_main:
            return u'[{0}][main]: {1}'.format(
                self.category.title,
                self.subcategory.title)
        else:
            return u'[{0}]: {1}'.format(
                self.category.title,
                self.subcategory.title)


class Licence(models.Model):

    """Publication licence."""
    class Meta:
        verbose_name = 'Licence'
        verbose_name_plural = 'Licences'

    code = models.CharField('Code', max_length=20)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')

    def __unicode__(self):
        """Textual Licence Form."""
        return self.title


class Comment(models.Model):

    """Comment in forum, articles, tutorial, chapter, etc."""
    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'

    objects = InheritanceManager()

    author = models.ForeignKey(User, verbose_name='Auteur',
                               related_name='comments', db_index=True)
    editor = models.ForeignKey(User, verbose_name='Editeur',
                               related_name='comments-editor+',
                               null=True, blank=True)
    ip_address = models.CharField('Adresse IP de l\'auteur ', max_length=39)

    position = models.IntegerField('Position', db_index=True)

    text = models.TextField('Texte')
    text_html = models.TextField('Texte en Html')

    like = models.IntegerField('Likes', default=0)
    dislike = models.IntegerField('Dislikes', default=0)

    pubdate = models.DateTimeField('Date de publication', auto_now_add=True, db_index=True)
    update = models.DateTimeField('Date d\'édition', null=True, blank=True)
    update_index_date = models.DateTimeField(
        'Date de dernière modification pour la réindexation partielle',
        auto_now=True,
        db_index=True)

    is_visible = models.BooleanField('Est visible', default=True)
    text_hidden = models.CharField(
        'Texte de masquage ',
        max_length=80,
        default='')

    def update_content(self, text):
        self.text = text
        self.text_html = emarkdown(self.text)

    def hide_comment_by_user(self, user, text_hidden):
        """Hide a comment and save it

        :param user: the user that hid the comment
        :param text_hidden: the hide reason
        :return:
        """
        self.is_visible = False
        self.text_hidden = text_hidden
        self.editor = user
        self.save()

    def get_user_vote(self, user):
        """ Get a user vote (like, dislike or neutral) """
        if user.is_authenticated():
            try:
                user_vote = 'like' if CommentVote.objects.get(user=user,
                                                              comment=self).positive else 'dislike'
            except CommentVote.DoesNotExist:
                user_vote = 'neutral'
        else:
            user_vote = 'neutral'

        return user_vote

    def set_user_vote(self, user, vote):
        """ Set a user vote (like, dislike or neutral) """
        if vote == 'neutral':
            CommentVote.objects.filter(user=user, comment=self).delete()
        else:
            CommentVote.objects.update_or_create(user=user, comment=self,
                                                 defaults={'positive': (vote == 'like')})

        self.like = CommentVote.objects.filter(positive=True, comment=self).count()
        self.dislike = CommentVote.objects.filter(positive=False, comment=self).count()

    def get_votes(self, type=None):
        """ Get the non-anonymous votes """
        if not hasattr(self, 'votes'):
            self.votes = CommentVote.objects.filter(comment=self,
                                                    id__gt=settings.VOTES_ID_LIMIT).select_related('user').all()

        return self.votes

    def get_likers(self):
        """ Get the list of the users that liked this Comment """
        return [vote.user for vote in self.get_votes() if vote.positive]

    def get_dislikers(self):
        """ Get the list of the users that disliked this Comment """
        return [vote.user for vote in self.get_votes() if not vote.positive]

    def __unicode__(self):
        return u'{0}'.format(self.text)


class Alert(models.Model):
    """Alerts on all kinds of Comments."""
    SCOPE_CHOICES = (
        ('FORUM', _(u'Forum')),
    ) + TYPE_CHOICES

    SCOPE_CHOICES_DICT = dict(SCOPE_CHOICES)

    author = models.ForeignKey(User,
                               verbose_name='Auteur',
                               related_name='alerts',
                               db_index=True)
    comment = models.ForeignKey(Comment,
                                verbose_name='Commentaire',
                                related_name='alerts',
                                db_index=True)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, db_index=True)
    text = models.TextField('Texte d\'alerte')
    pubdate = models.DateTimeField('Date de création', db_index=True)
    solved = models.BooleanField("Est résolue", default=False)
    moderator = models.ForeignKey(User,
                                  verbose_name='Modérateur',
                                  related_name='solved_alerts',
                                  db_index=True,
                                  null=True,
                                  blank=True)
    # sent to the alert creator
    resolve_reason = models.TextField('Texte de résolution',
                                      null=True,
                                      blank=True)
    # PrivateTopic sending the resolve_reason to the alert creator
    privatetopic = models.ForeignKey(PrivateTopic,
                                     verbose_name=u'Message privé',
                                     db_index=True,
                                     null=True,
                                     blank=True)
    solved_date = models.DateTimeField('Date de résolution',
                                       db_index=True,
                                       null=True,
                                       blank=True)

    def solve(self, note, moderator, resolve_reason='', msg_title='', msg_content=''):
        """Solve alert and send a PrivateTopic if a reason is given

        :param note: the note on which the alert has been raised
        :type note: ContentReaction
        :param resolve_reason: reason
        :type resolve_reason: str
        """
        self.resolve_reason = resolve_reason or None
        if msg_title and msg_content:
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            privatetopic = send_mp(
                bot,
                [self.author],
                msg_title,
                '',
                msg_content,
                True,
            )
            self.privatetopic = privatetopic

        self.solved = True
        self.moderator = moderator
        self.solved_date = datetime.now()
        self.save()

    def get_comment(self):
        return Comment.objects.get(id=self.comment.id)

    def get_comment_subclass(self):
        """Used to retrieve comment URLs (simple call to get_absolute_url
        doesn't work: objects are retrived as Comment and not subclasses) As
        real Comment implementation (subclasses) can't be hard-coded due to
        unresolvable import loops, use InheritanceManager from django-model-
        utils."""
        return Comment.objects.get_subclass(id=self.comment.id)

    def __unicode__(self):
        return u'{0}'.format(self.text)

    class Meta:
        verbose_name = 'Alerte'
        verbose_name_plural = 'Alertes'


class CommentVote(models.Model):

    """Set of comment votes."""
    class Meta:
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'
        unique_together = ('user', 'comment')

    comment = models.ForeignKey(Comment, db_index=True)
    user = models.ForeignKey(User, db_index=True)
    positive = models.BooleanField("Est un vote positif", default=True)


class Tag(models.Model):

    """Set of tags."""

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    title = models.CharField('Titre', max_length=30, unique=True, db_index=True)
    slug = models.SlugField('Slug', max_length=30)

    def __unicode__(self):
        """Textual Link Form."""
        return u"{0}".format(self.title)

    def get_absolute_url(self):
        return reverse('topic-tag-find', kwargs={'tag_pk': self.pk, 'tag_slug': self.slug})

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        if not self.title or not slugify(self.title.replace('-', '')):
            raise ValueError('Tag "{}" is not correct'.format(self.title))
        self.title = smart_text(self.title).lower()
        self.slug = slugify(self.title)
        super(Tag, self).save(*args, **kwargs)

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True


