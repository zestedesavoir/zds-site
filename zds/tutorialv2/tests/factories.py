from datetime import datetime
from os.path import basename, join
from shutil import copyfile

import factory
from django.conf import settings

from zds.forum.tests.factories import PostFactory, TopicFactory
from zds.gallery.tests.factories import GalleryFactory, UserGalleryFactory
from zds.tutorialv2.models.database import ContentContributionRole, ContentReaction, PublishableContent, Validation
from zds.tutorialv2.models.goals import Goal
from zds.tutorialv2.models.help_requests import HelpWriting
from zds.tutorialv2.models.labels import Label
from zds.tutorialv2.models.versioned import Container, Extract
from zds.tutorialv2.publication_utils import publish_content
from zds.tutorialv2.utils import init_new_repo
from zds.utils import old_slugify
from zds.utils.models import Licence
from zds.utils.tests.factories import LicenceFactory, SubCategoryFactory

text_content = "Ceci est un texte bidon, **avec markown**"

tricky_text_content = (
    "Ceci est un texte contenant plein d'images, pour la publication. Le modifier affectera le test !\n\n"
    "# Les images\n\n"
    "Image: ![PNG qui existe](https://upload.wikimedia.org/wikipedia/commons/2/24/"
    "Derivative_of_medical_imaging.jpg)\n\n"
    "Image: ![PNG qui existe pas](example.com/test.png)\n\n"
    "Image: ![SVG qui existe](https://upload.wikimedia.org/wikipedia/commons/f/f9/10DF.svg)\n\n"
    "Image: ![SVG qui existe pas](example.com/test.svg)\n\n"
    "Image: ![GIF qui existe](https://upload.wikimedia.org/wikipedia/commons/2/27/AnimatedStar.gif)\n\n"
    "Image: ![GIF qui existe pas](example.com/test.gif)\n\n"
    "Image: ![Image locale qui existe pas](does-not-exist/test.png)\n\n"
    "Image: ![Bonus: image bizarre](https://s2.qwant.com/thumbr/300x0/e/7/"
    "56e2a2bdcd656d0b8a29c650116e29e893239089f71adf128d5f06330703b1/1024px-"
    "Oh_my_darling.jpg?u=https%3A%2F%2Fupload"
    ".wikimedia.org%2Fwikipedia%2Fcommons%2Fthumb%2Fa%2Fa9%2FOh_my_darling.jpg%2F1024px-"
    "Oh_my_darling.jpg&q=0&b=0&p=0&a=0)\n\n"
    "Image: ![Bonus: le serveur existe pas !](http://unknown.image.zds/test.png)\n\n"
    "Image: ![Bonus: juste du texte](URL invalide)\n\n"
    "# Et donc ...\n\n"
    "Voilà :)"
)


class PublishableContentFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a PublishableContent.
    """

    class Meta:
        model = PublishableContent

    title = factory.Sequence("Mon contenu No{}".format)
    description = factory.Sequence("Description du contenu No{}".format)
    type = "TUTORIAL"
    creation_date = datetime.now()
    pubdate = datetime.now()

    @classmethod
    def _generate(cls, create, attrs):
        # These parameters are only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (they are removed from attrs).
        light = attrs.pop("light", True)
        author_list = attrs.pop("author_list", None)
        add_license = attrs.pop("add_license", True)
        add_category = attrs.pop("add_category", True)

        # This parameter will be saved in the database,
        # which is why we use attrs.get() (it stays in attrs).
        licence = attrs.get("licence", None)

        auths = author_list or []
        if add_license:
            given_licence = licence or Licence.objects.first()
            if isinstance(given_licence, str) and given_licence:
                given_licence = Licence.objects.filter(title=given_licence).first() or Licence.objects.first()
            licence = given_licence or LicenceFactory()

        text = text_content
        if not light:
            text = tricky_text_content

        intro_content = attrs.pop("intro", text)
        conclusion_content = attrs.pop("conclusion", text)

        publishable_content = super()._generate(create, attrs)
        publishable_content.gallery = GalleryFactory(title=publishable_content.title)
        publishable_content.licence = licence
        for auth in auths:
            publishable_content.authors.add(auth)

        if add_category:
            publishable_content.subcategory.add(SubCategoryFactory())

        publishable_content.save()

        for author in publishable_content.authors.all():
            UserGalleryFactory(user=author, gallery=publishable_content.gallery, mode="W")

        init_new_repo(publishable_content, intro_content, conclusion_content)

        return publishable_content


class ContainerFactory(factory.Factory):
    """
    Factory that creates a Container.
    """

    class Meta:
        model = Container

    title = factory.Sequence(lambda n: f"Mon container No{n + 1}")

    @classmethod
    def _generate(cls, create, attrs):
        # These parameters are only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (they are removed from attrs).
        db_object = attrs.pop("db_object", None)
        light = attrs.pop("light", True)

        # This parameter will be saved in the database,
        # which is why we use attrs.get() (it stays in attrs).
        parent = attrs.get("parent", None)

        text = text_content
        if not light:
            text = tricky_text_content

        intro_content = attrs.pop("intro", text)
        conclusion_content = attrs.pop("conclusion", text)

        # Needed because we use container.title later
        container = super()._generate(create, attrs)

        sha = parent.repo_add_container(container.title, intro_content, conclusion_content)
        container = parent.children[-1]

        if db_object:
            db_object.sha_draft = sha
            db_object.save()

        return container


class ExtractFactory(factory.Factory):
    """
    Factory that creates a Extract.
    """

    class Meta:
        model = Extract

    title = factory.Sequence(lambda n: f"Mon extrait No{n + 1}")

    @classmethod
    def _generate(cls, create, attrs):
        # These parameters are only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (they are removed from attrs).
        light = attrs.pop("light", True)
        db_object = attrs.pop("db_object", None)

        # This parameter will be saved in the database,
        # which is why we use attrs.get() (it stays in attrs).
        container = attrs.get("container", None)

        text = text_content
        if not light:
            text = tricky_text_content
        text = attrs.pop("text_content", text)

        # Needed because we use extract.title later
        extract = super()._generate(create, attrs)

        parent = container

        sha = parent.repo_add_extract(extract.title, text)
        extract = parent.children[-1]

        if db_object:
            db_object.sha_draft = sha
            db_object.save()

        return extract


class ContentReactionFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a ContentReaction.
    """

    class Meta:
        model = ContentReaction

    ip_address = "192.168.3.1"
    text = "Bonjour, je me présente, je m'appelle l'homme au texte bidonné"
    position = 1

    @classmethod
    def _generate(cls, create, attrs):
        note = super()._generate(create, attrs)
        note.pubdate = datetime.now()
        note.save()
        note.related_content.last_note = note
        note.related_content.save()
        return note


class BetaContentFactory(PublishableContentFactory):
    """
    Factory that creates a PublishableContent with a beta version and a beta topic.
    """

    @classmethod
    def _generate(cls, create, attrs):
        # This parameter is only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (it is removed from attrs).
        beta_forum = attrs.pop("forum", None)

        # Creates the PublishableContent (see PublishableContentFactory._generate() for more info)
        publishable_content = super()._generate(create, attrs)

        if publishable_content.authors.count() > 0 and beta_forum is not None:
            beta_topic = TopicFactory(
                title="[beta]" + publishable_content.title, author=publishable_content.authors.first(), forum=beta_forum
            )
            publishable_content.sha_beta = publishable_content.sha_draft
            publishable_content.beta_topic = beta_topic
            publishable_content.save()
            PostFactory(topic=beta_topic, position=1, author=publishable_content.authors.first())
            beta_topic.save()
        return publishable_content


class PublishedContentFactory(PublishableContentFactory):
    """
    Factory that creates a PublishableContent and then publishes it.

    NOTE: This factory returns the PublishableContent object, not the
    PublishedContent object (accessible through content.public_version).
    """

    @classmethod
    def _generate(cls, create, attrs):
        # This parameter is only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (it is removed from attrs).
        is_major_update = attrs.pop("is_major_update", True)

        # Creates the PublishableContent (see PublishableContentFactory._generate() for more info)
        content = super()._generate(create, attrs)

        published = publish_content(content, content.load_version(), is_major_update)
        content.sha_public = content.sha_draft
        content.public_version = published

        content.save()

        return content


class ValidationFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a Validation.
    """

    class Meta:
        model = Validation


class HelpWritingFactory(factory.django.DjangoModelFactory):
    """
    Factory that creates a HelpWriting.
    """

    class Meta:
        model = HelpWriting

    title = factory.Sequence("titre de l'image {}".format)
    slug = factory.LazyAttribute(lambda o: f"{old_slugify(o.title)}")
    tablelabel = factory.LazyAttribute(lambda n: "Besoin de " + n.title)

    @classmethod
    def _generate(cls, create, attrs):
        # These parameters are only used inside _generate() and won't be saved in the database,
        # which is why we use attrs.pop() (they are removed from attrs).
        image_path = attrs.pop("image_path", None)
        fixture_image_path = attrs.pop("fixture_image_path", None)

        help_writing = super()._generate(create, attrs)

        if fixture_image_path is not None:
            image_path = join(settings.BASE_DIR, "fixtures", fixture_image_path)

        if image_path is not None:
            copyfile(image_path, settings.MEDIA_ROOT / basename(image_path))
            help_writing.image = basename(image_path)
            help_writing.save()

        return help_writing

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        kwargs.pop("image_path", None)
        kwargs.pop("fixture_image_path", None)

        return super()._create(target_class, *args, **kwargs)


class GoalFactory(factory.django.DjangoModelFactory):
    """Factory that create a goal for use in tests."""

    class Meta:
        model = Goal

    name = factory.Sequence("Mon objectif n°{}".format)
    description = factory.Sequence("Très belle description n°{}".format)
    position = factory.Sequence(lambda n: n)
    slug = factory.Sequence("mon-objectif-{}".format)


class ContentContributionRoleFactory(factory.django.DjangoModelFactory):
    """Factory that create a role in contributions to contents, for use in tests."""

    class Meta:
        model = ContentContributionRole

    title = factory.Sequence("Rôle {}".format)


class LabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Label

    name = factory.Sequence("Mon label n°{}".format)
    description = factory.Sequence("Très belle description n°{}".format)
    slug = factory.Sequence("mon-label-{}".format)
