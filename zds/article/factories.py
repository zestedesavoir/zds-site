# coding: utf-8

from datetime import datetime
import factory
from git.repo import Repo
try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

import json as json_writer
import os
from zds.article.models import Article, Reaction, \
    Validation
from zds.utils.articles import export_article


class ArticleFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Article

    title = factory.Sequence(lambda n: 'Mon Article No{0}'.format(n))
    description = factory.Sequence(
        lambda n: 'Description de l\'article No{0}'.format(n))
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


class VaidationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Validation
