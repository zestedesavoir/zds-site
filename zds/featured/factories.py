# coding: utf-8
from datetime import datetime

import factory

from zds.featured.models import ResourceFeatured, MessageFeatured


class ResourceFeaturedFactory(factory.DjangoModelFactory):
    FACTORY_FOR = ResourceFeatured

    title = factory.Sequence(lambda n: 'Ma featured No{0}'.format(n))
    pubdate = datetime.now()


class MessageFeaturedFactory(factory.DjangoModelFactory):
    FACTORY_FOR = MessageFeatured

    message = factory.Sequence(lambda n: 'Message No{0}'.format(n))
    url = factory.Sequence(lambda n: 'http://www.google.com'.format(n))
