# coding: utf-8

from datetime import datetime

import factory
from zds.forum.factories import PostFactory, TopicFactory

from zds.tutorialv2.models.models_database import PublishableContent, Validation, ContentReaction
from zds.tutorialv2.models.models_versioned import Container, Extract
from zds.utils.models import SubCategory, Licence
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.tutorialv2.utils import init_new_repo
from zds.tutorialv2.publication_utils import publish_content

text_content = u'Ceci est un texte bidon, **avec markown**'

tricky_text_content = \
    u"Ceci est un texte contenant plein d'images, pour la publication. Le modifier affectera le test !\n\n" \
    u'# Les images\n\n' \
    u'Image: ![PNG qui existe](http://upload.wikimedia.org/wikipedia/en/9/9d/Commons-logo-31px.png)\n\n' \
    u'Image: ![PNG qui existe pas](example.com/test.png)\n\n' \
    u'Image: ![SVG qui existe](http://upload.wikimedia.org/wikipedia/commons/f/f9/10DF.svg)\n\n' \
    u'Image: ![SVG qui existe pas](example.com/test.svg)\n\n' \
    u'Image: ![GIF qui existe](http://upload.wikimedia.org/wikipedia/commons/2/27/AnimatedStar.gif)\n\n' \
    u'Image: ![GIF qui existe pas](example.com/test.gif)\n\n' \
    u'Image: ![Image locale qui existe](fixtures/image_test.jpg)\n\n' \
    u'Image: ![Image locale qui existe pas](does-not-exist/test.png)\n\n' \
    u'Image: ![Bonus: image bizarre](https://s.qwant.com/thumbr/?u=http%3A%2F%2Fwww.blogoergosum.com%2Fwp-content%2F' \
    u'uploads%2F2010%2F02%2Fwikipedia-logo.jpg&h=338&w=600)\n\n' \
    u'Image: ![Bonus: le serveur existe pas !](http://unknown.image.zds/test.png)\n\n' \
    u'Image: ![Bonus: juste du texte](URL invalide)\n\n' \
    u'# Et donc ...\n\n'\
    u'Voilà :)'


class PublishableContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = PublishableContent

    title = factory.Sequence(lambda n: 'Mon contenu No{0}'.format(n))
    description = factory.Sequence(lambda n: 'Description du contenu No{0}'.format(n))
    type = 'TUTORIAL'
    creation_date = datetime.now()
    pubdate = datetime.now()

    @classmethod
    def _prepare(cls, create, **kwargs):
        auths = []
        if 'author_list' in kwargs:
            auths = kwargs.pop('author_list')

        light = True
        if 'light' in kwargs:
            light = kwargs.pop('light')
        text = text_content
        if not light:
            text = tricky_text_content

        publishable_content = super(PublishableContentFactory, cls)._prepare(create, **kwargs)
        publishable_content.gallery = GalleryFactory()

        for auth in auths:
            publishable_content.authors.add(auth)

        publishable_content.save()

        for author in publishable_content.authors.all():
            UserGalleryFactory(user=author, gallery=publishable_content.gallery, mode='W')

        init_new_repo(publishable_content, text, text)

        return publishable_content


class ContainerFactory(factory.Factory):
    class Meta:
        model = Container

    title = factory.Sequence(lambda n: 'Mon container No{0}'.format(n + 1))

    @classmethod
    def _prepare(cls, create, **kwargs):
        db_object = kwargs.pop('db_object', None)
        parent = kwargs.pop('parent', None)

        light = True
        if 'light' in kwargs:
            light = kwargs.pop('light')
        text = text_content
        if not light:
            text = tricky_text_content

        sha = parent.repo_add_container(kwargs['title'], text, text)
        container = parent.children[-1]

        if db_object:
            db_object.sha_draft = sha
            db_object.save()

        return container


class ExtractFactory(factory.Factory):
    class Meta:
        model = Extract
    title = factory.Sequence(lambda n: 'Mon extrait No{0}'.format(n + 1))

    @classmethod
    def _prepare(cls, create, **kwargs):
        db_object = kwargs.pop('db_object', None)
        parent = kwargs.pop('container', None)

        light = True
        if 'light' in kwargs:
            light = kwargs.pop('light')
        text = text_content
        if not light:
            text = tricky_text_content

        sha = parent.repo_add_extract(kwargs['title'], text)
        extract = parent.children[-1]

        if db_object:
            db_object.sha_draft = sha
            db_object.save()

        return extract


class ContentReactionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ContentReaction

    ip_address = '192.168.3.1'
    text = "Bonjour, je me présente, je m'appelle l'homme au texte bidonné"

    @classmethod
    def _prepare(cls, create, **kwargs):
        note = super(ContentReactionFactory, cls)._prepare(create, **kwargs)
        note.pubdate = datetime.now()
        note.save()
        content = kwargs.pop('tutorial', None)
        if content:
            content.last_note = note
            content.save()
        return note


class BetaContentFactory(PublishableContentFactory):
    @classmethod
    def _prepare(cls, create, **kwargs):
        beta_forum = kwargs.pop('forum', None)
        publishable_content = super(BetaContentFactory, cls)._prepare(create, **kwargs)
        if publishable_content.authors.count() > 0 and beta_forum is not None:
            beta_topic = TopicFactory(title='[beta]' + publishable_content.title,
                                      author=publishable_content.authors.first(),
                                      forum=beta_forum)
            publishable_content.sha_beta = publishable_content.sha_draft
            publishable_content.beta_topic = beta_topic
            publishable_content.save()
            PostFactory(topic=beta_topic, position=1, author=publishable_content.authors.first())
            beta_topic.save()
        return publishable_content


class PublishedContentFactory(PublishableContentFactory):

    @classmethod
    def _prepare(cls, create, **kwargs):
        """create a new PublishableContent and then publish it.
        """

        is_major_update = kwargs.pop('is_major_update', True)

        content = super(PublishedContentFactory, cls)._prepare(create, **kwargs)
        published = publish_content(content, content.load_version(), is_major_update)
        content.sha_public = content.sha_draft
        content.public_version = published

        content.save()

        return content


class SubCategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = SubCategory

    title = factory.Sequence(lambda n: 'Sous-Categorie {0} pour Tuto'.format(n))
    subtitle = factory.Sequence(lambda n: 'Sous titre de Sous-Categorie {0} pour Tuto'.format(n))
    slug = factory.Sequence(lambda n: 'sous-categorie-{0}'.format(n))


class ValidationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Validation


class LicenceFactory(factory.DjangoModelFactory):
    class Meta:
        model = Licence

    code = factory.Sequence(lambda n: 'bidon-no{0}'.format(n + 1))
    title = factory.Sequence(lambda n: 'Licence bidon no{0}'.format(n + 1))

    @classmethod
    def _prepare(cls, create, **kwargs):
        licence = super(LicenceFactory, cls)._prepare(create, **kwargs)
        return licence
