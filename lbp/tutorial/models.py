# coding: utf-8

from os import path
import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from lbp.utils.models import DateManager, Version, Category, Licence
from lbp.gallery.models import Image, Gallery
from django.core.urlresolvers import reverse
from lbp.utils import slugify

TYPE_CHOICES = (
        ('MINI', 'Mini-tuto'),
        ('BIG', 'Big tuto'),
        ('ARTICLE', 'Article'),
    )

class Tutorial(models.Model):

    '''A tutorial, large or small'''
    class Meta:
        verbose_name = 'Tutoriel'
        verbose_name_plural = 'Tutoriels'

    title = models.CharField('Titre', max_length=80)
    description = models.CharField('Description', max_length=200)
    authors = models.ManyToManyField(User, verbose_name='Auteurs')
    
    category = models.ManyToManyField(Category, 
                                verbose_name='Categorie', 
                                blank=True, null=True)
    
    slug = models.SlugField(max_length=80)
    
    image = models.ForeignKey(Image, 
                              verbose_name='Image du tutoriel', 
                              blank=True, null=True)
    
    gallery = models.ForeignKey(Gallery, 
                                verbose_name='Gallérie d\'images', 
                                blank=True, null=True)

    date = models.ForeignKey(DateManager, 
                                verbose_name='Date',
                                blank=True, null=True)
    
    version = models.ForeignKey(Version, 
                                verbose_name='Version',
                                blank=True, null=True)
    
    licence = models.ForeignKey(Licence, 
                                verbose_name='Licence',
                                blank=True, null=True)
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('lbp.tutorial.views.view_tutorial', args=[
            self.pk, slugify(self.title)
        ])

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
        return self.version.beta_version_number>0
    
    def in_validation(self):
        return self.version.validation_version_number>0
    
    def in_drafting(self):
        return self.version.draft_version_number>0
    
    def on_line(self):
        return self.version.public_version_number>0
    
    def is_mini(self):
        b=self.type == 'MINI'
        return b
    
    def is_big(self):
        return self.type == 'BIG'
    
    def is_article(self):
        return self.type == 'ARTICLE'
    
    def get_path(self):
        return os.path.join(settings.REPO_PATH, self.slug)
    
    def get_introduction(self):
        intro=open(os.path.join(self.get_path(), 'introduction.md'), "r")
        intro_contenu=intro.read()
        intro.close()
        
        return intro_contenu.decode('utf-8')
    
    def get_conclusion(self):
        conclu=open(os.path.join(self.get_path(), 'conclusion.md'), "r")
        conclu_contenu=conclu.read()
        conclu.close()
        
        return conclu_contenu.decode('utf-8')
        
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
                            
        super(Tutorial, self).save(*args, **kwargs)


    
def get_last_tutorials():
    tutorials = Tutorial.objects.all()\
        .filter(version__public_version_number__gte=1)\
        .order_by('-date__pubdate')[:5]
        
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

    
    # The list of chapters is shown between introduction and conclusion

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Part, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'<Partie pour {0}, {1}>'.format\
            (self.tutorial.title, self.position_in_tutorial)

    def get_absolute_url(self):
        return reverse('lbp.tutorial.views.view_part', args=[
            self.tutorial.pk,
            self.tutorial.slug,
            self.slug,
        ])

    def get_chapters(self):
        return Chapter.objects.all()\
            .filter(part=self).order_by('position_in_part')

    def get_path(self):
        return os.path.join(os.path.join(settings.REPO_PATH, self.tutorial.slug), self.slug)
    
    def get_introduction(self):
        intro=open(os.path.join(self.get_path(), 'introduction.md'), "r")
        intro_contenu=intro.read()
        intro.close()
        
        return intro_contenu.decode('utf-8')
    
    def get_conclusion(self):
        conclu=open(os.path.join(self.get_path(), 'conclusion.md'), "r")
        conclu_contenu=conclu.read()
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
    
    def get_path(self):
        if self.tutorial:
            chapter_path = os.path.join(os.path.join(settings.REPO_PATH, self.tutorial.slug), self.slug)
        else:
            chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, self.part.tutorial.slug), self.part.slug), self.slug)
            
        return chapter_path
    
    def get_introduction(self):
        intro=open(os.path.join(self.get_path(), 'introduction.md'), "r")
        intro_contenu=intro.read()
        intro.close()
        
        return intro_contenu.decode('utf-8')
    
    def get_conclusion(self):
        conclu=open(os.path.join(self.get_path(), 'conclusion.md'), "r")
        conclu_contenu=conclu.read()
        conclu.close()
        
        return conclu_contenu.decode('utf-8')
    
class Extract(models.Model):

    '''A content extract from a chapter'''
    class Meta:
        verbose_name = 'Extrait'
        verbose_name_plural = 'Extraits'

    title = models.CharField('Titre', max_length=80)
    chapter = models.ForeignKey(Chapter, verbose_name='Chapitre parent')
    position_in_chapter = models.IntegerField('Position dans le chapitre')

    def __unicode__(self):
        return u'<extrait \'{0}\'>'.format(self.title)

    def get_absolute_url(self):
        return '{0}#{1}-{2}'.format(
            self.chapter.get_absolute_url(),
            self.position_in_chapter,
            slugify(self.title)
        )
        
    def get_path(self):
        if self.chapter.tutorial:
            chapter_path = os.path.join(os.path.join(settings.REPO_PATH, self.chapter.tutorial.slug), self.chapter.slug)
        else:
            chapter_path = os.path.join(os.path.join(os.path.join(settings.REPO_PATH, self.chapter.part.tutorial.slug), self.chapter.part.slug), self.chapter.slug)
            
        return os.path.join(chapter_path, slugify(self.title)) 
    
    def get_text(self):
        text=open(self.get_path(), "r")
        text_contenu=text.read()
        text.close()
        
        return text_contenu.decode('utf-8')