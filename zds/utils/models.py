# coding: utf-8

from django.utils.encoding import python_2_unicode_compatible
from datetime import datetime
import os
import string
import uuid
import logging
from uuslug import uuslug

from django.conf import settings

from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver

from easy_thumbnails.fields import ThumbnailerImageField

from zds.notification import signals
from zds.mp.models import PrivateTopic
from zds.tutorialv2.models import TYPE_CHOICES, TYPE_CHOICES_DICT
from zds.utils.mps import send_mp
from zds.utils import slugify
from zds.utils.templatetags.emarkdown import get_markdown_instance, render_markdown

from model_utils.managers import InheritanceManager


logger = logging.getLogger('zds.utils')


def image_path_category(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('categorie/normal', str(instance.pk), filename)


def image_path_help(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('helps/normal', str(instance.pk), filename)


@python_2_unicode_compatible
class Category(models.Model):
    """Common category for several concepts of the application."""

    class Meta:
        verbose_name = _('Categorie')
        verbose_name_plural = _('Categories')

    title = models.CharField(_('Titre'), unique=True, max_length=80)
    description = models.TextField(_('Description'))
    position = models.IntegerField(_('Position'), default=0, db_index=True)

    slug = models.SlugField(max_length=80, unique=True)

    def __str__(self):
        return self.title

    def get_subcategories(self):
        return [a.subcategory for a in
                CategorySubCategory.objects
                .filter(is_main=True, category__pk=self.pk)
                .prefetch_related('subcategory')
                .all()]


@python_2_unicode_compatible
class SubCategory(models.Model):
    """Common subcategory for several concepts of the application."""

    class Meta:
        verbose_name = _('Sous-categorie')
        verbose_name_plural = _('Sous-categories')

    title = models.CharField(_('Titre'), max_length=80, unique=True)
    subtitle = models.CharField(_('Sous-titre'), max_length=200)

    image = models.ImageField(upload_to=image_path_category, blank=True, null=True)

    slug = models.SlugField(max_length=80, unique=True)

    def __str__(self):
        return self.title

    def get_absolute_url_tutorial(self):
        url = reverse('tutorial-index')
        url += '?tag={}'.format(self.slug)
        return url

    def get_absolute_url_article(self):
        url = reverse('article-index')
        url += '?tag={}'.format(self.slug)
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


@python_2_unicode_compatible
class CategorySubCategory(models.Model):

    """ManyToMany between Category and SubCategory but save a boolean to know
    if category is his main category."""
    class Meta:
        verbose_name = _('Hierarchie catégorie')
        verbose_name_plural = _('Hierarchies catégories')

    category = models.ForeignKey(Category, verbose_name=_('Catégorie'), db_index=True)
    subcategory = models.ForeignKey(SubCategory, verbose_name=_('Sous-Catégorie'), db_index=True)
    is_main = models.BooleanField(_('Est la catégorie principale'), default=True, db_index=True)

    def __str__(self):
        """Textual Link Form."""
        if self.is_main:
            return '[{0}][main]: {1}'.format(
                self.category.title,
                self.subcategory.title)
        else:
            return '[{0}]: {1}'.format(
                self.category.title,
                self.subcategory.title)


@python_2_unicode_compatible
class Licence(models.Model):

    """Publication licence."""
    class Meta:
        verbose_name = _('Licence')
        verbose_name_plural = _('Licences')

    code = models.CharField(_('Code'), max_length=20)
    title = models.CharField(_('Titre'), max_length=80)
    description = models.TextField(_('Description'))

    def __str__(self):
        """Textual Licence Form."""
        return self.title


@python_2_unicode_compatible
class Hat(models.Model):
    """
    Hats are labels that users can add to their messages.
    Each member can be allowed to use several hats.
    A hat may also be linked to a group, which
    allows all members of the group to use it.
    It can be used for exemple to allow members to identify
    that a moderation message was posted by a staff member.
    """

    name = models.CharField(_('Casquette'), max_length=40, unique=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, verbose_name='Groupe possédant la casquette',
                              related_name='hats', db_index=True, null=True, blank=True)

    class Meta:
        verbose_name = _('Casquette')
        verbose_name_plural = _('Casquettes')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class HatRequest(models.Model):
    """
    A hat requested by a user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Utilisateur'),
                             related_name='requested_hats')
    hat = models.CharField(_('Casquette'), max_length=40)
    reason = models.TextField(_('Raison de la demande'), max_length=3000)
    date = models.DateTimeField(auto_now_add=True, db_index=True,
                                verbose_name=_('Date de la demande'), db_column='request_date')

    class Meta:
        verbose_name = _('Demande de casquette')
        verbose_name_plural = _('Demandes de casquettes')

    def __str__(self):
        return 'Hat {0} requested by {1}'.format(
            self.hat, self.user.username)

    def get_absolute_url(self):
        return reverse('hat-request', args=[self.pk])


@receiver(models.signals.post_save, sender=Hat)
def prevent_users_getting_hat_linked_to_group(sender, instance, **kwargs):
    """
    When a hat is saved with a linked group, all users that have gotten it by another way
    lose it to prevent a hat from being linked to a user through their profile and one of their groups.
    Hat requests for this hat are also canceled.
    """
    if instance.group:
        instance.profile_set.clear()
        HatRequest.objects.filter(hat__iexact=instance.name).delete()


def get_hat_from_request(request, author=None):
    if author is None:
        author = request.user
    if not request.POST.get('with_hat', None):
        return None
    try:
        hat = Hat.objects.get(pk=int(request.POST.get('with_hat')))
        if hat not in author.profile.get_hats():
            raise ValueError
        return hat
    except (ValueError, Hat.DoesNotExist):
        logger.warning('User #{0} failed to use hat #{1}.'.format(request.user.pk, request.POST.get('hat')))
        return None


def get_hat_from_settings(key):
    hat_name = settings.ZDS_APP['hats'][key]
    hat, _ = Hat.objects.get_or_create(name__iexact=hat_name, defaults={'name': hat_name})
    return hat


@python_2_unicode_compatible
class Comment(models.Model):

    """Comment in forum, articles, tutorial, chapter, etc."""
    class Meta:
        verbose_name = _('Commentaire')
        verbose_name_plural = _('Commentaires')

    objects = InheritanceManager()

    author = models.ForeignKey(User, verbose_name=_('Auteur'),
                               related_name='comments', db_index=True)
    editor = models.ForeignKey(User, verbose_name=_('Editeur'),
                               related_name='comments-editor+',
                               null=True, blank=True)
    ip_address = models.CharField(_("Adresse IP de l\'auteur"), max_length=39)

    position = models.IntegerField(_('Position'), db_index=True)

    text = models.TextField(_('Texte'))
    text_html = models.TextField(_('Texte en Html'))

    like = models.IntegerField(_('Likes'), default=0)
    dislike = models.IntegerField(_('Dislikes'), default=0)

    pubdate = models.DateTimeField(_('Date de publication'), auto_now_add=True, db_index=True)
    update = models.DateTimeField(_("Date d'édition"), null=True, blank=True)
    update_index_date = models.DateTimeField(
        _('Date de dernière modification pour la réindexation partielle'),
        auto_now=True,
        db_index=True)

    is_visible = models.BooleanField(_('Est visible'), default=True)
    text_hidden = models.CharField(
        _('Texte de masquage'),
        max_length=80,
        default='')

    hat = models.ForeignKey(Hat, verbose_name=_('Casquette'), on_delete=models.SET_NULL,
                            related_name='comments', blank=True, null=True)

    def update_content(self, text):
        from zds.notification.models import ping_url

        self.text = text
        md_instance = get_markdown_instance(ping_url=ping_url)
        self.text_html = render_markdown(md_instance, self.text)
        self.save()
        for username in list(md_instance.metadata.get('ping', []))[:settings.ZDS_APP['comment']['max_pings']]:
            signals.new_content.send(sender=self.__class__, instance=self, user=User.objects.get(username=username))

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

    def get_absolute_url(self):
        return Comment.objects.get_subclass(id=self.id).get_absolute_url()

    def __str__(self):
        return 'Comment by {}'.format(self.author.username)


@python_2_unicode_compatible
class CommentEdit(models.Model):
    """Archive for editing a comment."""

    class Meta:
        verbose_name = _("Édition d'un message")
        verbose_name_plural = _('Éditions de messages')

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name=_('Message'),
                                related_name='edits', db_index=True)
    editor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Éditeur'),
                               related_name='edits', db_index=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True,
                                verbose_name=_("Date de l'édition"), db_column='edit_date')
    original_text = models.TextField(_("Contenu d'origine"), blank=True)
    deleted_at = models.DateTimeField(db_index=True, verbose_name=_('Date de suppression'),
                                      blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_('Supprimé par'),
                                   related_name='deleted_edits', db_index=True,
                                   null=True, blank=True)

    def __str__(self):
        return 'Edit by {0} on a comment of {1}'.format(
            self.editor.username, self.comment.author.username)


@python_2_unicode_compatible
class Alert(models.Model):
    """Alerts on all kinds of Comments and PublishedContents."""
    SCOPE_CHOICES = (
        ('FORUM', _('Forum')),
        ('CONTENT', _('Contenu')),
    ) + TYPE_CHOICES

    SCOPE_CHOICES_DICT = dict(SCOPE_CHOICES)

    author = models.ForeignKey(User,
                               verbose_name=_('Auteur'),
                               related_name='alerts',
                               db_index=True)
    comment = models.ForeignKey(Comment,
                                verbose_name=_('Commentaire'),
                                related_name='alerts_on_this_comment',
                                db_index=True,
                                null=True,
                                blank=True)
    # use of string definition of pk to avoid circular import.
    content = models.ForeignKey('tutorialv2.PublishableContent',
                                verbose_name=_('Contenu'),
                                related_name='alerts_on_this_content',
                                db_index=True,
                                null=True,
                                blank=True)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, db_index=True)
    text = models.TextField(_("Texte d'alerte"))
    pubdate = models.DateTimeField(_('Date de création'), db_index=True)
    solved = models.BooleanField(_('Est résolue'), default=False)
    moderator = models.ForeignKey(User,
                                  verbose_name=_('Modérateur'),
                                  related_name='solved_alerts',
                                  db_index=True,
                                  null=True,
                                  blank=True)
    # sent to the alert creator
    resolve_reason = models.TextField(_('Texte de résolution'),
                                      null=True,
                                      blank=True)
    # PrivateTopic sending the resolve_reason to the alert creator
    privatetopic = models.ForeignKey(PrivateTopic,
                                     on_delete=models.SET_NULL,
                                     verbose_name=_('Message privé'),
                                     db_index=True,
                                     null=True,
                                     blank=True)
    solved_date = models.DateTimeField(_('Date de résolution'),
                                       db_index=True,
                                       null=True,
                                       blank=True)

    def get_type(self):
        if self.scope in TYPE_CHOICES_DICT:
            return _('Commentaire')
        else:
            return self.get_scope_display()

    def solve(self, moderator, resolve_reason='', msg_title='', msg_content=''):
        """Solve alert and send a PrivateTopic to the alert author if a reason is given

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
                hat=get_hat_from_settings('moderation'),
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

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = _('Alerte')
        verbose_name_plural = _('Alertes')


@python_2_unicode_compatible
class CommentVote(models.Model):

    """Set of comment votes."""
    class Meta:
        verbose_name = _('Vote')
        verbose_name_plural = _('Votes')
        unique_together = ('user', 'comment')

    comment = models.ForeignKey(Comment, db_index=True)
    user = models.ForeignKey(User, db_index=True)
    positive = models.BooleanField(_('Est un vote positif'), default=True)

    def __str__(self):
        return 'Vote from {} about Comment#{} thumb_up={}'.format(self.user.username, self.comment.pk, self.positive)


@python_2_unicode_compatible
class Tag(models.Model):

    """Set of tags."""

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    title = models.CharField(_('Titre'), max_length=30, unique=True, db_index=True)
    slug = models.SlugField(_('Slug'), max_length=30, unique=True)

    def __str__(self):
        """Textual Link Form."""
        return self.title

    def get_absolute_url(self):
        return reverse('topic-tag-find', kwargs={'tag_pk': self.pk, 'tag_slug': self.slug})

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        if not self.title or not slugify(self.title.replace('-', '')):
            raise ValueError('Tag "{}" is not correct'.format(self.title))
        self.title = smart_text(self.title).lower()
        self.slug = uuslug(self.title, instance=self, max_length=Tag._meta.get_field('slug').max_length)
        super(Tag, self).save(*args, **kwargs)

    @staticmethod
    def has_read_permission(request):
        return True

    def has_object_read_permission(self, request):
        return True


@python_2_unicode_compatible
class HelpWriting(models.Model):

    """Tutorial Help"""
    class Meta:
        verbose_name = _('Aide à la rédaction')
        verbose_name_plural = _('Aides à la rédaction')

    # A name for this help
    title = models.CharField(_('Name'), max_length=20, null=False)
    slug = models.SlugField(max_length=20)

    # tablelabel: Used for the accessibility "This tutoriel need help for writing"
    tablelabel = models.CharField(_('TableLabel'), max_length=150, null=False)

    # The image to use to illustrate this role
    image = ThumbnailerImageField(upload_to=image_path_help)

    def __str__(self):
        """Textual Help Form."""
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(HelpWriting, self).save(*args, **kwargs)
