from datetime import datetime

import factory

from zds.featured.models import FeaturedResource, FeaturedMessage


class FeaturedResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FeaturedResource

    title = factory.Sequence("Ma featured No{}".format)
    pubdate = datetime.now()


class FeaturedMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FeaturedMessage

    message = factory.Sequence("Message No{}".format)
    url = factory.Sequence("http://www.google.com/?q={}".format)
