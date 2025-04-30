import factory

from zds.mp.models import PrivatePost, PrivateTopic


class PrivateTopicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PrivateTopic

    title = factory.Sequence("Mon Sujet No{}".format)
    subtitle = factory.Sequence("Sous Titre du sujet No{}".format)


class PrivatePostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PrivatePost

    text = "Bonjour, je me présente, je m'appelle l'homme au texte bidonné"

    @classmethod
    def _generate(cls, create, attrs):
        ppost = super()._generate(create, attrs)
        ptopic = attrs.get("privatetopic", None)
        if ptopic:
            ppost.save()
            ptopic.last_message = ppost
            ptopic.save()
        return ppost
