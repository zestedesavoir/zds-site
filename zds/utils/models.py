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
from django.template.loader import render_to_string

from easy_thumbnails.fields import ThumbnailerImageField

from zds.notification import signals
from zds.mp.models import PrivateTopic
from zds.tutorialv2.models import TYPE_CHOICES, TYPE_CHOICES_DICT
from zds.utils.mps import send_mp
from zds.utils import slugify
from zds.utils.misc import contains_utf8mb4
from zds.utils.templatetags.emarkdown import render_markdown

from model_utils.managers import InheritanceManager


logger = logging.getLogger(__name__)


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


class Category(models.Model):
    """Common category for several concepts of the application."""

    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'

    title = models.CharField('Titre', unique=True, max_length=80)
    description = models.TextField('Description')
    position = models.IntegerField('Position', default=0, db_index=True)

    slug = models.SlugField(max_length=80, unique=True)

    def __str__(self):
        return self.title

    def get_subcategories(self):
        return [a.subcategory for a in
                CategorySubCategory.objects
                .filter(is_main=True, category__pk=self.pk)
                .prefetch_related('subcategory')
                .all()]


class SubCategory(models.Model):
    """Common subcategory for several concepts of the application."""

    class Meta:
        verbose_name = 'Sous-categorie'
        verbose_name_plural = 'Sous-categories'

    title = models.CharField('Titre', max_length=80, unique=True)
    subtitle = models.CharField('Sous-titre', max_length=200)
    position = models.IntegerField('Position', db_index=True, default=0)

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


class CategorySubCategory(models.Model):

    """ManyToMany between Category and SubCategory but save a boolean to know
    if category is his main category."""
    class Meta:
        verbose_name = 'Hierarchie catégorie'
        verbose_name_plural = 'Hierarchies catégories'

    category = models.ForeignKey(Category, verbose_name='Catégorie', db_index=True)
    subcategory = models.ForeignKey(SubCategory, verbose_name='Sous-Catégorie', db_index=True)
    is_main = models.BooleanField('Est la catégorie principale', default=True, db_index=True)

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


class Licence(models.Model):

    """Publication licence."""
    class Meta:
        verbose_name = 'Licence'
        verbose_name_plural = 'Licences'

    code = models.CharField('Code', max_length=20)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')

    def __str__(self):
        """Textual Licence Form."""
        return self.title


class Hat(models.Model):
    """
    Hats are labels that users can add to their messages.
    Each member can be allowed to use several hats.
    A hat may also be linked to a group, which
    allows all members of the group to use it.
    It can be used for exemple to allow members to identify
    that a moderation message was posted by a staff member.
    """

    name = models.CharField('Casquette', max_length=40, unique=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, verbose_name='Groupe possédant la casquette',
                              related_name='hats', db_index=True, null=True, blank=True)
    is_staff = models.BooleanField('Casquette interne au site', default=False)

    class Meta:
        verbose_name = 'Casquette'
        verbose_name_plural = 'Casquettes'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('hat-detail', args=[self.pk])

    def get_users(self):
        """
        Return all users being allowed to use this hat.
        """
        if self.group:
            return self.group.user_set.all()
        else:
            return [p.user for p in self.profile_set.all()]

    def get_users_count(self):
        return len(self.get_users())

    def get_users_preview(self):
        return self.get_users()[:settings.ZDS_APP['member']['users_in_hats_list']]


class HatRequest(models.Model):
    """
    A hat requested by a user.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Utilisateur',
                             related_name='requested_hats')
    hat = models.CharField('Casquette', max_length=40)
    reason = models.TextField('Raison de la demande', max_length=3000)
    date = models.DateTimeField(auto_now_add=True, db_index=True,
                                verbose_name='Date de la demande', db_column='request_date')
    is_granted = models.NullBooleanField('Est acceptée')
    solved_at = models.DateTimeField('Date de résolution', blank=True, null=True)
    moderator = models.ForeignKey(User, verbose_name='Modérateur', blank=True, null=True)
    comment = models.TextField('Commentaire', max_length=1000, blank=True)

    class Meta:
        verbose_name = 'Demande de casquette'
        verbose_name_plural = 'Demandes de casquettes'

    def __str__(self):
        return 'Hat {0} requested by {1}'.format(
            self.hat, self.user.username)

    def get_absolute_url(self):
        return reverse('hat-request', args=[self.pk])

    def get_hat(self, create=False):
        """
        Get hat that matches this request. If it doesn't exist, it is created
        or `None` is returned according to the `create` parameter.
        """

        try:
            return Hat.objects.get(name__iexact=self.hat)
        except Hat.DoesNotExist:
            if create:
                return Hat.objects.create(name=self.hat)
            else:
                return None

    def solve(self, is_granted, moderator=None, comment='', hat_name=None):
        """
        Solve a hat request by granting or denying the requested hat according
        to the `is_granted` parameter.
        """

        if self.is_granted is not None:
            raise Exception('This request is already solved.')

        if moderator is None:
            moderator = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])

        if is_granted:
            if self.get_hat() is None and hat_name:
                self.hat = get_hat_to_add(hat_name, self.user).name
            self.user.profile.hats.add(self.get_hat(create=True))
        self.is_granted = is_granted
        self.moderator = moderator
        self.comment = comment[:1000]
        self.solved_at = datetime.now()
        self.save()
        self.notify_member()

    def notify_member(self):
        """
        Notify the request author about the decision that has been made.
        """

        if self.is_granted is None:
            raise Exception('The request must have been solved to use this method.')

        solved_by_bot = self.moderator == get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])

        message = render_to_string(
            'member/messages/hat_request_decision.md', {
                'is_granted': self.is_granted,
                'hat': self.hat,
                'comment': self.comment,
                'solved_by_bot': solved_by_bot,
            }
        )
        send_mp(self.moderator, [self.user], _('Casquette « {} »').format(self.hat), '', message,
                leave=solved_by_bot, mark_as_read=True, hat=get_hat_from_settings('hats_management'))


@receiver(models.signals.post_save, sender=Hat)
def prevent_users_getting_hat_linked_to_group(sender, instance, **kwargs):
    """
    When a hat is saved with a linked group, all users that have gotten it by another way
    lose it to prevent a hat from being linked to a user through their profile and one of their groups.
    Hat requests for this hat are also canceled.
    """
    if instance.group:
        instance.profile_set.clear()
        for request in HatRequest.objects.filter(hat__iexact=instance.name, is_granted__isnull=True):
            request.solve(is_granted=False,
                          comment=_('La demande a été automatiquement annulée car la casquette est désormais accordée '
                                    'aux membres d’un groupe particulier. Vous l’avez reçue si '
                                    'vous en êtes membre.'))


def get_hat_from_request(request, author=None):
    """
    Return a hat that will be used for a post.
    This checks that the user is allowed to use this hat.
    """

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


def get_hat_to_add(hat_name, user):
    """
    Return a hat that will be added to a user.
    This function creates the hat if it does not exist,
    so be sure you will need it!
    """

    hat_name = hat_name.strip()
    if not hat_name:
        raise ValueError(_('Veuillez saisir une casquette.'))
    if contains_utf8mb4(hat_name):
        raise ValueError(_('La casquette saisie contient des caractères utf8mb4, '
                           'ceux-ci ne peuvent pas être utilisés.'))
    if len(hat_name) > 40:
        raise ValueError(_('La longueur des casquettes est limitée à 40 caractères.'))
    hat, created = Hat.objects.get_or_create(name__iexact=hat_name, defaults={'name': hat_name})
    if created:
        logger.info('Hat #{0} "{1}" has been created.'.format(hat.pk, hat.name))
    if hat in user.profile.get_hats():
        raise ValueError(_('{0} possède déjà la casquette « {1} ».'.format(user.username, hat.name)))
    if hat.group:
        raise ValueError(_('La casquette « {} » est accordée automatiquement aux membres d\'un groupe particulier '
                           'et ne peut donc pas être ajoutée à un membre externe à ce groupe.'.format(hat.name)))
    return hat


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

    hat = models.ForeignKey(Hat, verbose_name='Casquette', on_delete=models.SET_NULL,
                            related_name='comments', blank=True, null=True)

    def update_content(self, text, on_error=None):
        _, old_metadata, _ = render_markdown(self.text)
        html, metadata, messages = render_markdown(text, on_error=on_error)
        self.text = text
        self.text_html = html
        self.save()
        all_the_pings = list(filter(lambda user_name: user_name != self.author.username, metadata.get('ping', [])))
        all_the_pings = list(set(all_the_pings) - set(old_metadata.get('ping', [])))
        max_ping_count = settings.ZDS_APP['comment']['max_pings']
        first_pings = all_the_pings[:max_ping_count]
        for username in first_pings:
            pinged_user = User.objects.filter(username=username).first()
            if not pinged_user:
                continue
            signals.new_content.send(sender=self.__class__, instance=self, user=pinged_user)
        unpinged_usernames = set(old_metadata.get('ping', [])) - set(all_the_pings)
        unpinged_users = User.objects.filter(username__in=list(unpinged_usernames))
        for unpinged_user in unpinged_users:
            signals.unsubscribe.send(self.author, instance=self, user=unpinged_user)

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


class CommentEdit(models.Model):
    """Archive for editing a comment."""

    class Meta:
        verbose_name = "Édition d'un message"
        verbose_name_plural = 'Éditions de messages'

    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, verbose_name='Message',
                                related_name='edits', db_index=True)
    editor = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Éditeur',
                               related_name='edits', db_index=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True,
                                verbose_name="Date de l'édition", db_column='edit_date')
    original_text = models.TextField("Contenu d'origine", blank=True)
    deleted_at = models.DateTimeField(db_index=True, verbose_name='Date de suppression',
                                      blank=True, null=True)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Supprimé par',
                                   related_name='deleted_edits', db_index=True,
                                   null=True, blank=True)

    def __str__(self):
        return 'Edit by {0} on a comment of {1}'.format(
            self.editor.username, self.comment.author.username)


class Alert(models.Model):
    """Alerts on all kinds of Comments and PublishedContents."""
    SCOPE_CHOICES = [
        ('FORUM', _('Forum')),
        ('CONTENT', _('Contenu')),
    ] + TYPE_CHOICES

    SCOPE_CHOICES_DICT = dict(SCOPE_CHOICES)

    author = models.ForeignKey(User,
                               verbose_name='Auteur',
                               related_name='alerts',
                               db_index=True)
    comment = models.ForeignKey(Comment,
                                verbose_name='Commentaire',
                                related_name='alerts_on_this_comment',
                                db_index=True,
                                null=True,
                                blank=True)
    # use of string definition of pk to avoid circular import.
    content = models.ForeignKey('tutorialv2.PublishableContent',
                                verbose_name='Contenu',
                                related_name='alerts_on_this_content',
                                db_index=True,
                                null=True,
                                blank=True)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES, db_index=True)
    text = models.TextField("Texte d'alerte")
    pubdate = models.DateTimeField('Date de création', db_index=True)
    solved = models.BooleanField('Est résolue', default=False)
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
                                     on_delete=models.SET_NULL,
                                     verbose_name='Message privé',
                                     db_index=True,
                                     null=True,
                                     blank=True)
    solved_date = models.DateTimeField('Date de résolution',
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
    positive = models.BooleanField('Est un vote positif', default=True)

    def __str__(self):
        return 'Vote from {} about Comment#{} thumb_up={}'.format(self.user.username, self.comment.pk, self.positive)


class Tag(models.Model):

    """Set of tags."""

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    title = models.CharField('Titre', max_length=30, unique=True, db_index=True)
    slug = models.SlugField('Slug', max_length=30, unique=True)

    def __str__(self):
        """Textual Link Form."""
        return self.title

    def get_absolute_url(self):
        return reverse('topic-tag-find', kwargs={'tag_slug': self.slug})

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


class HelpWriting(models.Model):

    """Tutorial Help"""
    class Meta:
        verbose_name = 'Aide à la rédaction'
        verbose_name_plural = 'Aides à la rédaction'

    # A name for this help
    title = models.CharField('Name', max_length=20, null=False)
    slug = models.SlugField(max_length=20)

    # tablelabel: Used for the accessibility "This tutoriel need help for writing"
    tablelabel = models.CharField('TableLabel', max_length=150, null=False)

    # The image to use to illustrate this role
    image = ThumbnailerImageField(upload_to=image_path_help)

    def __str__(self):
        """Textual Help Form."""
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(HelpWriting, self).save(*args, **kwargs)
