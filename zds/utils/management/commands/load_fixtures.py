# coding: utf-8

import random
from django.core.management.base import BaseCommand
from random import randint
from faker import Factory
from zds.utils.templatetags.emarkdown import emarkdown

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.tutorial.factories import BigTutorialFactory, PartFactory, ChapterFactory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.member.factories import UserFactory, StaffFactory, StaffProfileFactory, ProfileFactory
from zds.utils.models import Tag
from zds.utils import slugify
from django.db import transaction


@transaction.atomic
class Command(BaseCommand):
    args = '[low|medium|high]'
    help = 'Load fixtures for ZdS'

    def handle(self, *args, **options):
        if len(args) > 0:
            if args[0] == "low":
                size = 1
            elif args[0] == "medium":
                size = 2
            elif args[0] == "high":
                size = 3
            else:
                size = 2
        else:
            size = 2
        fake = Factory.create(locale="fr_FR")

        """
        Load members
        """
        profiles = []
        nb_users = size * 10
        self.stdout.write(u"Nombres de membres à créer : {}".format(nb_users))
        for i in range(0, nb_users):
            profile = ProfileFactory()
            profile.user.set_password(profile.user.username)
            profile.user.first_name = fake.first_name()
            profile.user.last_name = fake.last_name()
            profile.user.email = fake.free_email()
            profile.user.save()
            profile.site = fake.url()
            profile.biography = fake.text(max_nb_chars=200)
            profile.last_ip_address = fake.ipv4()
            profile.save()
            profiles.append(profile)

        """
        Load staff
        """
        profile_staffs = []
        nb_staffs = size * 10
        self.stdout.write(u"Nombres de staffs à créer : {}".format(nb_staffs))
        for i in range(0, nb_staffs):
            profile = StaffProfileFactory()
            profile.user.first_name = fake.first_name()
            profile.user.last_name = fake.last_name()
            profile.user.email = fake.free_email()
            profile.user.save()
            profile.site = fake.url()
            profile.biography = fake.paragraph()
            profile.sign = fake.text(max_nb_chars=80)
            profile.last_ip_address = fake.ipv6()
            profile.save()
            profile_staffs.append(profile)

        """
        Load galleries
        """
        galleries = []
        nb_galleries = size * 3
        nb_images = size * 5
        self.stdout.write(u"Nombres de galéries à créer par utilisateur: {}".format(nb_galleries))
        self.stdout.write(u"Nombres d'images à créer par gallerie: {}".format(nb_images))
        for i in range(0, nb_users):
            for j in range(0, nb_galleries):
                gal = GalleryFactory(title=fake.text(max_nb_chars=80), subtitle=fake.text(max_nb_chars=200))
                ug = UserGalleryFactory(user=profiles[i].user, gallery=gal)
                for k in range(0, nb_images):
                    img = ImageFactory(gallery=gal)

        """
        Load categories
        """
        categories = []
        nb_categories = size * 2
        self.stdout.write(u"Nombres de catégories de forum à créer : {}".format(nb_categories))
        for i in range(0, nb_users):
            cat = CategoryFactory(position=i + 1)
            cat.title = fake.text(max_nb_chars=20)
            cat.save()
            categories.append(cat)

        """
        Load forums
        """
        forums = []
        nb_forums = size * 8
        self.stdout.write(u"Nombres de Forums à créer : {}".format(nb_forums))
        for i in range(0, nb_forums):
            forum = ForumFactory(category=categories[i % nb_categories],
                                 position_in_category=(i / nb_categories) + 1)
            forum.title = fake.text(max_nb_chars=20)
            forum.subtitle = fake.sentence(nb_words=15, variable_nb_words=True)
            forum.save()
            forums.append(forum)

        """
        Load tags
        """
        tags = []
        nb_tags = size * 50
        self.stdout.write(u"Nombres de Tags de forum à créer : {}".format(nb_tags))
        for i in range(0, nb_tags):
            title = fake.word()
            t = Tag(title=title, slug=slugify(title))

        """
        Load topics
        """
        topics = []
        nb_topics = size * 20
        self.stdout.write(u"Nombres de Topics à créer : {}".format(nb_topics))
        for i in range(0, nb_topics):
            # load one staff for ten member
            if i % 10 == 0:
                topic = TopicFactory(forum=forums[i % nb_forums], author=profiles[i % nb_users].user)
                topic.is_sticky = True
            else:
                topic = TopicFactory(forum=forums[i % nb_forums], author=profile_staffs[i % nb_staffs].user)
            nb_rand_tags = random.randint(0, 5)
            for k in range(0, nb_tags):
                topic.tags.add(random.randint(1, nb_tags))
            topic.title = fake.text(max_nb_chars=80)
            topic.subtitle = fake.text(max_nb_chars=200)
            topic.save()
            topics.append(topic)

        """
        Load posts
        """
        posts = []
        nb_avg_posts_in_topic = size * 10
        self.stdout.write(u"Nombres de messages à poster en moyenne dans un sujet : {}".format(nb_avg_posts_in_topic))
        for i in range(0, nb_topics):
            nb = randint(0, nb_avg_posts_in_topic * 2)
            for j in range(0, nb):
                if j == 0:
                    post = PostFactory(topic=topics[i], author=topics[i].author, position=1)
                else:
                    post = PostFactory(topic=topics[i], author=profiles[j % nb_users].user, position=j+1)
                post.text = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
                post.text_html = emarkdown(post.text)
                post.save()
                posts.append(post)

        """
        Load tutorials
        """
        tutorials = []
        parts = []
        chapters = []

        nb_tutos = size * 5
        nb_avg_parts_in_tuto = size * 1
        nb_avg_chapters_in_tuto = size * 1
        self.stdout.write(u"Nombres de big tutoriels à créer : {}".format(nb_tutos))
        for i in range(0, nb_tutos):
            tuto = BigTutorialFactory(title=fake.text(max_nb_chars=200),
                                      description=fake.sentence(nb_words=15, variable_nb_words=True))
            tuto.authors.add(profiles[i % nb_users].user)
            tutorials.append(tuto)
            nb_part = randint(0, nb_avg_parts_in_tuto * 2)
            for j in range(0, nb_part):
                parts.append(PartFactory(tutorial=tutorials[i],
                                         position_in_tutorial=j,
                                         title=fake.text(max_nb_chars=200)))
                nb_chap = randint(0, nb_avg_chapters_in_tuto * 2)
                for k in range(0, nb_chap):
                    chapters.append(ChapterFactory(part=parts[j],
                                                   position_in_part=k,
                                                   position_in_tutorial=j * k,
                                                   title=fake.text(max_nb_chars=200)))