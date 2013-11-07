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
        