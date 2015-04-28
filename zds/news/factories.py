# coding: utf-8
from datetime import datetime

import factory

from zds.news.models import News, MessageNews


class NewsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = News

    title = factory.Sequence(lambda n: 'Ma news No{0}'.format(n))
    pubdate = datetime.now()


class MessageNewsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = MessageNews

    message = factory.Sequence(lambda n: 'Message No{0}'.format(n))
    url = factory.Sequence(lambda n: 'http://www.google.com'.format(n))
