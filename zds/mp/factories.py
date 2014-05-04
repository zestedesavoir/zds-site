# coding: utf-8

import factory

from zds.mp.models import PrivateTopic, PrivatePost


class PrivateTopicFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PrivateTopic

    title = factory.Sequence(lambda n: 'Mon Sujet No{0}'.format(n))
    subtitle = factory.Sequence(
        lambda n: 'Sous Titre du sujet No{0}'.format(n))


class PrivatePostFactory(factory.DjangoModelFactory):
    FACTORY_FOR = PrivatePost

    text = 'Bonjour, je me présente, je m\'appelle l\'homme au texte bidonné'

    @classmethod
    def _prepare(cls, create, **kwargs):
        ppost = super(PrivatePostFactory, cls)._prepare(create, **kwargs)
        ptopic = kwargs.pop('privatetopic', None)
        if ptopic:
            ptopic.last_message = ppost
            ptopic.save()
        return ppost
