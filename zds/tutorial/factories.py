# coding: utf-8

from datetime import datetime
from git.repo import Repo
import json as json_writer
import os

import factory

from zds.tutorial.models import PubliableContent, Part, Chapter, Extract, Note,\
    Validation
from zds.utils.models import SubCategory, Licence
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.utils.tutorials import export_tutorial

content = (
    u'Ceci est un contenu de tutoriel utile et à tester un peu partout'
    u'Ce contenu ira aussi bien dans les introductions, que dans les conclusions et les extraits '
    u'le gros intéret étant qu\'il renferme des images pour tester l\'execution coté pandoc '
    u'Exemple d\'image ![Ma pepite souris](http://blog.science-infuse.fr/public/souris.jpg)'
    u'\nExemple d\'image ![Image inexistante](http://blog.science-infuse.fr/public/inv_souris.jpg)'
    u'\nExemple de gif ![](http://corigif.free.fr/oiseau/img/oiseau_004.gif)'
    u'\nExemple de gif inexistant ![](http://corigif.free.fr/oiseau/img/ironman.gif)'
    u'Une image de type wikipedia qui fait tomber des tests ![](https://s.qwant.com/thumbr/?u=http%3A%2'
    u'F%2Fwww.blogoergosum.com%2Fwp-content%2Fuploads%2F2010%2F02%2Fwikipedia-logo.jpg&h=338&w=600)'
    u'Image dont le serveur n\'existe pas ![](http://unknown.image.zds)'
    u'\n Attention les tests ne doivent pas crasher '
    u'qu\'un sujet abandonné !')

content_light = u'Un contenu light pour quand ce n\'est pas vraiment ça qui est testé'


class BigTutorialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PubliableContent

    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(
        lambda n: 'Description du Tutoriel No{0}'.format(n))
    type = 'BIG'
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
    FACTORY_FOR = PubliableContent

    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(
        lambda n: 'Description du Tutoriel No{0}'.format(n))
    type = 'MINI'
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
    FACTORY_FOR = Part

    title = factory.Sequence(lambda n: 'Ma partie No{0}'.format(n))

    @classmethod
    def _prepare(cls, create, **kwargs):
        light = kwargs.pop('light', False)
        part = super(PartFactory, cls)._prepare(create, **kwargs)
        tutorial = kwargs.pop('tutorial', None)

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

        f = open(os.path.join(tutorial.get_path(), part.introduction), "w")
        f.write(real_content.encode('utf-8'))
        f.close()
        repo.index.add([part.introduction])
        f = open(os.path.join(tutorial.get_path(), part.conclusion), "w")
        f.write(real_content.encode('utf-8'))
        f.close()
        repo.index.add([part.conclusion])

        if tutorial:
            tutorial.save()

            man = export_tutorial(tutorial)
            f = open(os.path.join(tutorial.get_path(), 'manifest.json'), "w")
            f.write(
                json_writer.dumps(
                    man,
                    indent=4,
                    ensure_ascii=False).encode('utf-8'))
            f.close()

            repo.index.add(['manifest.json'])

        cm = repo.index.commit("Init Part")

        if tutorial:
            tutorial.sha_draft = cm.hexsha
            tutorial.save()

        return part


class ChapterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Chapter

    title = factory.Sequence(lambda n: 'Mon Chapitre No{0}'.format(n))

    @classmethod
    def _prepare(cls, create, **kwargs):

        light = kwargs.pop('light', False)
        chapter = super(ChapterFactory, cls)._prepare(create, **kwargs)
        tutorial = kwargs.pop('tutorial', None)
        part = kwargs.pop('part', None)

        real_content = content
        if light:
            real_content = content_light
        path = chapter.get_path()

        if not os.path.isdir(path):
            os.makedirs(path, mode=0o777)

        if tutorial:
            chapter.introduction = ''
            chapter.conclusion = ''
            tutorial.save()
            repo = Repo(tutorial.get_path())

            man = export_tutorial(tutorial)
            f = open(os.path.join(tutorial.get_path(), 'manifest.json'), "w")
            f.write(
                json_writer.dumps(
                    man,
                    indent=4,
                    ensure_ascii=False).encode('utf-8'))
            f.close()
            repo.index.add(['manifest.json'])

        elif part:
            chapter.introduction = os.path.join(
                part.get_phy_slug(),
                chapter.get_phy_slug(),
                'introduction.md')
            chapter.conclusion = os.path.join(
                part.get_phy_slug(),
                chapter.get_phy_slug(),
                'conclusion.md')
            chapter.save()
            f = open(
                os.path.join(
                    part.tutorial.get_path(),
                    chapter.introduction),
                "w")
            f.write(real_content.encode('utf-8'))
            f.close()
            f = open(
                os.path.join(
                    part.tutorial.get_path(),
                    chapter.conclusion),
                "w")
            f.write(real_content.encode('utf-8'))
            f.close()
            part.tutorial.save()
            repo = Repo(part.tutorial.get_path())

            man = export_tutorial(part.tutorial)
            f = open(
                os.path.join(
                    part.tutorial.get_path(),
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

        if tutorial:
            tutorial.sha_draft = cm.hexsha
            tutorial.save()
            chapter.tutorial = tutorial
        elif part:
            part.tutorial.sha_draft = cm.hexsha
            part.tutorial.save()
            part.save()
            chapter.part = part

        return chapter


class ExtractFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Extract

    title = factory.Sequence(lambda n: 'Mon Extrait No{0}'.format(n))

    @classmethod
    def _prepare(cls, create, **kwargs):
        extract = super(ExtractFactory, cls)._prepare(create, **kwargs)
        chapter = kwargs.pop('chapter', None)
        if chapter:
            if chapter.tutorial:
                chapter.tutorial.sha_draft = 'EXTRACT-AAAA'
                chapter.tutorial.save()
            elif chapter.part:
                chapter.part.tutorial.sha_draft = 'EXTRACT-AAAA'
                chapter.part.tutorial.save()

        return extract


class NoteFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Note

    ip_address = '192.168.3.1'
    text = 'Bonjour, je me présente, je m\'appelle l\'homme au texte bidonné'

    @classmethod
    def _prepare(cls, create, **kwargs):
        note = super(NoteFactory, cls)._prepare(create, **kwargs)
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


class VaidationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Validation


class LicenceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Licence

    code = u'Licence bidon'
    title = u'Licence bidon'

    @classmethod
    def _prepare(cls, create, **kwargs):
        licence = super(LicenceFactory, cls)._prepare(create, **kwargs)
        return licence
