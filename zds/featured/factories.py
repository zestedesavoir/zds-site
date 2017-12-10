from datetime import datetime

import factory

from zds.featured.models import FeaturedResource, FeaturedMessage


class FeaturedResourceFactory(factory.DjangoModelFactory):
    class Meta:
        model = FeaturedResource

    title = factory.Sequence('Ma featured No{0}'.format)
    pubdate = datetime.now()


class FeaturedMessageFactory(factory.DjangoModelFactory):
    class Meta:
        model = FeaturedMessage

    message = factory.Sequence('Message No{0}'.format)
    url = factory.Sequence('http://www.google.com/?q={0}'.format)
