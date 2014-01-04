# coding: utf-8

import os
import uuid
import string
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from zds.utils.models import SubCategory
from zds.utils.articles import *

from zds.utils import slugify

from PIL import Image
from cStringIO import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
import json

IMAGE_MAX_WIDTH = 480
IMAGE_MAX_HEIGHT = 100 

def image_path(instance, filename):
    '''Return path to an image'''
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
    pubdate = models.DateTimeField('Date de publication', blank=True, null=True)
    update = models.DateTimeField('Date de mise à jour',
                                  blank=True, null=True)

    subcategory = models.ManyToManyField(SubCategory,
                                verbose_name='Sous-Catégorie',
                                blank=True, null=True)
    
    image = models.ImageField(upload_to=image_path, blank=True, null=True)
    thumbnail = models.ImageField(upload_to=image_path, blank=True, null=True)

    is_visible = models.BooleanField('Visible en rédaction')
    
    sha_public = models.CharField('Sha1 de la version publique',
                                  blank=True, null=True, max_length=80)
    sha_validation = models.CharField('Sha1 de la version en validation',
                                      blank=True, null=True, max_length=80)
    sha_draft = models.CharField('Sha1 de la version de rédaction',
                                 blank=True, null=True, max_length=80)
    
    text = models.CharField('chemin relatif du texte',blank=True, null=True, max_length=200)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/articles/off/{0}/{1}'.format(self.pk, slugify(self.title))
    
    def get_absolute_url_online(self):
        return '/articles/{0}/{1}'.format(self.pk, slugify(self.title))

    def get_edit_url(self):
        return '/articles/off/editer?article={0}'.format(self.pk)
    
    def on_line(self):
        return self.sha_public != None
    
    def in_validation(self):
        return self.sha_validation != None
    
    def get_path(self, relative=False):
        if relative:
            return None
        else:
            return os.path.join(settings.REPO_ARTICLE_PATH, self.slug)
    
    def load_json(self, path=None, online = False):
        if path==None:
            man_path=os.path.join(self.get_path(),'manifest.json')
        else :
            man_path=path
        if os.path.isfile(man_path):
            json_data=open(man_path)
            data = json.load(json_data)
            json_data.close()
            
            return data
        else:
            return None
    
    def dump_json(self, path=None):
        if path==None:
            man_path=os.path.join(self.get_path(),'manifest.json')
        else :
            man_path=path
            
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
        
    def save(self, force_update=False, force_insert=False, thumb_size=(IMAGE_MAX_HEIGHT,IMAGE_MAX_WIDTH)):
        
        self.slug = slugify(self.title)
        
        if has_changed(self, 'image') and self.image :
            # TODO : delete old image
            
            image = Image.open(self.image)
            
            if image.mode not in ('L', 'RGB'):
                image = image.convert('RGB')
            
            image.thumbnail(thumb_size, Image.ANTIALIAS)
            
            # save the thumbnail to memory
            temp_handle = StringIO()
            image.save(temp_handle, 'png')
            temp_handle.seek(0) # rewind the file
            
            # save to the thumbnail field
            suf = SimpleUploadedFile(os.path.split(self.image.name)[-1],
                                     temp_handle.read(),
                                     content_type='image/png')
            self.thumbnail.save(suf.name+'.png', suf, save=False)
        
            # save the image object
            super(Article, self).save(force_update, force_insert)
        else :
            super(Article, self).save()
        
def has_changed(instance, field, manager='objects'):
    """Returns true if a field has changed in a model
    May be used in a model.save() method.
    """
    if not instance.pk:
        return True
    manager = getattr(instance.__class__, manager)
    old = getattr(manager.get(pk=instance.pk), field)
    return not getattr(instance, field) == old

def get_last_articles():
    return Article.objects.all()\
        .filter(sha_public__isnull=False)\
        .order_by('-pubdate')[:5]


def get_prev_article(g_article):
    try:
        return Article.objects\
            .filter(sha_public__isnull=False)\
            .filter(pubdate__lt=g_article.pubdate)\
            .order_by('-pubdate')[0]
    except:
        return None


def get_next_article(g_article):
    try:
        return Article.objects\
            .filter(sha_public__isnull=False)\
            .filter(pubdate__gt=g_article.pubdate)\
            .order_by('pubdate')[0]
    except:
        return None

STATUS_CHOICES = (
        ('PENDING', 'En attente d\'un validateur'),
        ('PENDING_V', 'En cours de validation'),
        ('ACCEPT', 'Publié'),
        ('REJECT', 'Rejeté'),
    )

class Validation(models.Model):
    '''Article validation'''
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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    def __unicode__(self):
        return self.article.title
    
    def is_pending(self):
        return self.status == 'PENDING'
    
    def is_pending_valid(self):
        return self.status == 'PENDING_V'
    
    def is_accept(self):
        return self.status == 'ACCEPT'
    
    def is_reject(self):
        return self.status == 'REJECT'
