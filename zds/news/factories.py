# coding: utf-8
from datetime import datetime

import factory

from zds.news.models import News


class NewsFactory(factory.DjangoModelFactory):
    FACTORY_FOR = News

    title = factory.Sequence(lambda n: 'Ma news No{0}'.format(n))
    pubdate = datetime.now()
