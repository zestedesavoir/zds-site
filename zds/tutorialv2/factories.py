# coding: utf-8

from datetime import datetime
from git.repo import Repo
import os

import factory

from models import PublishableContent, Container, Extract, ContentReaction,\
from zds.utils import slugify
from zds.utils.models import SubCategory, Licence
from zds.gallery.factories import GalleryFactory, UserGalleryFactory

text_content = u'Ceci est un texte bidon'


class PublishableContentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PublishableContent

    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du Tutoriel No{0}'.format(n))
    type = 'TUTORIAL'
    type = 'TUTORIAL'

    @classmethod
    def _prepare(cls, create, **kwargs):
        publishable_content = super(PublishableContentFactory, cls)._prepare(create, **kwargs)
        path = publishable_content.get_repo_path()
        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

    FACTORY_FOR = PublishableContent
    type = 'TUTORIAL'
        introduction = 'introduction.md'
        conclusion = 'conclusion.md'
        versioned_content = VersionedContent(None,
                                             publishable_content.type,
                                             publishable_content.title,
                                             slugify(publishable_content.title))
        versioned_content.introduction = introduction
        versioned_content.conclusion = conclusion

        Repo.init(path, bare=False)
        repo = Repo(path)

        versioned_content.dump_json()
        f = open(os.path.join(path, introduction), "w")
        f.write(text_content.encode('utf-8'))
        f.close()
        f = open(os.path.join(path, conclusion), "w")
        f.write(text_content.encode('utf-8'))
        f.close()
        repo.index.add(['manifest.json', introduction, conclusion])
        cm = repo.index.commit("Init Tuto")

        publishable_content.sha_draft = cm.hexsha
        publishable_content.sha_beta = None
        publishable_content.gallery = GalleryFactory()
        for author in publishable_content.authors.all():
            UserGalleryFactory(user=author, gallery=publishable_content.gallery)
        return publishable_content


class ContainerFactory(factory.Factory):
    FACTORY_FOR = Container

    title = factory.Sequence(lambda n: 'Mon container No{0}'.format(n+1))
    slug = ''

    @classmethod
    def _prepare(cls, create, **kwargs):
        db_object = kwargs.pop('db_object', None)
        container = super(ContainerFactory, cls)._prepare(create, **kwargs)
        container.parent.add_container(container, generate_slug=True)

        path = container.get_path()
        repo = Repo(container.top_container().get_path())
        top_container = container.top_container()

        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

        container.introduction = os.path.join(container.get_path(relative=True), 'introduction.md')
        container.conclusion = os.path.join(container.get_path(relative=True), 'conclusion.md')

        f = open(os.path.join(top_container.get_path(), container.introduction), "w")
        f.write(text_content.encode('utf-8'))
        f.close()
        f = open(os.path.join(top_container.get_path(), container.conclusion), "w")
        f.write(text_content.encode('utf-8'))
        f.close()
        repo.index.add([container.introduction, container.conclusion])

        top_container.dump_json()
            parent.save()
        repo.index.add(['manifest.json'])

        cm = repo.index.commit("Add container")

        if db_object:
            db_object.sha_draft = cm.hexsha
            db_object.save()

        return container


class ExtractFactory(factory.Factory):
    FACTORY_FOR = Extract

    title = factory.Sequence(lambda n: 'Mon extrait No{0}'.format(n+1))
    slug = ''

    @classmethod
    def _prepare(cls, create, **kwargs):
        db_object = kwargs.pop('db_object', None)
        extract = super(ExtractFactory, cls)._prepare(create, **kwargs)
        extract.container.add_extract(extract, generate_slug=True)

        extract.text = extract.get_path(relative=True)
        top_container = extract.container.top_container()
        repo = Repo(top_container.get_path())
        f = open(extract.get_path(), 'w')
        f.write(text_content.encode('utf-8'))
        f.close()

        repo.index.add([extract.text])

        top_container.dump_json()
        repo.index.add(['manifest.json'])

        cm = repo.index.commit("Add extract")

        if db_object:
            db_object.sha_draft = cm.hexsha
            db_object.save()

        return extract


class ContentReactionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ContentReaction

    ip_address = '192.168.3.1'
    text = 'Bonjour, je me présente, je m\'appelle l\'homme au texte bidonné'

    @classmethod
    def _prepare(cls, create, **kwargs):
        note = super(ContentReactionFactory, cls)._prepare(create, **kwargs)
        note.pubdate = datetime.now()
        note.save()
        content = kwargs.pop('tutorial', None)
        if content:
            content.last_note = note
            content.save()
        return note


class SubCategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = SubCategory

    title = factory.Sequence(lambda n: 'Sous-Categorie {0} pour Tuto'.format(n))
    subtitle = factory.Sequence(lambda n: 'Sous titre de Sous-Categorie {0} pour Tuto'.format(n))
    slug = factory.Sequence(lambda n: 'sous-categorie-{0}'.format(n))


class ValidationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Validation


class LicenceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Licence

    code = u'Licence bidon'
    title = u'Licence bidon'

    @classmethod
    def _prepare(cls, create, **kwargs):
        licence = super(LicenceFactory, cls)._prepare(create, **kwargs)
        return licence

    FACTORY_FOR = PublishableContent