# coding: utf-8
from django.db import models
import os
import string
import uuid

from zds.utils import slugify
from django.contrib.auth.models import Group, User


def image_path_category(instance, filename):
    '''Return path to an image'''
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('categorie/normal', str(instance.pk), filename)

class Alert(models.Model):
    class Meta :
        verbose_name = 'Alerte'
        verbose_name_plural = 'Alertes'
    
    author = models.ForeignKey(User, verbose_name='Auteur',
                                     related_name='alerts')
    text = models.TextField('Texte d\'alerte')
    pubdate = models.DateTimeField('Date de publication', blank=True, null=True)
    
    def __unicode__(self):
        return u'{0}'.format(self.text)

class Category(models.Model):
    '''Common category for several concepts of the application'''
    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'

    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    slug = models.SlugField(max_length=80)
    
    def __unicode__(self):
        '''Textual Category Form'''
        return self.title

    def get_all_subcategories(self):
        return CategorySubCategory.objects \
                    .filter(category__in = [self]) \
                    .all()

    def get_subcategories(self):
        return CategorySubCategory.objects \
                    .filter(category__in = [self]
                        , is_main = True)\
                    .all()

class SubCategory(models.Model):
    '''Common subcategory for several concepts of the application'''
    class Meta:
        verbose_name = 'Sous-categorie'
        verbose_name_plural = 'Sous-categories'

    title = models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous-titre', max_length=200)
    
    group = models.ManyToManyField(Group, verbose_name='Groupe autorisés (Aucun = public)', null=True, blank=True)
    image = models.ImageField(upload_to=image_path_category)
    
    def __unicode__(self):
        '''Textual Category Form'''
        return self.title

    def get_tutos(self):
        from zds.tutorial.models import Tutorial
        return Tutorial.objects.filter(subcategory__in = [self]).all()

class CategorySubCategory(models.Model):
    '''ManyToMany between Category and SubCategory but save a boolean to know if category is his main category'''
    class Meta:
        verbose_name = 'Liaison entre Category et SubCategory'
        verbose_name_plural = 'Liaisons entre Category et SubCategory'

    category = models.ForeignKey(Category, verbose_name='Catégorie')
    subcategory = models.ForeignKey(SubCategory, verbose_name='Sous-Catégorie')
    is_main = models.BooleanField('Est la catégorie principale', default=True)
   
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
        