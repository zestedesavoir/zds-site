# coding: utf-8

from datetime import datetime
from git.repo import Repo
import json as json_writer
import os

import factory

from models import PublishableContent, Container, Extract, ContentReaction,\
    Validation
from zds.utils.models import SubCategory, Licence
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.utils.tutorials import export_tutorial
from zds.tutorial.views import mep

content = (
    u'Ceci est un contenu de tutoriel utile et à tester un peu partout\n\n '
    u'Ce contenu ira aussi bien dans les introductions, que dans les conclusions et les extraits \n\n '
    u'le gros intéret étant qu\'il renferme des images pour tester l\'execution coté pandoc \n\n '
    u'Exemple d\'image ![Ma pepite souris](http://blog.science-infuse.fr/public/souris.jpg)\n\n '
    u'\nExemple d\'image ![Image inexistante](http://blog.science-infuse.fr/public/inv_souris.jpg)\n\n '
    u'\nExemple de gif ![](http://corigif.free.fr/oiseau/img/oiseau_004.gif)\n\n '
    u'\nExemple de gif inexistant ![](http://corigif.free.fr/oiseau/img/ironman.gif)\n\n '
    u'Une image de type wikipedia qui fait tomber des tests ![](https://s.qwant.com/thumbr/?u=http%3A%2'
    u'F%2Fwww.blogoergosum.com%2Fwp-content%2Fuploads%2F2010%2F02%2Fwikipedia-logo.jpg&h=338&w=600)\n\n '
    u'Image dont le serveur n\'existe pas ![](http://unknown.image.zds)\n\n '
    u'\n Attention les tests ne doivent pas crasher \n\n \n\n \n\n '
    u'qu\'un sujet abandonné !\n\n ')

content_light = u'Un contenu light pour quand ce n\'est pas vraiment ça qui est testé'


class BigTutorialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PublishableContent

    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(
        lambda n: 'Description du Tutoriel No{0}'.format(n))
    type = 'TUTORIAL'
    create_at = datetime.now()
    introduction = 'introduction.md'
    conclusion = 'conclusion.md'

    @classmethod
    def _prepare(cls, create, **kwargs):

        light = kwargs.pop('light', False)
        tuto = super(BigTutorialFactory, cls)._prepare(create, **kwargs)
        path = tuto.get_path()
        real_content = content
        if light:
            real_content = content_light
        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

        man = export_tutorial(tuto)
        repo = Repo.init(path, bare=False)
        repo = Repo(path)

        f = open(os.path.join(path, 'manifest.json'), "w")
        f.write(json_writer.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
        f.close()
        f = open(os.path.join(path, tuto.introduction), "w")
        f.write(real_content.encode('utf-8'))
        f.close()
        f = open(os.path.join(path, tuto.conclusion), "w")
        f.write(real_content.encode('utf-8'))
        f.close()
        repo.index.add(['manifest.json', tuto.introduction, tuto.conclusion])
        cm = repo.index.commit("Init Tuto")

        tuto.sha_draft = cm.hexsha
        tuto.sha_beta = None
        tuto.gallery = GalleryFactory()
        for author in tuto.authors.all():
            UserGalleryFactory(user=author, gallery=tuto.gallery)
        return tuto


class MiniTutorialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PublishableContent

    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(
        lambda n: 'Description du Tutoriel No{0}'.format(n))
    type = 'TUTORIAL'
    create_at = datetime.now()
    introduction = 'introduction.md'
    conclusion = 'conclusion.md'

    @classmethod
    def _prepare(cls, create, **kwargs):
        light = kwargs.pop('light', False)
        tuto = super(MiniTutorialFactory, cls)._prepare(create, **kwargs)
        real_content = content

        if light:
            real_content = content_light
        path = tuto.get_path()
        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

        man = export_tutorial(tuto)
        repo = Repo.init(path, bare=False)
        repo = Repo(path)

        file = open(os.path.join(path, 'manifest.json'), "w")
        file.write(
            json_writer.dumps(
                man,
                indent=4,
                ensure_ascii=False).encode('utf-8'))
        file.close()
        file = open(os.path.join(path, tuto.introduction), "w")
        file.write(real_content.encode('utf-8'))
        file.close()
        file = open(os.path.join(path, tuto.conclusion), "w")
        file.write(real_content.encode('utf-8'))
        file.close()

        repo.index.add(['manifest.json', tuto.introduction, tuto.conclusion])
        cm = repo.index.commit("Init Tuto")

        tuto.sha_draft = cm.hexsha
        tuto.gallery = GalleryFactory()
        for author in tuto.authors.all():
            UserGalleryFactory(user=author, gallery=tuto.gallery)
        return tuto


class PartFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Container

    title = factory.Sequence(lambda n: 'Ma partie No{0}'.format(n))

    @classmethod
    def _prepare(cls, create, **kwargs):
        light = kwargs.pop('light', False)
        part = super(PartFactory, cls)._prepare(create, **kwargs)
        parent = kwargs.pop('tutorial', None)

        real_content = content
        if light:
            real_content = content_light

        path = part.get_path()
        repo = Repo(part.tutorial.get_path())

        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

        part.introduction = os.path.join(part.get_phy_slug(), 'introduction.md')
        part.conclusion = os.path.join(part.get_phy_slug(), 'conclusion.md')
        part.save()

        f = open(os.path.join(parent.get_path(), part.introduction), "w")
        f.write(real_content.encode('utf-8'))
        f.close()
        repo.index.add([part.introduction])
        f = open(os.path.join(parent.get_path(), part.conclusion), "w")
        f.write(real_content.encode('utf-8'))
        f.close()
        repo.index.add([part.conclusion])

        if parent:
            parent.save()

            man = export_tutorial(parent)
            f = open(os.path.join(parent.get_path(), 'manifest.json'), "w")
            f.write(
                json_writer.dumps(
                    man,
                    indent=4,
                    ensure_ascii=False).encode('utf-8'))
            f.close()

            repo.index.add(['manifest.json'])

        cm = repo.index.commit("Init Part")

        if parent:
            parent.sha_draft = cm.hexsha
            parent.save()

        return part


class ChapterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Container

    title = factory.Sequence(lambda n: 'Mon Chapitre No{0}'.format(n))

    @classmethod
    def _prepare(cls, create, **kwargs):

        light = kwargs.pop('light', False)
        chapter = super(ChapterFactory, cls)._prepare(create, **kwargs)
        parent = kwargs.pop('part', None)

        real_content = content
        if light:
            real_content = content_light
        path = chapter.get_path()

        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

        if parent:
            chapter.introduction = os.path.join(
                parent.get_phy_slug(),
                chapter.get_phy_slug(),
                'introduction.md')
            chapter.conclusion = os.path.join(
                parent.get_phy_slug(),
                chapter.get_phy_slug(),
                'conclusion.md')
            chapter.save()
            f = open(
                os.path.join(
                    parent.tutorial.get_path(),
                    chapter.introduction),
                "w")
            f.write(real_content.encode('utf-8'))
            f.close()
            f = open(
                os.path.join(
                    parent.tutorial.get_path(),
                    chapter.conclusion),
                "w")
            f.write(real_content.encode('utf-8'))
            f.close()
            parent.tutorial.save()
            repo = Repo(parent.tutorial.get_path())

            man = export_tutorial(parent.tutorial)
            f = open(
                os.path.join(
                    parent.parent.get_path(),
                    'manifest.json'),
                "w")
            f.write(
                json_writer.dumps(
                    man,
                    indent=4,
                    ensure_ascii=False).encode('utf-8'))
            f.close()

            repo.index.add([chapter.introduction, chapter.conclusion])
            repo.index.add(['manifest.json'])

        cm = repo.index.commit("Init Chapter")

        if parent:
            parent.parent.sha_draft = cm.hexsha
            parent.parent.save()
            parent.save()
            chapter.parent = parent

        return chapter


class ExtractFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Extract

    title = factory.Sequence(lambda n: 'Mon Extrait No{0}'.format(n))

    @classmethod
    def _prepare(cls, create, **kwargs):
        extract = super(ExtractFactory, cls)._prepare(create, **kwargs)
        container = kwargs.pop('container', None)
        if container:
            if container.parent is PublishableContent:
                container.parent.sha_draft = 'EXTRACT-AAAA'
                container.parent.save()
            elif container.parent.parent is PublishableContent:
                container.parent.parent.sha_draft = 'EXTRACT-AAAA'
                container.parent.parent.tutorial.save()

        return extract


class NoteFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Note

    ip_address = '192.168.3.1'
    text = 'Bonjour, je me présente, je m\'appelle l\'homme au texte bidonné'

    @classmethod
    def _prepare(cls, create, **kwargs):
        note = super(NoteFactory, cls)._prepare(create, **kwargs)
        note.pubdate = datetime.now()
        note.save()
        tutorial = kwargs.pop('tutorial', None)
        if tutorial:
            tutorial.last_note = note
            tutorial.save()
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


class PublishedMiniTutorial(MiniTutorialFactory):
    FACTORY_FOR = Tutorial

    @classmethod
    def _prepare(cls, create, **kwargs):
        tutorial = super(PublishedMiniTutorial, cls)._prepare(create, **kwargs)
        tutorial.pubdate = datetime.now()
        tutorial.sha_public = tutorial.sha_draft
        tutorial.source = ''
        tutorial.sha_validation = None
        mep(tutorial, tutorial.sha_draft)
        tutorial.save()
        return tutorial
