from datetime import datetime

import factory
from zds.forum.factories import PostFactory, TopicFactory

from zds.tutorialv2.models.database import PublishableContent, Validation, ContentReaction
from zds.tutorialv2.models.versioned import Container, Extract
from zds.utils.models import SubCategory, Licence, CategorySubCategory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory
from zds.tutorialv2.utils import init_new_repo
from zds.tutorialv2.publication_utils import publish_content

text_content = 'Ceci est un texte bidon, **avec markown**'

tricky_text_content = \
    "Ceci est un texte contenant plein d'images, pour la publication. Le modifier affectera le test !\n\n" \
    '# Les images\n\n' \
    'Image: ![PNG qui existe](http://upload.wikimedia.org/wikipedia/en/9/9d/Commons-logo-31px.png)\n\n' \
    'Image: ![PNG qui existe pas](example.com/test.png)\n\n' \
    'Image: ![SVG qui existe](http://upload.wikimedia.org/wikipedia/commons/f/f9/10DF.svg)\n\n' \
    'Image: ![SVG qui existe pas](example.com/test.svg)\n\n' \
    'Image: ![GIF qui existe](http://upload.wikimedia.org/wikipedia/commons/2/27/AnimatedStar.gif)\n\n' \
    'Image: ![GIF qui existe pas](example.com/test.gif)\n\n' \
    'Image: ![Image locale qui existe pas](does-not-exist/test.png)\n\n' \
    'Image: ![Bonus: image bizarre](https://s2.qwant.com/thumbr/300x0/e/7/' \
    '56e2a2bdcd656d0b8a29c650116e29e893239089f71adf128d5f06330703b1/1024px-' \
    'Oh_my_darling.jpg?u=https%3A%2F%2Fupload' \
    '.wikimedia.org%2Fwikipedia%2Fcommons%2Fthumb%2Fa%2Fa9%2FOh_my_darling.jpg%2F1024px-' \
    'Oh_my_darling.jpg&q=0&b=0&p=0&a=0)\n\n' \
    'Image: ![Bonus: le serveur existe pas !](http://unknown.image.zds/test.png)\n\n' \
    'Image: ![Bonus: juste du texte](URL invalide)\n\n' \
    '# Et donc ...\n\n'\
    'Voilà :)'


class PublishableContentFactory(factory.DjangoModelFactory):
    class Meta:
        model = PublishableContent

    title = factory.Sequence('Mon contenu No{0}'.format)
    description = factory.Sequence('Description du contenu No{0}'.format)
    type = 'TUTORIAL'
    creation_date = datetime.now()
    pubdate = datetime.now()

    @classmethod
    def _prepare(cls, create, *, light=True, author_list=None, licence: Licence = None, text=text_content, **kwargs):
        auths = author_list or []
        given_licence = licence or Licence.objects.first()
        if isinstance(given_licence, str) and given_licence:
            given_licence = Licence.objects.filter(title=given_licence).first() or Licence.objects.first()
        licence = given_licence or LicenceFactory()

        #text = text_content
        if not light:
            text = tricky_text_content

        publishable_content = super(PublishableContentFactory, cls)._prepare(create, **kwargs)
        publishable_content.gallery = GalleryFactory()
        publishable_content.licence = licence
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
    def _prepare(cls, create, *, db_object=None, light=True, **kwargs):
        parent = kwargs.pop('parent', None)

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
    def _prepare(cls, create, *, light=True, container=None, **kwargs):
        db_object = kwargs.pop('db_object', None)
        parent = container
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
        note.related_content.last_note = note
        note.related_content.save()
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
    def _prepare(cls, create, *, light=True, author_list=None, licence: Licence = None, **kwargs):
        """create a new PublishableContent and then publish it.
        """

        is_major_update = kwargs.pop('is_major_update', True)

        content = super(PublishedContentFactory, cls)._prepare(create, light=light, author_list=author_list,
                                                               licence=licence, **kwargs)
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

    @classmethod
    def _prepare(cls, create, **kwargs):

        category = kwargs.pop('category', None)

        subcategory = super(SubCategoryFactory, cls)._prepare(create, **kwargs)

        if category is not None:
            relation = CategorySubCategory(category=category, subcategory=subcategory)
            relation.save()

        return subcategory


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
