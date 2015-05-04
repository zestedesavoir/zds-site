# coding: utf-8
from datetime import datetime

import factory

from zds.featured.models import FeaturedResource, FeaturedMessage


class FeaturedResourceFactory(factory.DjangoModelFactory):
    FACTORY_FOR = FeaturedResource

    title = factory.Sequence(lambda n: 'Ma featured No{0}'.format(n))
    pubdate = datetime.now()


class FeaturedMessageFactory(factory.DjangoModelFactory):
    FACTORY_FOR = FeaturedMessage

    message = factory.Sequence(lambda n: 'Message No{0}'.format(n))
    url = factory.Sequence(lambda n: 'http://www.google.com'.format(n))
