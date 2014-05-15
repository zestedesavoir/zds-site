# coding: utf-8

import os
import string
import uuid

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models

from model_utils.managers import InheritanceManager


def image_path_category(instance, filename):
    """Return path to an image."""
    ext = filename.split('.')[-1]
    filename = u'{}.{}'.format(str(uuid.uuid4()), string.lower(ext))
    return os.path.join('categorie/normal', str(instance.pk), filename)


class Category(models.Model):

    """Common category for several concepts of the application."""
    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categories'

    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')

    slug = models.SlugField(max_length=80)

    def __unicode__(self):
        """Textual Category Form."""
        return self.title

    def get_tutos(self):
        from zds.tutorial.models import Tutorial
        scat = CategorySubCategory.objects.filter(
            category__pk=self.pk,
            is_main=True)
        msct = []
        for sc in scat:
            msct.append(sc.subcategory)
        return Tutorial.objects.filter(
            subcategory__in=msct).exclude(
            sha_public=None).exclude(
            sha_public='').all()

    def get_all_subcategories(self):
        """Get all subcategories of a category (not main include)"""
        return CategorySubCategory.objects \
            .filter(category__in=[self]) \
            .all()

    def get_subcategories(self):
        """Get only main subcategories of a category."""
        return CategorySubCategory.objects \
            .filter(category__in=[self], is_main=True)\
            .all()


class SubCategory(models.Model):

    """Common subcategory for several concepts of the application."""
    class Meta:
        verbose_name = 'Sous-categorie'
        verbose_name_plural = 'Sous-categories'

    title = models.CharField('Titre', max_length=80)
    subtitle = models.CharField('Sous-titre', max_length=200)

    image = models.ImageField(
        upload_to=image_path_category,
        blank=True,
        null=True)

    slug = models.SlugField(max_length=80)

    def __unicode__(self):
        """Textual Category Form."""
        return self.title

    def get_tutos(self):
        from zds.tutorial.models import Tutorial
        return Tutorial.objects.filter(
            subcategory__in=[self]).exclude(
            sha_public=None).exclude(
            sha_public='').all()

    def get_absolute_url_tutorial(self):
        return reverse('zds.tutorial.views.index') + '?tag={}'.format(self.slug)

    def get_absolute_url_article(self):
        return reverse('zds.article.views.index') + '?tag={}'.format(self.slug)


class CategorySubCategory(models.Model):

    """ManyToMany between Category and SubCategory but save a boolean to know
    if category is his main category."""
    class Meta:
        verbose_name = 'Hierarchie catégorie'
        verbose_name_plural = 'Hierarchies catégories'

    category = models.ForeignKey(Category, verbose_name='Catégorie')
    subcategory = models.ForeignKey(SubCategory, verbose_name='Sous-Catégorie')
    is_main = models.BooleanField('Est la catégorie principale', default=True)

    def __unicode__(self):
        """Textual Link Form."""
        if self.is_main:
            return u'[{0}][main]: {1}'.format(
                self.category.title,
                self.subcategory.title)
        else:
            return u'[{0}]: {1}'.format(
                self.category.title,
                self.subcategory.title)


class Licence(models.Model):

    """Publication licence."""
    class Meta:
        verbose_name = 'Licence'
        verbose_name_plural = 'Licences'

    code = models.CharField('Code', max_length=20)
    title = models.CharField('Titre', max_length=80)
    description = models.TextField('Description')

    def __unicode__(self):
        """Textual Licence Form."""
        return self.title


class Comment(models.Model):

    """Comment in forum, articles, tutorial, chapter, etc."""
    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'

    objects = InheritanceManager()

    author = models.ForeignKey(User, verbose_name='Auteur',
                               related_name='comments')
    editor = models.ForeignKey(User, verbose_name='Editeur',
                               related_name='comments-editor',
                               null=True, blank=True)
    ip_address = models.CharField('Adresse IP de l\'auteur ', max_length=15)

    position = models.IntegerField('Position')

    text = models.TextField('Texte')
    text_html = models.TextField('Texte en Html')

    like = models.IntegerField('Likes', default=0)
    dislike = models.IntegerField('Dislikes', default=0)

    pubdate = models.DateTimeField('Date de publication', auto_now_add=True)
    update = models.DateTimeField('Date d\'édition', null=True, blank=True)

    is_visible = models.BooleanField('Est visible', default=True)
    text_hidden = models.CharField(
        'Texte de masquage ',
        max_length=80,
        default='')

    def get_like_count(self):
        """Gets number of like for the post."""
        return CommentLike.objects.filter(comments__pk=self.pk).count()

    def get_dislike_count(self):
        """Gets number of dislike for the post."""
        return CommentDislike.objects.filter(comments__pk=self.pk).count()


class Alert(models.Model):
    """Alerts on all kinds of Comments"""

    ARTICLE = 'A'
    FORUM = 'F'
    TUTORIAL = 'T'
    SCOPE_CHOICES = (
            (ARTICLE, 'Commentaire d\'article'),
            (FORUM, 'Forum'),
            (TUTORIAL, 'Commentaire de tuto'),
    )

    author = models.ForeignKey(User,
                               verbose_name='Auteur',
                               related_name='alerts')
    comment = models.ForeignKey(Comment,
                               verbose_name='Commentaire',
                               related_name='alerts')
    scope = models.CharField(max_length=1, choices=SCOPE_CHOICES)
    text = models.TextField('Texte d\'alerte')
    pubdate = models.DateTimeField('Date de publication')
    
    def get_comment(self):
        return Comment.objects.get(id=self.comment.id)

    def get_comment_subclass(self):
        """
        Used to retrieve comment URLs (simple call to get_absolute_url doesn't
        work: objects are retrived as Comment and not subclasses)
        As real Comment implementation (subclasses) can't be hard-coded due to
        unresolvable import loops, use InheritanceManager from
        django-model-utils.
        """
        return Comment.objects.get_subclass(id=self.comment.id)

    def __unicode__(self):
        return u'{0}'.format(self.text)

    class Meta:
        verbose_name = 'Alerte'
        verbose_name_plural = 'Alertes'


class CommentLike(models.Model):

    """Set of like comments."""
    class Meta:
        verbose_name = 'Ce message est utile'
        verbose_name_plural = 'Ces messages sont utiles'

    comments = models.ForeignKey(Comment)
    user = models.ForeignKey(User, related_name='post_liked')


class CommentDislike(models.Model):

    """Set of dislike comments."""
    class Meta:
        verbose_name = 'Ce message est inutile'
        verbose_name_plural = 'Ces messages sont inutiles'

    comments = models.ForeignKey(Comment)
    user = models.ForeignKey(User, related_name='post_disliked')
