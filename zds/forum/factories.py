# coding: utf-8

import factory
from zds.forum.models import Category, Forum, Topic, Post
from zds.utils.models import Tag

class CategoryFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Category

    title = factory.Sequence(lambda n: 'Ma catégorie No{0}'.format(n))
    slug = factory.Sequence(lambda n: 'category{0}'.format(n))


class ForumFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Forum

    title = factory.Sequence(lambda n: 'Mon Forum No{0}'.format(n))
    subtitle = factory.Sequence(
        lambda n: 'Sous Titre du Forum No{0}'.format(n))
    slug = factory.Sequence(lambda n: 'forum{0}'.format(n))

class TagFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Tag
    
    title = factory.Sequence(lambda n: 'Tag{0}'.format(n))
    slug = factory.Sequence(lambda n: 'tag{0}'.format(n))

class TopicFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Topic

    title = factory.Sequence(lambda n: 'Mon Sujet No{0}'.format(n))
    subtitle = factory.Sequence(
        lambda n: 'Sous Titre du sujet No{0}'.format(n))


class PostFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Post

    ip_address = '192.168.3.1'
    text = 'Bonjour, je me présente, je m\'appelle l\'homme au texte bidonné'

    @classmethod
    def _prepare(cls, create, **kwargs):
        post = super(PostFactory, cls)._prepare(create, **kwargs)
        topic = kwargs.pop('topic', None)
        if topic:
            topic.last_message = post
            topic.save()
        return post
