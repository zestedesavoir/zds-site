# coding: utf-8
from django.db import models

class DateManager(models.Model):
    class Meta:
        verbose_name = 'Gestion de la date'
        verbose_name_plural = 'Gestion des dates'
        
    create_at = models.DateTimeField('Date de création', blank=True)
    pubdate = models.DateTimeField('Date de publication', blank=True, null=True)
    update = models.DateTimeField('Date de mise à jour', blank=True, null=True)
    
    def __unicode__(self):
        return '{0}|{1}|{2}'.format(self.create_at, self.update, self.pubdate )
    

class Alert(models.Model):
    class Meta :
        verbose_name = 'Alerte'
        verbose_name_plural = 'Alertes'
    
    text = models.TextField('Texte d\'alerte')
    pubdate = models.DateTimeField('Date de publication', blank=True, null=True)
    
    def __unicode__(self):
        return '{0}'.format(self.text)
    
class Version(models.Model):
    class Meta :
        verbose_name = 'Versions'
        verbose_name_plural = 'Version'
        
    public_version_number = models.IntegerField('Numéro de version publique', default=0)
    
    beta_version_number = models.IntegerField('Numéro de version en beta publique', default=0)
    beta_version_date = models.DateTimeField('Date d\'envoi en version Beta', blank=True, null=True)
    
    validation_version_number = models.IntegerField('Numéro de version en validation', default=0)
    validation_version_date = models.DateTimeField('Date d\'envoi en validation', blank=True, null=True)
    
    draft_version_number = models.IntegerField('Numéro de version de rédaction', default=0)
    
    def __unicode__(self):
        return 'public({0}), beta({1}), validation({2}), draft({3})'.format(self.public_version_number, self.beta_version_number, self.validation_version_number, self.draft_version_number)

class Category(models.Model):
    '''Une catégorie, qui correspond à la catégorie dans laquelle on peut ranger un projet (Site Web, Jeux vidéos, etc.)'''
    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'
        ordering = ('title',)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    
    def __unicode__(self):
        '''
        Textual Category Form
        '''
        return self.title
    
    def get_news(self):
        from lbp.news.models import News
        return News.objects.all().filter(category__in = [self])
    
    def get_news_count(self):
        from lbp.news.models import News
        return News.objects.all().filter(category__in = [self]).count()
    
    def get_project(self):
        from lbp.project.models import Project
        return Project.objects.all().filter(category__in = [self])
    
    def get_project_count(self):
        from lbp.project.models import Project
        return Project.objects.all().filter(category__in = [self]).count()
    
    def get_tuto(self):
        from lbp.tutorial.models import Tutorial
        return Tutorial.objects.all().filter(category__in = [self])
    
    def get_tuto_count(self):
        from lbp.tutorial.models import Tutorial
        return Tutorial.objects.all().filter(category__in = [self]).count()
    
    def get_news_url(self):
        return '/news/categorie/{0}/{1}'.format(self.pk, slugify(self.title))
    
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
        