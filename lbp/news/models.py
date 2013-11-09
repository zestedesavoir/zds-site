# encoding: utf-8
from math import ceil

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from taggit.managers import TaggableManager

from lbp.utils.models import DateManager, Alert
from lbp.utils import slugify, get_current_user


from lbp.project.models import Category
from lbp.gallery.models import Image, Gallery, UserGallery
import os

from django.conf import settings

POSTS_PER_PAGE = 21
TOPICS_PER_PAGE = 21
SPAM_LIMIT_SECONDS = 60 * 15

STATE_CHOICES = (
        ('REDACTION', 'En rédaction'),
        ('VALIDATION', 'En cours de validation'),
        ('PUBLIQUE', 'Publique'),
    )

class News(models.Model):
    '''Une actualité, désigne les nouvelles qui peuvent être rédigée par les membres'''
    class Meta:
        permissions = (
                ("valider_news",u"Valider une news"),
        )
        verbose_name = 'Actualités'
        verbose_name_plural = 'Actualités'
        ordering = ('date__update',)
        

    title = models.CharField('Titre', max_length=80)
    description = models.CharField('Description', max_length=200)

    text = models.TextField('Texte')

    image = models.ForeignKey(Image, 
                              verbose_name='Image de la news', 
                              blank=True, null=True)
    gallery = models.ForeignKey(Gallery, 
                                verbose_name='Gallérie d\'images', 
                                blank=True, null=True)
    category = models.ManyToManyField(Category, 
                                verbose_name='Categorie', 
                                blank=True, null=True)
    date = models.ForeignKey(DateManager, 
                                verbose_name='Date',
                                blank=True, null=True)
    authors = models.ManyToManyField(User, verbose_name='Auteurs', related_name='u+')

    tags = TaggableManager()
    
    statut = models.CharField(max_length=15, choices=STATE_CHOICES, default='REDACTION')

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/news/{0}/{1}'.format(self.pk, slugify(self.title))

    def get_edit_url(self):
        return '/news/editer?news={0}'.format(self.pk)
    
    def en_validation(self):
        return self.statut=='VALIDATION'
    
    def en_redaction(self):
        return self.statut=='REDACTION'
    
    def en_ligne(self):
        return self.statut=='PUBLIQUE'
    
    def get_comments(self):
        comments = Comment.objects.all().filter(news=self)
        return comments
    
    def get_comment_count(self):
        '''
        Return the number of comments in the news
        '''
        return Comment.objects.all().filter(news__pk=self.pk).count()
    
    def get_last_answer(self):
        '''
        Gets the last answer in the thread, if any
        '''
        comments = Comment.objects.all()\
            .filter(news__pk=self.pk)\
            .order_by('-pubdate')
        if len(comments) == 0:
            last_comment = None
        else:
            last_comment = comments[0]

        return last_comment
    
    def first_comment(self):
        '''
        Return the first post of a topic, written by topic's author
        '''
        comments = Comment.objects.all()\
            .filter(news__pk=self.pk)\
            .order_by('pubdate')
        if len(comments) == 0:
            first_comment = None
        else:
            first_comment = comments[0]

        return first_comment
            
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

        last_user_comments = Comment.objects\
            .filter(news__pk=self.pk)\
            .filter(author=user)\
            .order_by('-pubdate')

        if last_user_comments and last_user_comments[0] == self.get_last_answer():
            last_user_comment = last_user_comments[0]
            t = timezone.now() - last_user_comment.pubdate
            if t.total_seconds() < SPAM_LIMIT_SECONDS:
                return True

        return False

class Comment(models.Model):
    '''
    A News comment written by an user.
    '''
    class Meta :
        permissions = (
                ("moderer_news",u"Moderer une news"),
            )
    news = models.ForeignKey(News, verbose_name='News')
    author = models.ForeignKey(User, verbose_name='Auteur',
                                     related_name='comments')
    text = models.TextField('Texte')

    pubdate = models.DateTimeField('Date de publication', auto_now_add=True)
    update = models.DateTimeField('Date d\'édition', null=True, blank=True)

    position = models.IntegerField('Position')

    def __unicode__(self):
        '''Textual form of a post'''
        return u'<Post pour "{0}", #{1}>'.format(self.news, self.pk)

    def get_absolute_url(self):
        page = int(ceil(float(self.position) / POSTS_PER_PAGE))

        return '{0}?page={1}#p{2}'.format(self.news.get_absolute_url(), page, self.pk)
    
    def get_alerts(self):
        alerts = AlertNews.objects.all().filter(comment=self)
        return comments

class AlertNews(Alert):
    '''
    A News comment written by an user.
    '''
    class Meta :
        verbose_name = 'Alerte de news'
        verbose_name_plural = 'Alertes de news'
        ordering = ('-pubdate',)
    
    comment = models.ForeignKey(Comment, 
                                verbose_name='Commentaire', 
                                blank=True, null=True)
        


def get_last_news():
    return News.objects.all()\
        .filter(statut='PUBLIQUE')\
        .order_by('-date__pubdate')[:5]


def get_prev_news(g_news):
    try:
        return News.objects\
            .filter(statut='PUBLIQUE')\
            .filter(date__pubdate__lt=g_news.date.pubdate)\
            .order_by('-date__pubdate')[0]
    except:
        return None


def get_next_news(g_news):
    try:
        return News.objects\
            .filter(statut='PUBLIQUE')\
            .filter(date__pubdate__gt=g_news.date.pubdate)\
            .order_by('date__pubdate')[0]
    except:
        return None
