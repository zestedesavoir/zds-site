# coding: utf-8

from datetime import datetime
import factory
from git.repo import Repo

import json as json_writer
import os
from zds.article.models import Article, Reaction, \
    Validation, Licence
from zds.utils.articles import export_article
from zds.article.views import mep
from zds.utils.models import SubCategory


class ArticleFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Article

    title = factory.Sequence('Mon Article No{0}'.format)
    description = factory.Sequence('Description de l\'article No{0}'.format)
    text = 'text.md'
    create_at = datetime.now()

    @classmethod
    def _prepare(cls, create, **kwargs):
        article = super(ArticleFactory, cls)._prepare(create, **kwargs)

        path = article.get_path()
        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

        man = export_article(article)
        repo = Repo.init(path, bare=False)
        repo = Repo(path)

        f = open(os.path.join(path, 'manifest.json'), "w")
        f.write(json_writer.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
        f.close()
        f = open(os.path.join(path, article.text), "w")
        f.write(u'Test')
        f.close()
        repo.index.add(['manifest.json', article.text])
        cm = repo.index.commit("Init Article")

        article.sha_draft = cm.hexsha
        return article


class ReactionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Reaction

    ip_address = '192.168.3.1'
    text = u'Bonjour, je me présente, je m\'appelle l\'homme au texte bidonné'

    @classmethod
    def _prepare(cls, create, **kwargs):
        reaction = super(ReactionFactory, cls)._prepare(create, **kwargs)
        article = kwargs.pop('article', None)
        if article:
            article.last_reaction = reaction
            article.save()
        return reaction


class ValidationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Validation


class LicenceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Licence

    code = u'GNU_GPL'
    title = u'GNU General Public License'

    @classmethod
    def _prepare(cls, create, **kwargs):
        licence = super(LicenceFactory, cls)._prepare(create, **kwargs)
        return licence


class PublishedArticleFactory(ArticleFactory):
    FACTORY_FOR = Article

    @classmethod
    def _prepare(cls, create, **kwargs):
        article = super(PublishedArticleFactory, cls)._prepare(create, **kwargs)
        mep(article, article.sha_draft)
        article.sha_public = article.sha_draft
        article.pubdate = datetime.now()
        article.save()
        return article


class SubCategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = SubCategory

    title = factory.Sequence('Sous-Categorie {0} pour l\'article'.format)
    subtitle = factory.Sequence('Sous titre de Sous-Categorie {0} pour l\'article'.format)
    slug = factory.Sequence('sous-categorie-{0}'.format)
