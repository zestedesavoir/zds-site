# coding: utf-8

from django.db import models


class SearchIndexTag(models.Model):
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    title = models.CharField('Titre', max_length=80)


class SearchIndexAuthors(models.Model):
    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

    username = models.CharField('Pseudo', max_length=80)


class SearchIndexContent(models.Model):

    class Meta:
        verbose_name = 'SearchIndexContent'
        verbose_name_plural = 'SearchIndexContents'

    publishable_content = models.ForeignKey('tutorialv2.PublishableContent', verbose_name='content',
                                            related_name='search_index_content_publishable_content', db_index=False,
                                            on_delete=models.SET_NULL, null=True)

    title = models.CharField('Titre', max_length=200)
    description = models.TextField('Description', null=True, blank=True)

    pub_date = models.DateTimeField('Date de création', auto_now_add=True)
    update_date = models.DateTimeField('Date de mise à jours', blank=True, null=True)

    licence = models.CharField('Licence du contenu', max_length=80)
    url_image = models.CharField('L\'adresse vers l\'image du contenu', max_length=200, null=True, blank=True)

    tags = models.ManyToManyField(SearchIndexTag, verbose_name='Tags', null=True, blank=True, db_index=True)
    authors = models.ManyToManyField(SearchIndexAuthors, verbose_name='Authors', db_index=True)

    url_to_redirect = models.CharField('Adresse pour rediriger', max_length=200)

    introduction = models.TextField('Introduction', null=True, blank=True)
    conclusion = models.TextField('Conclusion', null=True, blank=True)

    keywords = models.TextField('Mots clés du contenu')

    type = models.CharField('Type de contenu', max_length=80)


class SearchIndexContainer(models.Model):

    class Meta:
        verbose_name = 'SearchIndexContainer'
        verbose_name_plural = 'SearchIndexContainers'

    search_index_content = models.ForeignKey(SearchIndexContent, verbose_name='content',
                                             related_name='container_search_index_content', db_index=True)

    title = models.CharField('Titre', max_length=80)

    url_to_redirect = models.CharField('Adresse pour rediriger', max_length=200)

    introduction = models.TextField('Introduction', null=True, blank=True)
    conclusion = models.TextField('Conclusion', null=True, blank=True)

    level = models.CharField('level', max_length=80)

    keywords = models.TextField('Mots clés du contenu')


class SearchIndexExtract(models.Model):

    class Meta:
        verbose_name = 'SearchIndexExtract'
        verbose_name_plural = 'SearchIndexExtracts'

    title = models.CharField('Titre', max_length=80)

    search_index_content = models.ForeignKey(SearchIndexContent, verbose_name='content',
                                             related_name='extract_search_index_content', db_index=True)

    url_to_redirect = models.CharField('Adresse pour rediriger', max_length=200)

    extract_content = models.TextField('Contenu', null=True, blank=True)

    keywords = models.TextField('Mots clés du contenu')
