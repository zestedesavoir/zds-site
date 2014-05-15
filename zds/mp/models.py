# coding: utf-8

from math import ceil

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from zds.utils import get_current_user, slugify


class PrivateTopic(models.Model):

    """Topic private, containing private posts."""
    class Meta:
        verbose_name = 'Message privé'
        verbose_name_plural = 'Messages privés'

    title = models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous-titre', max_length=200)

    author = models.ForeignKey(User, verbose_name='Auteur',
                               related_name='author')
    participants = models.ManyToManyField(User, verbose_name='Participants',
                                          related_name='participants')
    last_message = models.ForeignKey('PrivatePost', null=True,
                                     related_name='last_message',
                                     verbose_name='Dernier message')
    pubdate = models.DateTimeField('Date de création', auto_now_add=True)

    def __unicode__(self):
        """Textual form of a thread."""
        return self.title

    def get_absolute_url(self):
        return reverse('zds.mp.views.topic',
                       kwargs = {'topic_pk': self.pk,
                                 'topic_slug': slugify(self.title)})

    def get_post_count(self):
        """Return the number of private posts in the private topic."""
        return PrivatePost.objects.filter(privatetopic__pk=self.pk).count()

    def get_last_answer(self):
        """Gets the last answer in the thread, if any."""
        last_post = PrivatePost.objects\
            .filter(privatetopic__pk=self.pk)\
            .order_by('-pubdate')\
            .first()

        if last_post == self.first_post():
            return None
        else:
            return last_post

    def first_post(self):
        """Return the first post of a topic, written by topic's author."""
        return PrivatePost.objects\
            .filter(privatetopic=self)\
            .order_by('pubdate')\
            .first()

    def last_read_post(self):
        """Return the last private post the user has read."""
        try:
            post = PrivateTopicRead.objects\
                .select_related()\
                .filter(privatetopic=self, user=get_current_user())
            if len(post) == 0:
                return self.first_post()
            else:
                return post.latest('privatepost__pubdate').privatepost

        except PrivatePost.DoesNotExist:
            return self.first_post()

    def first_unread_post(self):
        """Return the first post the user has unread."""
        try:
            last_post = PrivateTopicRead.objects\
                .select_related()\
                .filter(privatetopic=self, user=get_current_user())\
                .latest('post__pubdate').privatepost
            
            next_post = PrivatePost.objects.filter(
                privatetopic__pk=self.pk,
                pubdate__gt=last_post__pubdate).first()

            return next_post
        except:
            return self.first_post()

    def alone(self):
        """Check if there just one participant in the conversation
        """
        return self.participants.count()==0

    def never_read(self):
        return never_privateread(self)


class PrivatePost(models.Model):

    """A private post written by an user."""
    privatetopic = models.ForeignKey(
        PrivateTopic,
        verbose_name='Message privé')
    author = models.ForeignKey(User, verbose_name='Auteur',
                               related_name='privateposts')
    text = models.TextField('Texte')

    pubdate = models.DateTimeField('Date de publication', auto_now_add=True)
    update = models.DateTimeField('Date d\'édition', null=True, blank=True)

    position_in_topic = models.IntegerField('Position dans le sujet')

    def __unicode__(self):
        """Textual form of a post."""
        return u'<Post pour "{0}", #{1}>'.format(self.privatetopic, self.pk)

    def get_absolute_url(self):
        page = int(
            ceil(
                float(
                    self.position_in_topic) /
                settings.POSTS_PER_PAGE))

        return '{0}?page={1}#p{2}'.format(
            self.privatetopic.get_absolute_url(),
            page,
            self.pk)


class PrivateTopicRead(models.Model):

    """Small model which keeps track of the user viewing private topics.

    It remembers the topic he looked and what was the last private Post
    at this time.

    """
    class Meta:
        verbose_name = 'Message privé lu'
        verbose_name_plural = 'Messages privés lus'

    privatetopic = models.ForeignKey(PrivateTopic)
    privatepost = models.ForeignKey(PrivatePost)
    user = models.ForeignKey(User, related_name='privatetopics_read')

    def __unicode__(self):
        return u'<Sujet "{0}" lu par {1}, #{2}>'.format(self.privatetopic,
                                                        self.user,
                                                        self.privatepost.pk)


def never_privateread(privatetopic, user=None):
    """Check if a private topic has been read by an user since it last post was
    added."""
    if user is None:
        user = get_current_user()

    return PrivateTopicRead.objects\
        .filter(privatepost=privatetopic.last_message, privatetopic=privatetopic, user=user)\
        .count() == 0


def mark_read(privatetopic):
    """Mark a private topic as read for the user."""
    PrivateTopicRead.objects.filter(
        privatetopic=privatetopic,
        user=get_current_user()).delete()
    t = PrivateTopicRead(
        privatepost=privatetopic.last_message,
        privatetopic=privatetopic,
        user=get_current_user())
    t.save()


def get_last_privatetopics():
    """Returns the 5 very last topics."""
    return PrivateTopic.objects.order_by('-pubdate').all()[:5]
