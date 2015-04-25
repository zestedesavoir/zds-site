# coding: utf-8

from datetime import datetime

from zds.tutorialv2.models import init_new_repo

import factory

from zds.tutorialv2.models import PublishableContent, Validation, ContentReaction, Container, Extract
from zds.utils.models import SubCategory, Licence
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.tutorialv2.utils import publish_content

text_content = u'Ceci est un texte bidon, **avec markown**'


class PublishableContentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PublishableContent

    title = factory.Sequence(lambda n: 'Mon contenu No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du contenu No{0}'.format(n))
    type = 'TUTORIAL'
    creation_date = datetime.now()

    @classmethod
    def _prepare(cls, create, **kwargs):
        auths = []
        if "author_list" in kwargs:
            auths = kwargs.pop("author_list")

        publishable_content = super(PublishableContentFactory, cls)._prepare(create, **kwargs)
        for auth in auths:
            publishable_content.authors.add(auth)
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


class PublishedContentFactory(PublishableContentFactory):

    @classmethod
    def _prepare(cls, create, **kwargs):
        """create a new PublishableContent and then publish it.
        """

        content = super(PublishedContentFactory, cls)._prepare(create, **kwargs)
        published = publish_content(content, content.load_version(), True)

        content.public_version = published
        content.save()

        return content


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
