# coding: utf-8

from datetime import datetime
from git.repo import Repo
import json
import os

import factory

from zds.tutorial.models import Tutorial, Part, Chapter, Extract, Note,\
    Validation
from zds.utils.tutorials import export_tutorial


class BigTutorialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Tutorial
    
    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du Tutoriel No{0}'.format(n))
    type='BIG'
    create_at = datetime.now()
    introduction = 'introduction.md'
    conclusion = 'conclusion.md'


    @classmethod
    def _prepare(cls, create, **kwargs):
        tuto = super(BigTutorialFactory, cls)._prepare(create, **kwargs)
        path = tuto.get_path()
        if not os.path.isdir(path):
            os.makedirs(path, mode=0777)
        
        man = export_tutorial(tuto)
        repo = Repo.init(path, bare=False)
        repo = Repo(path)
        
        f = open(os.path.join(path,'manifest.json'), "w")
        f.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
        f.close()
        f = open(os.path.join(path,tuto.introduction), "w")
        f.write(u'Test')
        f.close()
        f = open(os.path.join(path,tuto.conclusion), "w")
        f.write(u'Test')
        f.close()
        repo.index.add(['manifest.json', tuto.introduction, tuto.conclusion])
        cm=repo.index.commit("Init Tuto")
        
        tuto.sha_draft=cm.hexsha
        return tuto
    
class MiniTutorialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Tutorial
    
    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du Tutoriel No{0}'.format(n))
    type='MINI'
    create_at = datetime.now()
    introduction = 'introduction.md'
    conclusion = 'conclusion.md'
    
    @classmethod
    def _prepare(cls, create, **kwargs):
        tuto = super(MiniTutorialFactory, cls)._prepare(create, **kwargs)
        path = tuto.get_path()
        if not os.path.isdir(path):
            os.makedirs(path, mode=0777)
        
        man = export_tutorial(tuto)
        repo = Repo.init(path, bare=False)
        repo = Repo(path)
        
        file = open(os.path.join(path,'manifest.json'), "w")
        file.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
        file.close()
        file = open(os.path.join(path,tuto.introduction), "w")
        file.write(u'Test')
        file.close()
        file = open(os.path.join(path,tuto.conclusion), "w")
        file.write(u'Test')
        file.close()
        
        repo.index.add(['manifest.json',tuto.introduction, tuto.conclusion])
        cm = repo.index.commit("Init Tuto")
        
        tuto.sha_draft=cm.hexsha
        return tuto    
    
    
class PartFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Part
    
    title = factory.Sequence(lambda n: 'Ma partie No{0}'.format(n))
    
    @classmethod
    def _prepare(cls, create, **kwargs):
        part = super(PartFactory, cls)._prepare(create, **kwargs)
        tutorial = kwargs.pop('tutorial', None)
        
        path = part.get_path()
        repo = Repo(part.tutorial.get_path())
        
        if not os.path.isdir(path):
            os.makedirs(path, mode=0777)
        
        part.introduction = os.path.join(part.slug,'introduction.md')
        part.conclusion = os.path.join(part.slug,'conclusion.md')
        part.save()
        
        f = open(os.path.join(tutorial.get_path(),part.introduction), "w")
        f.write(u'Test')
        f.close()
        repo.index.add([part.introduction])
        f = open(os.path.join(tutorial.get_path(),part.conclusion), "w")
        f.write(u'Test')
        f.close()
        repo.index.add([part.conclusion])
        
        if tutorial:
            tutorial.save()
            
            man = export_tutorial(tutorial)
            f = open(os.path.join(tutorial.get_path(),'manifest.json'), "w")
            f.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
            f.close()
            
            repo.index.add(['manifest.json'])
        
        cm = repo.index.commit("Init Part")
        
        if tutorial:
            tutorial.sha_draft=cm.hexsha
            tutorial.save()
            
        return part

class ChapterFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Chapter
    
    title = factory.Sequence(lambda n: 'Mon Chapitre No{0}'.format(n))
    
    @classmethod
    def _prepare(cls, create, **kwargs):
        chapter = super(ChapterFactory, cls)._prepare(create, **kwargs)
        tutorial = kwargs.pop('tutorial', None)
        part = kwargs.pop('part', None)
        
        path = chapter.get_path()
        
        if not os.path.isdir(path):
            os.makedirs(path, mode=0777)
            
        if tutorial:
            chapter.introduction = ''
            chapter.conclusion = ''
            tutorial.save()
            repo = Repo(tutorial.get_path())
            
            man = export_tutorial(tutorial)
            f = open(os.path.join(tutorial.get_path(),'manifest.json'), "w")
            f.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
            f.close()
            repo.index.add(['manifest.json'])
                
        elif part:
            chapter.introduction = os.path.join(part.slug, chapter.slug, 'introduction.md')
            chapter.conclusion = os.path.join(part.slug, chapter.slug, 'conclusion.md')
            chapter.save()
            f = open(os.path.join(part.tutorial.get_path(),chapter.introduction), "w")
            f.write(u'Test')
            f.close()
            f = open(os.path.join(part.tutorial.get_path(),chapter.conclusion), "w")
            f.write(u'Test')
            f.close()
            part.tutorial.save()
            repo = Repo(part.tutorial.get_path())
            
            man = export_tutorial(part.tutorial)
            f = open(os.path.join(part.tutorial.get_path(),'manifest.json'), "w")
            f.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
            f.close()
            
            repo.index.add([chapter.introduction, chapter.conclusion])
            repo.index.add(['manifest.json'])
        
        cm=repo.index.commit("Init Chapter")
        
        if tutorial:
            tutorial.sha_draft=cm.hexsha
            tutorial.save()
            chapter.tutorial=tutorial
        elif part:
            part.tutorial.sha_draft=cm.hexsha
            part.tutorial.save()
            part.save()
            chapter.part=part
        
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

class VaidationFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Validation
    