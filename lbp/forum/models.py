# coding: utf-8

from math import ceil

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from lbp.utils import get_current_user

# TODO: Put these constants in settings.py file
POSTS_PER_PAGE = 21
TOPICS_PER_PAGE = 21
SPAM_LIMIT_SECONDS = 60 * 15


class Category(models.Model):
    '''A category, containing forums'''
    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'

    title = models.CharField('Titre', max_length=80)
    position = models.IntegerField('Position', null=True, blank=True)
    slug = models.SlugField(max_length=80)

    def __unicode__(self):
        '''Textual form of a category'''
        return self.title

    def get_absolute_url(self):
        return '/forums/{0}/'.format(self.slug)

    def get_forums(self):
        return Forum.objects.all()\
            .filter(category=self)\
            .order_by('position_in_category')


class Forum(models.Model):
    '''A forum, containing topics'''
    class Meta:
        verbose_name = 'Forum'
        verbose_name_plural = 'Forums'

    title = models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous-titre', max_length=200)

    category = models.ForeignKey(Category, verbose_name='Catégorie')
    position_in_category = models.IntegerField('Position dans la catégorie',
                                               null=True, blank=True)

    slug = models.SlugField(max_length=80)

    def __unicode__(self):
        '''Textual form of a forum'''
        return self.title

    def get_absolute_url(self):
        return '/forums/{0}/{1}/'.format(
            self.category.slug,
            self.slug,
        )

    def get_topic_count(self):
        '''Gets the number of threads in the forum'''
        return Topic.objects.all().filter(forum__pk=self.pk).count()

    def get_post_count(self):
        return Post.objects.all().filter(topic__forum=self).count()

    def get_last_message(self):
        '''Gets the last message on the forum, if there are any'''
        try:
            return Post.objects.all().filter(topic__forum__pk=self.pk).order_by('-pubdate')[0]
        except IndexError:
            return None

    def is_read(self):
        for t in Topic.objects.all().filter(forum=self):
            if never_read(t):
                return False
        return True


class Topic(models.Model):
    '''A thread, containing posts'''
    class Meta:
        verbose_name = 'Sujet'
        verbose_name_plural = 'Sujets'

    title = models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous-titre', max_length=200)

    forum = models.ForeignKey(Forum, verbose_name='Forum')
    author = models.ForeignKey(User, verbose_name='Auteur',
                                     related_name='topics')
    last_message = models.ForeignKey('Post', null=True,
                                     related_name='last_message',
                                     verbose_name='Dernier message')
    pubdate = models.DateTimeField('Date de création', auto_now_add=True)

    is_solved = models.BooleanField('Est résolu')
    is_locked = models.BooleanField('Est verrouillé')
    is_sticky = models.BooleanField('Est en post-it')

    def __unicode__(self):
        '''
        Textual form of a thread
        '''
        return self.title

    def get_absolute_url(self):
        return '/forums/sujet/{0}/{1}'.format(self.pk, slugify(self.title))

    def get_post_count(self):
        '''
        Return the number of posts in the topic
        '''
        return Post.objects.all().filter(topic__pk=self.pk).count()

    def get_last_answer(self):
        '''
        Gets the last answer in the thread, if any
        '''
        last_post = Post.objects.all()\
            .filter(topic__pk=self.pk)\
            .order_by('-pubdate')[0]

        if last_post == self.first_post():
            return None
        else:
            return last_post

    def first_post(self):
        '''
        Return the first post of a topic, written by topic's author
        '''
        return Post.objects\
            .filter(topic=self)\
            .order_by('pubdate')[0]

    def last_read_post(self):
        '''
        Return the last post the user has read
        '''
        try:
            return TopicRead.objects\
                .select_related()\
                .filter(topic=self, user=get_current_user())\
                .latest('post__pubdate').post
        except Post.DoesNotExist:
            return self.first_post()

    def is_followed(self, user=None):
        '''
        Check if the topic is currently followed by the user. This method uses
        the TopicFollowed objects.
        '''
        if user is None:
            user = get_current_user()

        try:
            TopicFollowed.objects.get(topic=self, user=user)
        except TopicFollowed.DoesNotExist:
            return False
        return True

    def antispam(self, user=None):
        '''
        Check if the user is allowed to post in a topic according to the
        SPAM_LIMIT_SECONDS value. If user shouldn't be able to post, then
        antispam is activated and this method returns True. Otherwise time
        elapsed between user's last post and now is enough, and the method will
        return False.
        '''
        if user is None:
            user = get_current_user()

        last_user_posts = Post.objects\
            .filter(topic=self)\
            .filter(author=user)\
            .order_by('-pubdate')

        if last_user_posts and last_user_posts[0] == self.get_last_answer():
            last_user_post = last_user_posts[0]
            t = timezone.now() - last_user_post.pubdate
            if t.total_seconds() < SPAM_LIMIT_SECONDS:
                return True

        return False

    def never_read(self):
        return never_read(self)


class Post(models.Model):
    '''
    A forum post written by an user.
    '''
    topic = models.ForeignKey(Topic, verbose_name='Sujet')
    author = models.ForeignKey(User, verbose_name='Auteur',
                                     related_name='posts')
    text = models.TextField('Texte')

    pubdate = models.DateTimeField('Date de publication', auto_now_add=True)
    update = models.DateTimeField('Date d\'édition', null=True, blank=True)

    position_in_topic = models.IntegerField('Position dans le sujet')

    is_useful = models.BooleanField('Est utile', default=False)

    def __unicode__(self):
        '''Textual form of a post'''
        return u'<Post pour "{0}", #{1}>'.format(self.topic, self.pk)

    def get_absolute_url(self):
        page = int(ceil(float(self.position_in_topic) / POSTS_PER_PAGE))

        return '{0}?page={1}#p{2}'.format(self.topic.get_absolute_url(), page, self.pk)

    def get_like_count(self):
        return PostLike.objects.filter(posts__pk=self.pk).count()
    
    def get_dislike_count(self):
        return PostDislike.objects.filter(posts__pk=self.pk).count()

class TopicRead(models.Model):
    '''
    Small model which keeps track of the user viewing topics. It remembers the
    topic he looked and what was the last Post at this time.
    '''
    class Meta:
        verbose_name = 'Sujet lu'
        verbose_name_plural = 'Sujets lus'

    topic = models.ForeignKey(Topic)
    post = models.ForeignKey(Post)
    user = models.ForeignKey(User, related_name='topics_read')

    def __unicode__(self):
        return u'<Sujet "{0}" lu par {1}, #{2}>'.format(self.topic,
                                                        self.user,
                                                        self.post.pk)


class TopicFollowed(models.Model):
    '''
    Small model which keeps track of the topics followed by an user. If an
    instance of this model is stored with an user and topic instance, that
    means that this user is following this topic.
    '''
    class Meta:
        verbose_name = 'Sujet suivi'
        verbose_name_plural = 'Sujets suivis'

    topic = models.ForeignKey(Topic)
    user = models.ForeignKey(User, related_name='topics_followed')

    def __unicode__(self):
        return u'<Sujet "{0}" suivi par {1}>'.format(self.topic.title,
                                                     self.user.username)

class PostLike(models.Model):
    '''
    Set of like posts
    '''
    class Meta:
        verbose_name = 'Ce message est utile'
        verbose_name_plural = 'Ces messages sont utiles'

    posts = models.ForeignKey(Post)
    user = models.ForeignKey(User, related_name='post_liked')

class PostDislike(models.Model):
    '''
    Set of dislike posts
    '''
    class Meta:
        verbose_name = 'Ce message est inutile'
        verbose_name_plural = 'Ces messages sont inutiles'

    posts = models.ForeignKey(Post)
    user = models.ForeignKey(User, related_name='post_disliked')


def never_read(topic, user=None):
    '''
    Check if a topic has been read by an user since it last post was added.
    '''
    if user is None:
        user = get_current_user()

    return TopicRead.objects\
        .filter(post=topic.last_message, topic=topic, user=user)\
        .count() == 0


def mark_read(topic):
    '''
    Mark a topic as read for the user
    '''
    TopicRead.objects.filter(topic=topic, user=get_current_user()).delete()
    t = TopicRead(
        post=topic.last_message, topic=topic, user=get_current_user())
    t.save()


def follow(topic):
    '''
    Toggle following of a topic for an user
    '''
    ret = None
    try:
        existing = TopicFollowed.objects.get(
            topic=topic, user=get_current_user()
        )
    except TopicFollowed.DoesNotExist:
        existing = None

    if not existing:
        # Make the user follow the topic
        t = TopicFollowed(
            topic=topic,
            user=get_current_user()
        )
        t.save()
        ret = True
    else:
        # If user is already following the topic, we make him don't anymore
        existing.delete()
        ret = False
    return ret


def get_last_topics():
    '''
    Returns the 5 very last topics
    '''
    return Topic.objects.all().order_by('-last_message__pubdate')[:5]
