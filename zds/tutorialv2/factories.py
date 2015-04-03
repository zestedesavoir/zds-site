# coding: utf-8

from datetime import datetime

import factory

from zds.tutorialv2.models import PublishableContent, Validation, ContentReaction, Container, Extract, init_new_repo
from zds.utils.models import SubCategory, Licence
from zds.gallery.factories import GalleryFactory, UserGalleryFactory

text_content = u'Ceci est un texte bidon'


class PublishableContentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PublishableContent

    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du Tutoriel No{0}'.format(n))
    type = 'TUTORIAL'
    creation_date = datetime.now()

    @classmethod
    def _prepare(cls, create, **kwargs):
        publishable_content = super(PublishableContentFactory, cls)._prepare(create, **kwargs)

        publishable_content.gallery = GalleryFactory()
        for author in publishable_content.authors.all():
            UserGalleryFactory(user=author, gallery=publishable_content.gallery)

        init_new_repo(publishable_content, text_content, text_content)

        return publishable_content


class ContainerFactory(factory.Factory):
    FACTORY_FOR = Container

    title = factory.Sequence(lambda n: 'Mon container No{0}'.format(n + 1))

    @classmethod
    def _prepare(cls, create, **kwargs):
        db_object = kwargs.pop('db_object', None)
        parent = kwargs.pop('parent', None)

        sha = parent.repo_add_container(kwargs['title'], text_content, text_content)
        container = parent.children[-1]

        if db_object:
            db_object.sha_draft = sha
            db_object.save()

        return container


class ExtractFactory(factory.Factory):
    FACTORY_FOR = Extract
    title = factory.Sequence(lambda n: 'Mon extrait No{0}'.format(n + 1))

    @classmethod
    def _prepare(cls, create, **kwargs):
        db_object = kwargs.pop('db_object', None)
        parent = kwargs.pop('container', None)

        sha = parent.repo_add_extract(kwargs['title'], text_content)
        extract = parent.children[-1]

        if db_object:
            db_object.sha_draft = sha
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

    code = factory.Sequence(lambda n: 'bidon-no{0}'.format(n + 1))
    title = factory.Sequence(lambda n: 'Licence bidon no{0}'.format(n + 1))

    @classmethod
    def _prepare(cls, create, **kwargs):
        licence = super(LicenceFactory, cls)._prepare(create, **kwargs)
        return licence
