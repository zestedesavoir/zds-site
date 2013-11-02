# encoding: utf-8

from django.db import models
from django.contrib.auth.models import User
from lbp.gallery.models import Image, Gallery, UserGallery
from lbp.utils.models import DateManager

#from lbp.actualite.models import Actualite

STATE_PUB = (
        ('PENDING', 'En construction'),
        ('ALPHA', 'Alpha'),
        ('BETA', 'Beta'),
        ('RC', 'Realease Candidate'),
        ('STABLE', 'Stable'),
    )
    
class BPlan(models.Model):
    '''
    Business plan of project
    '''
    short_description=models.TextField('Description Courte')
    long_description=models.TextField('Description Longue')
    roadmap = models.TextField('RoadMap')
    market_study = models.TextField('Etude de marché') #Forces, faiblesses, opportunités, menaces
    product = models.TextField('Produit') # Offre, Demande, Environnement
    pricing = models.TextField('Prix')
    promote = models.TextField('Communication')
    place = models.TextField('Ditribution') 
    strategy = models.TextField('Stratégie') #Segmentation, Ciblage, Positionnement
    
    def __unicode__(self):
        '''
        A textual form of business plan
        '''
        return self.pk
    
class Project(models.Model):
    '''
    Project, who contains projec't versions
    '''
    class Meta:
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'
        ordering = ('date__update',)

    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    bplan = models.ForeignKey(BPlan, 
                              verbose_name='Business Plan', 
                              blank=True, null=True)
    slug = models.SlugField(max_length=80)
    image = models.ForeignKey(Image, 
                              verbose_name='Image du projet', 
                              blank=True, null=True)
    gallery = models.ForeignKey(Gallery, 
                                verbose_name='Gallérie d\'images', 
                                blank=True, null=True)
    author = models.ForeignKey(User, verbose_name='Auteur',
                               related_name='projets')
    
    state = models.CharField(max_length=15, choices=STATE_PUB, default='PENDING')
    
    last_version = models.ForeignKey('Project', verbose_name='Version Précédente', blank=True, null=True)
    date = models.ForeignKey(DateManager, 
                                verbose_name='Date')
    
    categories = models.ManyToManyField('Category', related_name='projets+', blank=True)  # les catégories de métiers touchés par le projet
    technologies = models.ManyToManyField('Technology', related_name='projets+', blank=True)  # les technologies abordés pendant le projet
    plateforms = models.ManyToManyField('Plateform', related_name='projets+', blank=True)  # les plateformes visés par le projet
    
    def __unicode__(self):
        '''
        Project Textual form
        '''
        return self.titre
    def get_participants(self):
        '''
        Project participants
        '''
        return Participant.objects.all()\
            .filter(projet=self, user__isnull=False)

    def get_vacancies(self):
        '''
        Vacancies
        '''
        return Participant.objects.all()\
            .filter(projet=self, user__isnull=True)
            
    def is_followed(self, user=None):
        '''
        Check if the project is currently followed by the user. This method uses
        the ProjectFollowed objects.
        '''
        if user is None:
            user = get_current_user()

        try:
            ProjectFollowed.objects.get(project=self, user=user)
        except ProjectFollowed.DoesNotExist:
            return False
        return True

class ProjectFollowed(models.Model):
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)

class ProjectRead(models.Model):
    user = models.ForeignKey(User)
    project = models.ForeignKey(Project)    

class Fonction(models.Model):
    '''Une fonction, qui correspond aux différentes fonctions occupées dans un projet (chef de projet, graphistes, testeur, donateurs, etc.)'''
    class Meta:
        verbose_name = 'Fonction'
        verbose_name_plural = 'Fonctions'
        ordering = ('title',)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    create_at = models.DateTimeField('Date de création')
    pubdate = models.DateTimeField('Date de publication')
    update = models.DateTimeField('Date de mise à jour')
    public = models.BooleanField('Est publique')

    def __unicode__(self):
        '''
        Textual fonction form
        '''
        return self.title
    
class Category(models.Model):
    '''Une catégorie, qui correspond à la catégorie dans laquelle on peut ranger un projet (Site Web, Jeux vidéos, Amménagement, etc.)'''
    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'
        ordering = ('title',)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    criterias = models.ManyToManyField('Criteria', verbose_name='Critères d\'évaluation',
                               related_name='categories',
                               blank=True, null=True)
    
    def __unicode__(self):
        '''
        Textual Category Form
        '''
        return self.title

class Technology(models.Model):
    '''Une technologie, qui correspond, au domaine technique utilisé pour résoudre un problème (Java, Perçeuse, etc.)'''
    class Meta:
        verbose_name = 'Technologie'
        verbose_name_plural = 'Technologies'
        ordering = ('title',)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    public = models.BooleanField('Est publique')

    def __unicode__(self):
        '''
        Formulation textuelle d'une technologie
        '''
        if(self.public) :
            return self.title
        else :
            return u'{0} (Privé)'.format(self.title)

class Plateform(models.Model):
    '''Une plateforme, qui correspond à la plateforme ou au support sur lequel on travaille (Windows, Android, Extérieure, etc.)'''
    class Meta:
        verbose_name = 'Plateforme'
        verbose_name_plural = 'Plateformes'
        ordering = ('title',)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    public = models.BooleanField('Est publique')

    def __unicode__(self):
        '''
        Textual Plateform form
        '''
        if(self.public) :
            return self.title
        else :
            return u'{0} (Privé)'.format(self.title)

class Criteria(models.Model):
    '''Un critère, qui permet d'évaluer certains projets'''
    class Meta:
        verbose_name = 'Critère'
        verbose_name_plural = 'Critères'
        ordering = ('title',)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')
    public = models.BooleanField('Est publique')
    score_max = models.IntegerField('Score Maximum')
    
    def __unicode__(self):
        '''
        Formulation textuelle d'un critère
        '''
        if(self.public) :
            return self.title
        else :
            return u'{0} (Privé)'.format(self.titre)

class Evaluation(models.Model):
    '''Une évalutation, qui correspond à l'évaluation attribuée à un projet '''
    class Meta:
        verbose_name = 'Evaluation'
        verbose_name_plural = 'Evaluations'
    
    project = models.ForeignKey('Project')  # le projet concerné
    author = models.ForeignKey(User) #evaluation author
    criteria = models.ForeignKey('Criteria', verbose_name='Critère', related_name='evaluations')  # critère d'évaluation
    note = models.ForeignKey('Note', verbose_name='Note', related_name='evaluations+', blank=True)  # la note communautaire attribuée par les membres avec qui ont a travaillé
    comment = models.TextField('Commentaire')
    public = models.BooleanField('Est publique')

    def __unicode__(self):
        '''
        Formulation textuelle d'une évaluation
        '''
        if(self.publique) :
            return self.titre
        else :
            return u'{0} (Privé)'.format(self.titre)
        
class Note(models.Model):
    '''Une note, qui correspond aux types de notes qu'on attribue lors d'une évaluation'''
    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ('score',)
    code = models.CharField('Code', max_length=5)
    title = models.CharField('Titre', max_length=20)
    score = models.IntegerField('Score')
    

    def __unicode__(self):
        '''
        Formulation textuelle d'une note
        '''
        return u'"{0}" ({1})'.format(self.title, self.score)
    
class Participation(models.Model):
    '''Une participation, qui correspond aux participations à un projet'''
    class Meta:
        verbose_name = 'Participation'
        verbose_name_plural = 'participations'
    user = models.ForeignKey(User, verbose_name='Participant', related_name='participations')  # Utilisateur participant
    project = models.ForeignKey('Project', verbose_name='Projet', related_name='participations')  # Projet concerné
    fonction = models.ForeignKey('Fonction', verbose_name='Fonction', related_name='participations')  # Fonction dans laquelle ont participe au projet

    def __unicode__(self):
        '''
        Formulation textuelle d'une participation
        '''
        return u'{0} -> {1}'.format(self.user.username, self.projet.titre)
    
class CompetenceFonctionnelle(models.Model):
    '''Une compétence fonctionnelle, qui correspond à une compétence dans une fonction bien précise'''
    class Meta:
        verbose_name = 'Compétence Fonctionnelle'
        verbose_name_plural = 'Compétences Fonctionnelle'
    user = models.ForeignKey(User, verbose_name='Detenteur', related_name='fdcompetences')  # l'utilisateur compétent
    other = models.ForeignKey(User, verbose_name='Evaluateur', related_name='fecompetences')  # celui qui évalue la compétence
    fonction = models.ForeignKey('Fonction', verbose_name='Fonction', related_name='fcompetences')  # la fonction concerné
    notes = models.ManyToManyField('Note', verbose_name='Notes', related_name='fcompetences+', blank=True)  # la note communautaire attribuée par les membres avec qui ont a travaillé


    def __unicode__(self):
        '''
        Formulation textuelle d'une compétence fonctionnelle
        '''
        return u'{0} -> {1}'.format(self.user, self.fonction)

class CompetenceTechno(models.Model):
    '''Une compétence technique, qui correspond à une compétence dans une technologie bien précise'''
    class Meta:
        verbose_name = 'Compétence Technologique'
        verbose_name_plural = 'Compétences Technologique'
    user = models.ForeignKey(User, verbose_name='User', related_name='tdcompetences')  # l'utilisateur compétent
    other = models.ForeignKey(User, verbose_name='Evaluateur', related_name='tecompetences')  # celui qui évalue la compétence
    technology = models.ForeignKey('Technology', verbose_name='Technologie', related_name='tcompetences')  # la techno concernée
    notes = models.ManyToManyField('Note', verbose_name='Notes', related_name='tcompetences+', blank=True)  # la note communautaire attribuée par les membres avec qui ont a travaillé


    def __unicode__(self):
        '''
        Formulation textuelle d'une compétence technologique
        '''
        return u'{0} -> {1}'.format(self.user, self.fonction)
    
    
class CompetencePlateforme(models.Model):
    '''Une compétence technique, qui correspond à une compétence dans une plateforme bien précise'''
    class Meta:
        verbose_name = 'Compétence sur Plateforme'
        verbose_name_plural = 'Compétences sur Plateforme'
    user = models.ForeignKey(User, verbose_name='User', related_name='pdcompetences')  # l'utilisateur compétent
    other = models.ForeignKey(User, verbose_name='Evaluateur', related_name='pecompetences')  # celui qui évalue la compétence
    plateform = models.ForeignKey('Plateform', verbose_name='Plateforme', related_name='pcompetences')  # la plateforme concernée
    notes = models.ManyToManyField(Note, verbose_name='Notes', related_name='pcompetences+', blank=True)  # la note communautaire attribuée par les membres avec qui ont a travaillé


    def __unicode__(self):
        '''
        Formulation textuelle d'une compétence plateforme
        '''
        return u'{0} -> {1}'.format(self.user, self.fonction)
