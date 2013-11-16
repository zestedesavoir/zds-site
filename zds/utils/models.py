# coding: utf-8
from django.db import models
import os
import string
import uuid

from zds.utils import slugify


def image_path_category(instance, filename):
    '''Return path to an image'''
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('categorie/normal', str(instance.pk), filename)

class Alert(models.Model):
    class Meta :
        verbose_name = 'Alerte'
        verbose_name_plural = 'Alertes'
    
    text = models.TextField('Texte d\'alerte')
    pubdate = models.DateTimeField('Date de publication', blank=True, null=True)
    
    def __unicode__(self):
        return '{0}'.format(self.text)

class Category(models.Model):
    '''Une catégorie, qui correspond à la catégorie dans laquelle on peut ranger un projet (Site Web, Jeux vidéos, etc.)'''
    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'
        ordering = ('title',)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    image = models.ImageField(upload_to=image_path_category)
    
    def __unicode__(self):
        '''
        Textual Category Form
        '''
        return self.title
    
    def get_tuto(self):
        from zds.tutorial.models import Tutorial
        return Tutorial.objects.all().filter(category__in = [self])
    
    def get_tuto_count(self):
        from zds.tutorial.models import Tutorial
        return Tutorial.objects.all().filter(category__in = [self]).count()
   
class Licence(models.Model):
    '''Publication licence'''
    class Meta:
        verbose_name = 'Licence'
        verbose_name_plural = 'Licences'
        
    code = models.CharField('Code', max_length=20)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    
    def __unicode__(self):
        '''
        Textual Licence Form
        '''
        return self.title
        