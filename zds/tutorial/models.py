# coding: utf-8

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from os import path
import os
import json

from zds.gallery.models import Image, Gallery
from zds.utils import slugify
from zds.utils.models import Category, SubCategory, Licence
from zds.utils.tutorials import *


TYPE_CHOICES = (
        ('MINI', 'Mini-tuto'),
        ('BIG', 'Big tuto'),
    )

STATUS_CHOICES = (
        ('PENDING', 'En attente d\'un validateur'),
        ('PENDING_V', 'En cours de validation'),
        ('ACCEPT', 'Publié'),
        ('REJECT', 'Rejeté'),
    )

class Tutorial(models.Model):

    '''A tutorial, large or small'''
    class Meta:
        verbose_name = 'Tutoriel'
        verbose_name_plural = 'Tutoriels'

    title = models.CharField('Titre', max_length=80)
    description = models.CharField('Description', max_length=200)
    authors = models.ManyToManyField(User, verbose_name='Auteurs')
    
    subcategory = models.ManyToManyField(SubCategory,
                                verbose_name='SubCategory',
                                blank=True, null=True)

    slug = models.SlugField(max_length=80)

    image = models.ForeignKey(Image,
                              verbose_name='Image du tutoriel',
                              blank=True, null=True)

    create_at = models.DateTimeField('Date de création')
    pubdate = models.DateTimeField('Date de publication',
                                   blank=True, null=True)
    update = models.DateTimeField('Date de mise à jour',
                                  blank=True, null=True)
    
    sha_public = models.CharField('Sha1 de la version publique',
                                  blank=True, null=True, max_length=80)
    sha_beta = models.CharField('Sha1 de la version beta publique',
                                blank=True, null=True, max_length=80)
    sha_validation = models.CharField('Sha1 de la version en validation',
                                      blank=True, null=True, max_length=80)
    sha_draft = models.CharField('Sha1 de la version de rédaction',
                                 blank=True, null=True, max_length=80)
    
    licence = models.ForeignKey(Licence,
                                verbose_name='Licence',
                                blank=True, null=True)
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    
    introduction = models.CharField('chemin relatif introduction',blank=True, null=True, max_length=200)
    
    conclusion = models.CharField('chemin relatif conclusion',blank=True, null=True, max_length=200)
    
    images = models.CharField('chemin relatif images',blank=True, null=True, max_length=200)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('zds.tutorial.views.view_tutorial', args=[
            self.pk, slugify(self.title)
        ])
    
    def get_absolute_url_online(self):
        return reverse('zds.tutorial.views.view_tutorial_online', args=[
            self.pk, slugify(self.title)
        ])
    
    def get_absolute_url_beta(self):
        if self.sha_beta != None:
            return reverse('zds.tutorial.views.view_tutorial', args=[
                self.pk, slugify(self.title)
            ])+'?version='+self.sha_beta
        else:
            return self.get_absolute_url()

    def get_edit_url(self):
        return '/tutorial/editer?tutorial={0}'.format(self.pk)

    def get_parts(self):
        return Part.objects.all()\
            .filter(tutorial__pk=self.pk)\
            .order_by('position_in_tutorial')

    def get_chapter(self):
        '''Gets the chapter associated with the tutorial if it's small'''
        # We can use get since we know there'll only be one chapter
        return Chapter.objects.get(tutorial__pk=self.pk)
    
    def in_beta(self):
        return self.sha_beta != None
    
    def in_validation(self):
        return self.sha_validation != None
    
    def in_drafting(self):
        return self.sha_draft != None
    
    def on_line(self):
        return self.sha_public != None
    
    def is_mini(self):
        return self.type == 'MINI'
    
    def is_big(self):
        return self.type == 'BIG'
    
    def get_path(self, relative=False):
        if relative:
            return ''
        else:
            return os.path.join(settings.REPO_PATH, self.slug)
    
    def get_prod_path(self):
        return os.path.join(settings.REPO_PATH_PROD, self.slug)
    
        
    def load_json(self, path=None, online = False):
        if path==None:
            if online :
                man_path=os.path.join(self.get_prod_path(),'manifest.json')
            else:
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
            
        dct = export_tutorial(self)
        data = json.dumps(dct, indent=4, ensure_ascii=False)
        json_data = open(man_path, "w")
        json_data.write(data.encode('utf-8'))
        json_data.close()
    
    def get_introduction(self):
        path = os.path.join(self.get_path(), self.introduction)
        intro = open(path, "r")
        intro_contenu = intro.read()
        intro.close()
        
        return intro_contenu.decode('utf-8')
    
    def get_introduction_online(self):
        intro = open(os.path.join(self.get_prod_path(), self.introduction+'.html'), "r")
        intro_contenu = intro.read()
        intro.close()
        
        return intro_contenu.decode('utf-8')
    
    def get_conclusion(self):
        
        conclu = open(os.path.join(self.get_path(), self.conclusion), "r")
        conclu_contenu = conclu.read()
        conclu.close()
        
        return conclu_contenu.decode('utf-8')

    def get_conclusion_online(self):
        conclu = open(os.path.join(self.get_prod_path(), self.conclusion+'.html'), "r")
        conclu_contenu = conclu.read()
        conclu.close()
        
        return conclu_contenu.decode('utf-8')
        
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
                            
        super(Tutorial, self).save(*args, **kwargs)


    
def get_last_tutorials():
    tutorials = Tutorial.objects.all()\
        .filter(sha_public__isnull=False)\
        .order_by('-pubdate')[:5]
        
    return tutorials


class Part(models.Model):

    '''A part, containing chapters'''
    class Meta:
        verbose_name = 'Partie'
        verbose_name_plural = 'Parties'

    # A part has to belong to a tutorial, since only tutorials with parts
    # are large tutorials
    tutorial = models.ForeignKey(Tutorial, verbose_name='Tutoriel parent')
    position_in_tutorial = models.IntegerField('Position dans le tutoriel')

    title = models.CharField('Titre', max_length=80)

    slug = models.SlugField(max_length=80)
    
    introduction = models.CharField('chemin relatif introduction',blank=True, null=True, max_length=200)
    conclusion = models.CharField('chemin relatif conclusion',blank=True, null=True, max_length=200)

    
    # The list of chapters is shown between introduction and conclusion

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Part, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'<Partie pour {0}, {1}>'.format\
            (self.tutorial.title, self.position_in_tutorial)

    def get_absolute_url(self):
        return reverse('zds.tutorial.views.view_part', args=[
            self.tutorial.pk,
            self.tutorial.slug,
            self.slug,
        ])
    
    def get_absolute_url_online(self):
        return reverse('zds.tutorial.views.view_part_online', args=[
            self.tutorial.pk,
            self.tutorial.slug,
            self.slug,
        ])

    def get_chapters(self):
        return Chapter.objects.all()\
            .filter(part=self).order_by('position_in_part')

    def get_path(self, relative=False):
        if relative:
            return self.slug
        else:
            return os.path.join(os.path.join(settings.REPO_PATH, self.tutorial.slug), self.slug)
    
    def get_introduction(self):
        intro = open(os.path.join(self.tutorial.get_path(), self.introduction), "r")
        intro_contenu = intro.read()
        intro.close()
        
        return intro_contenu.decode('utf-8')
    
    def get_introduction_online(self):
        intro = open(os.path.join(self.tutorial.get_prod_path(), self.introduction+'.html'), "r")
        intro_contenu = intro.read()
        intro.close()
        
        return intro_contenu.decode('utf-8')
    
    def get_conclusion(self):
        
        conclu = open(os.path.join(self.tutorial.get_path(), self.conclusion), "r")
        conclu_contenu = conclu.read()
        conclu.close()
        
        return conclu_contenu.decode('utf-8')

    def get_conclusion_online(self):
        conclu = open(os.path.join(self.tutorial.get_prod_path(), self.conclusion+'.html'), "r")
        conclu_contenu = conclu.read()
        conclu.close()
        
        return conclu_contenu.decode('utf-8')

class Chapter(models.Model):

    '''A chapter, containing text'''
    class Meta:
        verbose_name = 'Chapitre'
        verbose_name_plural = 'Chapitres'

    # A chapter may belong to a part, that's where the difference between large
    # and small tutorials is.
    part = models.ForeignKey(Part, null=True, blank=True,
                             verbose_name='Partie parente')

    position_in_part = models.IntegerField('Position dans la partie',
                                           null=True, blank=True)

    image = models.ForeignKey(Image,
                              verbose_name='Image du chapitre',
                              blank=True, null=True)
    # This field is required in order to use pagination in chapters, see the
    # update_position_in_tutorial() method.
    position_in_tutorial = models.IntegerField('Position dans le tutoriel',
                                               null=True, blank=True)

    # If the chapter doesn't belong to a part, it's a small tutorial; we need
    # to bind informations about said tutorial directly
    tutorial = models.ForeignKey(Tutorial, null=True, blank=True,
                                 verbose_name='Tutoriel parent')

    title = models.CharField('Titre', max_length=80, blank=True)

    slug = models.SlugField(max_length=80)
    
    introduction = models.CharField('chemin relatif introduction',blank=True, null=True, max_length=200)
    
    conclusion = models.CharField('chemin relatif conclusion',blank=True, null=True, max_length=200)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Chapter, self).save(*args, **kwargs)
        
    def __unicode__(self):
        if self.tutorial:
            return u'<minituto \'{0}\'>'.format(self.tutorial.title)
        elif self.part:
            return u'<bigtuto \'{0}\', \'{1}\'>'.format \
                (self.part.tutorial.title, self.title)
        else:
            return u'<orphelin>'

    def get_absolute_url(self):
        if self.tutorial:
            return self.tutorial.get_absolute_url()

        elif self.part:
            return self.part.get_absolute_url() + '{0}/'.format(self.slug)

        else:
            return '/tutoriels/'
    
    def get_absolute_url_online(self):
        if self.tutorial:
            return self.tutorial.get_absolute_url_online()

        elif self.part:
            return self.part.get_absolute_url_online() + '{0}/'.format(self.slug)

        else:
            return '/tutoriels/'

    def get_extract_count(self):
        return Extract.objects.all().filter(chapter__pk=self.pk).count()

    def get_extracts(self):
        return Extract.objects.all()\
            .filter(chapter__pk=self.pk)\
            .order_by('position_in_chapter')

    def get_tutorial(self):
        if self.part:
            return self.part.tutorial
        return self.tutorial

    def update_position_in_tutorial(self):
        '''
        Update the position_in_tutorial field, but don't save it ; you have
        to call save() method manually if you want to save the new computed
        position
        '''
        position = 1
        for part in self.part.tutorial.get_parts():
            if part.position_in_tutorial < self.part.position_in_tutorial:
                for chapter in part.get_chapters():
                    position += 1
            elif part == self.part:
                for chapter in part.get_chapters():
                    if chapter.position_in_part < self.position_in_part:
                        position += 1
        self.position_in_tutorial = position
    
    def get_path(self, relative=False):
        if relative:
            if self.tutorial:
                chapter_path = self.slug
            else:
                chapter_path = os.path.join(self.part.slug, self.slug)
        else:
            if self.tutorial:
                chapter_path = os.path.join(os.path.join(settings.REPO_PATH, self.tutorial.slug), self.slug)
            else:
                chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, self.part.tutorial.slug), self.part.slug), self.slug)
            
        return chapter_path
    
    def get_introduction(self):
        if self.introduction:
            if self.tutorial:
                path = os.path.join(self.tutorial.get_path(), self.introduction)
            else:
                path = os.path.join(self.part.tutorial.get_path(), self.introduction)
                
            if os.path.isfile(path):
                intro = open(path, "r")
                intro_contenu = intro.read()
                intro.close()
                
                return intro_contenu.decode('utf-8')
            else:
                return None
        else:
            return None
    
    def get_introduction_online(self):
        if self.introduction:
            if self.tutorial:
                path = os.path.join(self.tutorial.get_path(), self.introduction+'.html')
            else:
                path = os.path.join(self.part.tutorial.get_path(), self.introduction+'.html')
            
            if os.path.isfile(path):
                intro = open(path, "r")
                intro_contenu = intro.read()
                intro.close()
                
                return intro_contenu.decode('utf-8')
            else:
                return None
        else:
            return None
    
    def get_conclusion(self):
        if self.conclusion:
            if self.tutorial:
                path = os.path.join(self.tutorial.get_path(), self.conclusion)
            else:
                path = os.path.join(self.part.tutorial.get_path(), self.conclusion)
                
            if os.path.isfile(path):
                conclu = open(path, "r")
                conclu_contenu = conclu.read()
                conclu.close()
                
                return conclu_contenu.decode('utf-8')
            else:
                return None
        else:
            return None

    def get_conclusion_online(self):
        if self.conclusion:
            if self.tutorial:
                path = os.path.join(self.tutorial.get_path(), self.conclusion+'.html')
            else:
                path = os.path.join(self.part.tutorial.get_path(), self.conclusion+'.html')
                
            if os.path.isfile(path):
                conclu = open(path, "r")
                conclu_contenu = conclu.read()
                conclu.close()
                
                return conclu_contenu.decode('utf-8')
            else:
                return None
            
            return conclu_contenu.decode('utf-8')
        else:
            return None

class Extract(models.Model):

    '''A content extract from a chapter'''
    class Meta:
        verbose_name = 'Extrait'
        verbose_name_plural = 'Extraits'

    title = models.CharField('Titre', max_length=80)
    chapter = models.ForeignKey(Chapter, verbose_name='Chapitre parent')
    position_in_chapter = models.IntegerField('Position dans le chapitre')
    
    text = models.CharField('chemin relatif du texte',blank=True, null=True, max_length=200)

    def __unicode__(self):
        return u'<extrait \'{0}\'>'.format(self.title)

    def get_absolute_url(self):
        return '{0}#{1}-{2}'.format(
            self.chapter.get_absolute_url(),
            self.position_in_chapter,
            slugify(self.title)
        )
    
    def get_absolute_url_online(self):
        return '{0}#{1}-{2}'.format(
            self.chapter.get_absolute_url_online(),
            self.position_in_chapter,
            slugify(self.title)
        )
        
    def get_path(self, relative=False):
        if relative:
            if self.chapter.tutorial:
                chapter_path = self.chapter.slug
            else:
                chapter_path = os.path.join(self.chapter.part.slug, self.chapter.slug)
        else:
            if self.chapter.tutorial:
                chapter_path = os.path.join(os.path.join(settings.REPO_PATH, self.chapter.tutorial.slug), self.chapter.slug)
            else:
                chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, self.chapter.part.tutorial.slug), self.chapter.part.slug), self.chapter.slug)
            
        return os.path.join(chapter_path, slugify(self.title)+'.md') 
    
    def get_prod_path(self):
        if self.chapter.tutorial:
            chapter_path = os.path.join(os.path.join(settings.REPO_PATH_PROD, self.chapter.tutorial.slug), self.chapter.slug)
        else:
            chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH_PROD, self.chapter.part.tutorial.slug), self.chapter.part.slug), self.chapter.slug)
            
        return os.path.join(chapter_path, slugify(self.title)+'.md.html') 
    
    def get_text(self):
        if self.chapter.tutorial:
            path = os.path.join(self.chapter.tutorial.get_path(), self.text)
        else:
            path = os.path.join(self.chapter.part.tutorial.get_path(), self.text)
            
        if os.path.isfile(path):
            text = open(path, "r")
            text_contenu = text.read()
            text.close()
            
            return text_contenu.decode('utf-8')
        else:
            return None
    
    def get_text_online(self):
        
        if self.chapter.tutorial:
            path = os.path.join(self.chapter.tutorial.get_prod_path(), self.text+'.html')
        else:
            path = os.path.join(self.chapter.part.tutorial.get_prod_path(), self.text+'.html')
        
        if os.path.isfile(path):
            text = open(path, "r")
            text_contenu = text.read()
            text.close()
            
            return text_contenu.decode('utf-8')
        else:
            return None

    
class Validation(models.Model):
    '''Tutorial validation'''
    class Meta:
        verbose_name = 'Validation'
        verbose_name_plural = 'Validations'
    
    tutorial = models.ForeignKey(Tutorial, null=True, blank=True,
                                 verbose_name='Tutoriel proposé')
    version = models.CharField('Sha1 de la version',
                                  blank=True, null=True, max_length=80)
    date_proposition = models.DateTimeField('Date de proposition')
    comment_authors = models.TextField('Commentaire de l\'auteur')
    validator = models.ForeignKey(User,
                                verbose_name='Validateur',
                                related_name='author_validations',
                                blank=True, null=True)
    date_reserve = models.DateTimeField('Date de réservation', 
                                           blank=True, null=True)
    date_validation = models.DateTimeField('Date de validation', 
                                           blank=True, null=True)
    comment_validator = models.TextField('Commentaire du validateur', 
                                         blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    def __unicode__(self):
        return self.tutorial.title
    
    def is_pending(self):
        return self.status == 'PENDING'
    
    def is_pending_valid(self):
        return self.status == 'PENDING_V'
    
    def is_accept(self):
        return self.status == 'ACCEPT'
    
    def is_reject(self):
        return self.status == 'REJECT'
