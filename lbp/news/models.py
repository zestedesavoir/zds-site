# encoding: utf-8

from django.db import models
from django.contrib.auth.models import User

from taggit.managers import TaggableManager

from lbp.utils.models import DateManager
from lbp.project.models import Category
from lbp.gallery.models import Image, Gallery, UserGallery
import os

from django.conf import settings

STATE_CHOICES = (
        ('REDACTION', 'En rédaction'),
        ('VALIDATION', 'En cours de validation'),
        ('PUBLIQUE', 'Publique'),
    )

class News(models.Model):
    '''Une actualité, désigne les nouvelles qui peuvent être rédigée par les membres'''
    class Meta:
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

def get_last_news():
    return Actualite.objects.all()\
        .filter(statut='PUBLIQUE')\
        .order_by('-pubdate')[:3]


def get_prev_news(g_news):
    try:
        return Actualite.objects\
            .filter(statut='PUBLIQUE')\
            .filter(pubdate__lt=g_news.pubdate)\
            .order_by('-pubdate')[0]
    except IndexError:
        return None


def get_next_news(g_news):
    try:
        return News.objects\
            .filter(statut='PUBLIQUE')\
            .filter(pubdate__gt=g_news.pubdate)\
            .order_by('pubdate')[0]
    except IndexError:
        return None
