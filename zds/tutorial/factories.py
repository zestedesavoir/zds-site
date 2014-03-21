# coding: utf-8
from collections import OrderedDict
from datetime import datetime
from django.contrib.auth.models import User
import factory
import json
import os

from zds.tutorial.models import *


class BigTutorialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Tutorial
    
    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du Tutoriel No{0}'.format(n))
    type='BIG'
    sha_draft = 'BIG-AAAA'
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
        
        file = open(os.path.join(path,'manifest.json'), "w")
        file.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
        file.close()
        file = open(os.path.join(path,tuto.introduction), "w")
        file.write(u'Test')
        file.close()
        file = open(os.path.join(path,tuto.conclusion), "w")
        file.write(u'Test')
        file.close()
        
        repo = Repo(path)
        repo.index.add([path, os.path.join(path,'manifest.json')])
        repo.index.commit("Init Tuto")
        
        return tuto
    
class MiniTutorialFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Tutorial
    
    title = factory.Sequence(lambda n: 'Mon Tutoriel No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du Tutoriel No{0}'.format(n))
    type='MINI'
    sha_draft = 'MINI-AAAA'
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
        
        file = open(os.path.join(path,'manifest.json'), "w")
        file.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
        file.close()
        file = open(os.path.join(path,tuto.introduction), "w")
        file.write(u'Test')
        file.close()
        file = open(os.path.join(path,tuto.conclusion), "w")
        file.write(u'Test')
        file.close()
        
        repo = Repo(path)
        repo.index.add([path, os.path.join(path,'manifest.json'),os.path.join(path,tuto.introduction), os.path.join(path,tuto.conclusion) ])
        repo.index.commit("Init Tuto")
            
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
            repo.index.add([path])
        
        part.introduction = os.path.join(part.slug,'introduction.md')
        part.conclusion = os.path.join(part.slug,'conclusion.md')
        part.save()
        
        file = open(os.path.join(tutorial.get_path(),part.introduction), "w")
        file.write(u'Test')
        file.close()
        repo.index.add([os.path.join(tutorial.get_path(),part.introduction)])
        file = open(os.path.join(tutorial.get_path(),part.conclusion), "w")
        file.write(u'Test')
        file.close()
        repo.index.add([os.path.join(tutorial.get_path(),part.conclusion)])
        
        if tutorial:
            tutorial.sha_draft = 'PART-AAAA'
            tutorial.save()
            
            man = export_tutorial(tutorial)
            file = open(os.path.join(tutorial.get_path(),'manifest.json'), "w")
            file.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
            file.close()
            
            repo.index.add([os.path.join(tutorial.get_path(),'manifest.json')])
        
        repo.index.commit("Init Part")
        
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
            tutorial.sha_draft = 'CHAPTER-AAAA'
            tutorial.save()
            repo = Repo(tutorial.get_path())
            
            man = export_tutorial(tutorial)
            file = open(os.path.join(tutorial.get_path(),'manifest.json'), "w")
            file.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
            file.close()
            
            repo.index.add([tutorial.get_path()])
                
        elif part:
            chapter.introduction = os.path.join(part.slug, chapter.slug, 'introduction.md')
            chapter.conclusion = os.path.join(part.slug, chapter.slug, 'conclusion.md')
            chapter.save()
            file = open(os.path.join(part.tutorial.get_path(),chapter.introduction), "w")
            file.write(u'Test')
            file.close()
            file = open(os.path.join(part.tutorial.get_path(),chapter.conclusion), "w")
            file.write(u'Test')
            file.close()
            part.tutorial.sha_draft = 'CHAPTER-AAAA'
            part.tutorial.save()
            repo = Repo(part.tutorial.get_path())
            
            man = export_tutorial(part.tutorial)
            file = open(os.path.join(part.tutorial.get_path(),'manifest.json'), "w")
            file.write(json.dumps(man, indent=4, ensure_ascii=False).encode('utf-8'))
            file.close()
            
            repo.index.add([part.tutorial.get_path(), os.path.join(part.tutorial.get_path(),chapter.introduction), os.path.join(part.tutorial.get_path(),chapter.conclusion)])
        
        repo.index.commit("Init Chapter")
        
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