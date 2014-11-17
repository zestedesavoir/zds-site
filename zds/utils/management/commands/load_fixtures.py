# coding: utf-8

import random
from django.core.management.base import BaseCommand
from random import randint
from faker import Factory
from zds.utils.templatetags.emarkdown import emarkdown

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.tutorial.factories import BigTutorialFactory, PartFactory, ChapterFactory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.member.factories import StaffProfileFactory, ProfileFactory
from django.contrib.auth.models import User
from zds.member.models import Profile
from zds.forum.models import Category, Forum, Topic, Post
from zds.utils.models import Tag
from zds.utils import slugify
from django.db import transaction


def load_member(cli, size, fake):
    """
    Load members
    """
    nb_users = size * 10
    cli.stdout.write(u"Nombres de membres à créer : {}".format(nb_users))
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


def load_staff(cli, size, fake):
    """
    Load staff
    """
    nb_staffs = size * 10
    cli.stdout.write(u"Nombres de staffs à créer : {}".format(nb_staffs))
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


def load_gallery(cli, size, fake):
    """
    Load galleries
    """
    nb_galleries = size * 3
    nb_images = size * 5
    cli.stdout.write(u"Nombres de galéries à créer par utilisateur: {}".format(nb_galleries))
    cli.stdout.write(u"Nombres d'images à créer par gallerie: {}".format(nb_images))
    nb_users = User.objects.count()
    profiles = list(Profile.objects.all())
    for i in range(0, nb_users):
        for j in range(0, nb_galleries):
            gal = GalleryFactory(title=fake.text(max_nb_chars=80), subtitle=fake.text(max_nb_chars=200))
            ug = UserGalleryFactory(user=profiles[i].user, gallery=gal)
            for k in range(0, nb_images):
                img = ImageFactory(gallery=gal)


def load_categories_forum(cli, size, fake):
    """
    Load categories
    """
    nb_categories = size * 2
    cli.stdout.write(u"Nombres de catégories de forum à créer : {}".format(nb_categories))
    nb_users = User.objects.count()
    for i in range(0, nb_users):
        cat = CategoryFactory(position=i + 1)
        cat.title = fake.text(max_nb_chars=20)
        cat.save()


def load_forums(cli, size, fake):
    """
    Load forums
    """
    nb_forums = size * 8
    cli.stdout.write(u"Nombres de Forums à créer : {}".format(nb_forums))
    nb_categories = Category.objects.count()
    categories = list(Category.objects.all())
    for i in range(0, nb_forums):
        forum = ForumFactory(category=categories[i % nb_categories],
                             position_in_category=(i / nb_categories) + 1)
        forum.title = fake.text(max_nb_chars=20)
        forum.subtitle = fake.sentence(nb_words=15, variable_nb_words=True)
        forum.save()


def load_tags(cli, size, fake):
    """
    Load tags
    """
    nb_tags = size * 50
    cli.stdout.write(u"Nombres de Tags de forum à créer : {}".format(nb_tags))
    for i in range(0, nb_tags):
        title = fake.word()
        t = Tag(title=title, slug=slugify(title))


def load_topics(cli, size, fake):
    """
    Load topics
    """
    nb_topics = size * 20
    cli.stdout.write(u"Nombres de Topics à créer : {}".format(nb_topics))
    nb_forums = Forum.objects.count()
    forums = list(Forum.objects.all())
    nb_users = User.objects.count()
    profiles = list(Profile.objects.all())
    nb_tags = Tag.objects.count()
    for i in range(0, nb_topics):
        topic = TopicFactory(forum=forums[i % nb_forums], author=profiles[i % nb_users].user)
        topic.is_sticky = True
        nb_rand_tags = random.randint(0, 5)
        for k in range(0, nb_rand_tags):
            topic.tags.add(random.randint(1, nb_tags))
        topic.title = fake.text(max_nb_chars=80)
        topic.subtitle = fake.text(max_nb_chars=200)
        topic.save()


def load_posts(cli, size, fake):
    """
    Load posts
    """
    nb_avg_posts_in_topic = size * 10
    cli.stdout.write(u"Nombres de messages à poster en moyenne dans un sujet : {}".format(nb_avg_posts_in_topic))
    nb_topics = Topic.objects.count()
    topics = list(Topic.objects.all())
    nb_users = User.objects.count()
    profiles = list(Profile.objects.all())
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


def load_comment_article(cli, size, fake):
    """
    Load article's comments
    """
    nb_avg_posts = size * 20
    cli.stdout.write(u"Nombres de messages à poster en moyenne dans un article : {}".format(nb_avg_posts))
    nb_articles = Article.objects.filter(sha_public__isnull=False).count()
    articles = list(Article.objects.filter(sha_public__isnull=False).all())
    nb_users = User.objects.count()
    profiles = list(Profile.objects.all())
    for i in range(0, nb_articles):
        nb = randint(0, nb_avg_posts * 2)
        for j in range(0, nb):
            post = ReactionFactory(article=articles[i], author=profiles[j % nb_users].user, position=j+1)
            post.text = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
            post.text_html = emarkdown(post.text)
            post.save()


def load_comment_tutorial(cli, size, fake):
    """
    Load tutorial's comments
    """
    nb_avg_posts = size * 20
    cli.stdout.write(u"Nombres de messages à poster en moyenne dans un tutoriel : {}".format(nb_avg_posts))
    nb_tutorials = Tutorial.objects.filter(sha_public__isnull=False).count()
    tutorials = list(Tutorial.objects.filter(sha_public__isnull=False).all())
    nb_users = User.objects.count()
    profiles = list(Profile.objects.all())
    for i in range(0, nb_tutorials):
        nb = randint(0, nb_avg_posts * 2)
        for j in range(0, nb):
            post = NoteFactory(tutorial=tutorials[i], author=profiles[j % nb_tutorials].user, position=j+1)
            post.text = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
            post.text_html = emarkdown(post.text)
            post.save()


def load_tutorials(cli, size, fake):
    """
    Load tutorials
    """
    tutorials = []
    parts = []
    chapters = []

    nb_tutos = size * 10
    nb_avg_parts_in_tuto = size * 1
    nb_avg_chapters_in_tuto = size * 1
    cli.stdout.write(u"Nombres de big tutoriels à créer : {}".format(nb_tutos))
    nb_users = User.objects.count()
    profiles = list(Profile.objects.all())
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

    percent_tutos_validation_without_validator = 0.1
    percent_tutos_validation_with_validator = 0.1
    percent_tutos_in_beta = 0.1
    percent_tutos_public = 0.3
    tutorials_count = len(tutorials)
    cli.stdout.write(u"Nombres de big tutoriels sans validateurs : {}".format(str(int(tutorials_count * percent_tutos_validation_without_validator))))
    cli.stdout.write(u"Nombres de big tutoriels réservé en validations : {}".format(str(int(tutorials_count * percent_tutos_validation_with_validator))))
    cli.stdout.write(u"Nombres de big tutoriels en beta : {}".format(str(int(tutorials_count * percent_tutos_in_beta))))
    cli.stdout.write(u"Nombres de big tutoriels publiés : {}".format(str(int(tutorials_count * percent_tutos_public))))
    # code validation

@transaction.atomic
class Command(BaseCommand):
    args = '[low|medium|high]'
    help = 'Load fixtures for ZdS'

    def handle(self, *args, **options):
        default_size = "low"
        default_module = ["member", "staff", "category_forum", "forum", "tag", "topic", "post", "article", "note", "gallery", "tutorial", "reaction"]
        for arg in args:
            ps = arg.split("=")
            if len(ps) < 2:
                continue
            else:
                if ps[0] in ["size", "sizes", "taille", "level"]:
                    default_size = ps[1].split(",")[0]
                elif ps[0] in ["type", "types"]:
                    default_module = ps[1].split(",")

        if default_size == "low":
            size = 1
        elif default_size == "medium":
            size = 2
        elif default_size == "high":
            size = 3
        else:
            size = 1
        fake = Factory.create(locale="fr_FR")

        if "member" in default_module:
            load_member(self, size, fake)
        if "staff" in default_module:
            load_staff(self, size, fake)
        if "gallery" in default_module:
            load_gallery(self, size, fake)
        if "category_forum" in default_module:
            load_categories_forum(self, size, fake)
        if "forum" in default_module:
            load_forums(self, size, fake)
        if "tag" in default_module:
            load_tags(self, size, fake)
        if "topic" in default_module:
            load_topics(self, size, fake)
        if "post" in default_module:
            load_posts(self, size, fake)
        if "article" in default_module:
            load_articles(self, size, fake)
        if "tutorial" in default_module:
            load_tutorials(self, size, fake)
        if "reaction" in default_module:
            load_comment_article(self, size, fake)
        if "note" in default_module:
            load_comment_tutorial(self, size, fake)
