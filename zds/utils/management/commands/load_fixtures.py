# coding: utf-8

import random
import sys
import time

from datetime import datetime
from django.core.management.base import BaseCommand
from random import randint
from faker import Factory
from zds.utils.templatetags.emarkdown import emarkdown

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.tutorial.factories import BigTutorialFactory, PartFactory, ChapterFactory, NoteFactory, MiniTutorialFactory,\
    ExtractFactory
from zds.article.factories import ReactionFactory, ArticleFactory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.member.factories import StaffProfileFactory, ProfileFactory
from django.contrib.auth.models import User, Permission
from zds.member.models import Profile
from zds.article.models import Article, Validation as AValidation
from zds.tutorial.models import Tutorial, Validation as TValidation
from zds.tutorial.views import mep as mep_tuto
from zds.article.views import mep as mep_art
from zds.forum.models import Forum, Topic, Category as FCategory
from zds.utils.models import Tag, Category as TCategory, CategorySubCategory, SubCategory, Licence
from zds.utils import slugify
from zds import settings
from django.db import transaction


def load_member(cli, size, fake, root):
    """
    Load members
    """
    nb_users = size * 10
    cli.stdout.write(u"Nombres de membres à créer : {}".format(nb_users))
    tps1 = time.time()
    cpt = 1
    # member in settings
    users_set = ["admin",
                 settings.ZDS_APP["member"]["external_account"],
                 settings.ZDS_APP["member"]["anonymous_account"]]
    for u in users_set:
        us = Profile.objects.filter(user__username=u).first()
        if us is None:
            profile = ProfileFactory(user__username=u)
            profile.user.set_password(u)
            profile.user.first_name = u
            profile.user.email = fake.free_email()
            if u == "admin":
                profile.user.is_superuser = True
                profile.user.is_staff = True
            profile.user.save()
            profile.site = fake.url()
            profile.biography = fake.text(max_nb_chars=200)
            profile.last_ip_address = fake.ipv4()
            profile.save()

    for i in range(0, nb_users):
        while Profile.objects.filter(user__username="{}{}".format(root, cpt)).count() > 0:
            cpt += 1
        profile = ProfileFactory(user__username="{}{}".format(root, cpt))
        profile.user.set_password(profile.user.username)
        profile.user.first_name = fake.first_name()
        profile.user.last_name = fake.last_name()
        profile.user.email = fake.free_email()
        profile.user.save()
        profile.site = fake.url()
        profile.biography = fake.text(max_nb_chars=200)
        profile.last_ip_address = fake.ipv4()
        profile.save()
        cpt += 1
        sys.stdout.write(" User {}/{}  \r".format(i+1, nb_users))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_staff(cli, size, fake, root):
    """
    Load staff
    """
    nb_staffs = size * 3
    cli.stdout.write(u"Nombres de staffs à créer : {}".format(nb_staffs))
    tps1 = time.time()
    cpt = 1
    for i in range(0, nb_staffs):
        while Profile.objects.filter(user__username="{}staff{}".format(root, cpt)).count() > 0:
            cpt += 1
        profile = StaffProfileFactory(user__username="{}staff{}".format(root, cpt))
        profile.user.first_name = fake.first_name()
        profile.user.last_name = fake.last_name()
        profile.user.email = fake.free_email()
        profile.user.save()
        profile.site = fake.url()
        profile.biography = fake.paragraph()
        profile.sign = fake.text(max_nb_chars=80)
        profile.last_ip_address = fake.ipv6()
        profile.save()
        cpt += 1
        sys.stdout.write(" Staff {}/{}  \r".format(i+1, nb_staffs))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_gallery(cli, size, fake):
    """
    Load galleries
    """
    nb_galleries = size * 3
    nb_images = size * 5
    cli.stdout.write(u"Nombres de galéries à créer par utilisateur: {}".format(nb_galleries))
    cli.stdout.write(u"Nombres d'images à créer par gallerie: {}".format(nb_images))
    tps1 = time.time()
    nb_users = User.objects.count()
    if nb_users == 0:
        cli.stdout.write(u"Il n'y a aucun membre actuellement. "
                         u"Vous devez rajouter les membres dans vos fixtures (member)")
    else:
        profiles = list(Profile.objects.all())
        for i in range(0, nb_users):
            for j in range(0, nb_galleries):
                gal = GalleryFactory(title=fake.text(max_nb_chars=80), subtitle=fake.text(max_nb_chars=200))
                UserGalleryFactory(user=profiles[i].user, gallery=gal)
                for k in range(0, nb_images):
                    ImageFactory(gallery=gal)
                    sys.stdout.write(" User {}/{}  \tGallery {}/{}  \tImage {}/{}  \r".
                                     format(i+1, nb_users,
                                            j+1, nb_galleries,
                                            k+1, nb_images))
                    sys.stdout.flush()
        tps2 = time.time()
        cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_categories_forum(cli, size, fake):
    """
    Load categories
    """
    nb_categories = size * 2
    cli.stdout.write(u"Nombres de catégories de forum à créer : {}".format(nb_categories))
    tps1 = time.time()
    for i in range(0, nb_categories):
        cat = CategoryFactory(position=i + 1)
        cat.title = fake.word()
        cat.save()
        sys.stdout.write(" Cat. {}/{}  \r".format(i+1, nb_categories))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_forums(cli, size, fake):
    """
    Load forums
    """
    nb_forums = size * 8
    cli.stdout.write(u"Nombres de Forums à créer : {}".format(nb_forums))
    tps1 = time.time()
    nb_categories = FCategory.objects.count()
    if nb_categories == 0:
        cli.stdout.write(u"Il n'y a aucune catgorie actuellement. "
                         u"Vous devez rajouter les categories de forum dans vos fixtures (category_forum)")
    else:
        categories = list(FCategory.objects.all())
        for i in range(0, nb_forums):
            forum = ForumFactory(category=categories[i % nb_categories],
                                 position_in_category=(i / nb_categories) + 1)
            forum.title = fake.word()
            forum.subtitle = fake.sentence(nb_words=15, variable_nb_words=True)
            forum.save()
            sys.stdout.write(" Forum {}/{}  \r".format(i+1, nb_forums))
            sys.stdout.flush()
        tps2 = time.time()
        cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_tags(cli, size, fake):
    """
    Load tags
    """
    nb_tags = size * 50
    cli.stdout.write(u"Nombres de Tags de forum à créer : {}".format(nb_tags))
    tps1 = time.time()
    for i in range(0, nb_tags):
        title = fake.word()
        t = Tag(title=title, slug=slugify(title))
        t.save()
        sys.stdout.write(" Tag {}/{}  \r".format(i+1, nb_tags))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_topics(cli, size, fake):
    """
    Load topics
    """
    nb_topics = size * 20
    cli.stdout.write(u"Nombres de Topics à créer : {}".format(nb_topics))
    tps1 = time.time()
    nb_forums = Forum.objects.count()
    if nb_forums == 0:
        cli.stdout.write(u"Il n'y a aucun forum actuellement. "
                         u"Vous devez rajouter les forums dans vos fixtures (forum)")
    else:
        forums = list(Forum.objects.all())
        nb_users = User.objects.count()
        if nb_users == 0:
            cli.stdout.write(u"Il n'y a aucun membre actuellement. "
                             u"Vous devez rajouter les membres dans vos fixtures (member)")
        else:
            profiles = list(Profile.objects.all())
            nb_tags = Tag.objects.count()
            if nb_tags == 0:
                cli.stdout.write(u"Il n'y a aucun tag actuellement. "
                                 u"Vous devez rajouter les tags dans vos fixtures (tag)")
            else:
                for i in range(0, nb_topics):
                    topic = TopicFactory(forum=forums[i % nb_forums], author=profiles[i % nb_users].user)
                    if i % 5 == 0:
                        topic.is_solved = True
                    if i % 10 == 0:
                        topic.is_locked = True
                    if i % 15 == 0:
                        topic.is_sticky = True
                    nb_rand_tags = random.randint(0, 5)
                    for k in range(0, nb_rand_tags):
                        my_random_tag = Tag.objects.filter(pk=random.randint(1, nb_tags)).first()
                        if my_random_tag:
                            topic.tags.add(my_random_tag)
                    topic.title = fake.text(max_nb_chars=80)
                    topic.subtitle = fake.text(max_nb_chars=200)
                    topic.save()
                    sys.stdout.write(" Topic {}/{}  \r".format(i+1, nb_topics))
                    sys.stdout.flush()
                tps2 = time.time()
                cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_posts(cli, size, fake):
    """
    Load posts
    """
    nb_avg_posts_in_topic = size * 10
    cli.stdout.write(u"Nombres de messages à poster en moyenne dans un sujet : {}".format(nb_avg_posts_in_topic))
    tps1 = time.time()
    nb_topics = Topic.objects.count()
    if nb_topics == 0:
        cli.stdout.write(u"Il n'y a aucun topic actuellement. "
                         u"Vous devez rajouter les topics dans vos fixtures (topic)")
    else:
        topics = list(Topic.objects.all())
        nb_users = User.objects.count()
        if nb_users == 0:
            cli.stdout.write(u"Il n'y a aucun membre actuellement. "
                             u"Vous devez rajouter les membres dans vos fixtures (member)")
        else:
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
                    if int(nb * 0.3) > 0:
                        if j % int(nb * 0.3) == 0:
                            post.is_useful = True
                    post.save()
                    sys.stdout.write(" Topic {}/{}  \tPost {}/{}  \r".
                                     format(i+1, nb_topics,
                                            j+1, nb))
                    sys.stdout.flush()
            tps2 = time.time()
            cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_categories_content(cli, size, fake):
    """
    Load categories and subcategories for tutorial and article
    """

    lics = ["CB-BY", "CC-BY-ND", "CC-BY-ND-SA", "CC-BY-SA", "CC", "CC-BY-IO", "Tout-Droits"]
    for lic in lics:
        ex = Licence.objects.filter(code=lic)
        if ex is None:
            l = Licence(code=lic, title=lic, description="")
            l.save()
    categories = []
    sub_categories = []
    nb_categories = size * 5
    nb_sub_categories = size * 10
    cli.stdout.write(u"Nombres de catégories de contenus à créer : {}".format(nb_categories))
    cli.stdout.write(u"Nombres de sous-catégories de contenus à créer : {}".format(nb_sub_categories))
    tps1 = time.time()
    for i in range(0, nb_categories):
        ttl = fake.word()
        cat = TCategory(title=ttl,
                        description=fake.sentence(nb_words=15, variable_nb_words=True),
                        slug=slugify(ttl))
        cat.save()
        categories.append(cat)
        sys.stdout.write(" Cat. {}/{}  \r".format(i+1, nb_categories))
        sys.stdout.flush()

    for i in range(0, nb_sub_categories):
        ttl = fake.word()
        cat = SubCategory(title=ttl,
                          subtitle=fake.sentence(nb_words=5, variable_nb_words=True),
                          slug=slugify(ttl))
        cat.save()
        sub_categories.append(cat)
        sys.stdout.write(" SubCat. {}/{}  \r".format(i+1, nb_sub_categories))
        sys.stdout.flush()

    for i in range(0, nb_sub_categories):
        h = CategorySubCategory(category=categories[i % nb_categories], subcategory=sub_categories[i], is_main=True)
        h.save()
        sys.stdout.write(" CatSubCat. {}/{}  \r".format(i+1, nb_sub_categories))
        sys.stdout.flush()

    tps2 = time.time()
    cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_comment_article(cli, size, fake):
    """
    Load article's comments
    """
    nb_avg_posts = size * 20
    cli.stdout.write(u"Nombres de messages à poster en moyenne dans un article : {}".format(nb_avg_posts))
    tps1 = time.time()
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
            sys.stdout.write(" Article {}/{}  \tComment {}/{}  \r".
                             format(i+1, nb_articles,
                                    j+1, nb))
            sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_comment_tutorial(cli, size, fake):
    """
    Load tutorial's comments
    """
    nb_avg_posts = size * 20
    cli.stdout.write(u"Nombres de messages à poster en moyenne dans un tutoriel : {}".format(nb_avg_posts))
    tps1 = time.time()
    nb_tutorials = Tutorial.objects.filter(sha_public__isnull=False).count()
    tutorials = list(Tutorial.objects.filter(sha_public__isnull=False).all())
    nb_users = User.objects.count()
    profiles = list(Profile.objects.all())
    for i in range(0, nb_tutorials):
        nb = randint(0, nb_avg_posts * 2)
        for j in range(0, nb):
            post = NoteFactory(tutorial=tutorials[i], author=profiles[j % nb_users].user, position=j+1)
            post.text = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
            post.text_html = emarkdown(post.text)
            post.save()
            sys.stdout.write(" Tuto {}/{}  \tComment {}/{}  \r".
                             format(i+1, nb_tutorials,
                                    j+1, nb))
            sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_tutorials(cli, size, fake):
    """
    Load tutorials
    """

    tutorials = []
    parts = []
    chapters = []

    nb_tutos = size * 10
    percent_tutos_validation_in_validation = 0.4
    percent_tutos_validation_with_validator = 0.2
    percent_tutos_public = 0.3
    nb_avg_parts_in_tuto = size * 1
    nb_avg_chapters_in_tuto = size * 1
    nb_avg_extracts_in_tuto = size * 1
    cli.stdout.write(u"Nombres de big tutoriels à créer : {}".format(nb_tutos))
    cli.stdout.write(u"Nombres de big tutoriels en validations : {}"
                     .format(str(int(nb_tutos * percent_tutos_validation_in_validation))))
    cli.stdout.write(u"Nombres de big tutoriels réservé en validations : {}"
                     .format(str(int(nb_tutos * percent_tutos_validation_with_validator))))
    cli.stdout.write(u"Nombres de big tutoriels publiés : {}"
                     .format(str(int(nb_tutos * percent_tutos_public))))
    cli.stdout.write(u"Nombres de mini tutoriels à créer : {}".format(nb_tutos))
    cli.stdout.write(u"Nombres de mini tutoriels en validations : {}"
                     .format(str(int(nb_tutos * percent_tutos_validation_in_validation))))
    cli.stdout.write(u"Nombres de mini tutoriels réservé en validations : {}"
                     .format(str(int(nb_tutos * percent_tutos_validation_with_validator))))
    cli.stdout.write(u"Nombres de mini tutoriels publiés : {}"
                     .format(str(int(nb_tutos * percent_tutos_public))))
    tps1 = time.time()
    nb_users = User.objects.count()
    if nb_users == 0:
        cli.stdout.write(u"Il n'y a aucun membre actuellement."
                         u"Vous devez rajouter les membre dans vos fixtures (member)")
    else:
        profiles = list(Profile.objects.all())
        nb_sub_categories = SubCategory.objects.count()
        if nb_sub_categories == 0:
            cli.stdout.write(u"Il n'y a aucune catégories actuellement."
                             u"Vous devez rajouter les membre dans vos fixtures (category_content)")
        else:
            sub_categories = list(SubCategory.objects.all())
            perms = list(Permission.objects.filter(codename__startswith='change_').all())
            staffs = list(User.objects.filter(groups__permissions__in=perms).all())
            nb_staffs = len(staffs)
            if nb_staffs == 0:
                cli.stdout.write(u"Il n'y a aucun staff actuellement."
                                 u"Vous devez rajouter les staffs dans vos fixtures (staff)")
            else:
                # big tutorials
                for i in range(0, nb_tutos):
                    tuto = BigTutorialFactory(title=fake.text(max_nb_chars=80),
                                              description=fake.sentence(nb_words=15, variable_nb_words=True))
                    tuto.authors.add(profiles[i % nb_users].user)
                    tuto.subcategory.add(sub_categories[random.randint(0, nb_sub_categories-1)])
                    tutorials.append(tuto)
                    nb_part = randint(0, nb_avg_parts_in_tuto * 2)
                    for j in range(0, nb_part):
                        parts.append(PartFactory(tutorial=tutorials[i],
                                                 position_in_tutorial=j,
                                                 title=fake.text(max_nb_chars=80)))
                        nb_chap = randint(0, nb_avg_chapters_in_tuto * 2)
                        for k in range(0, nb_chap):
                            chapters.append(ChapterFactory(part=parts[j],
                                                           position_in_part=k,
                                                           position_in_tutorial=j * k,
                                                           title=fake.text(max_nb_chars=80)))
                            nb_ext = randint(0, nb_avg_extracts_in_tuto * 2)
                            for l in range(0, nb_ext):
                                ExtractFactory(chapter=chapters[k],
                                               position_in_chapter=l,
                                               title=fake.text(max_nb_chars=80))
                    if i < int(nb_tutos * percent_tutos_validation_with_validator):
                        validator = staffs[random.randint(0, nb_staffs-1)]
                        v = TValidation(tutorial=tuto,
                                        version=tuto.sha_draft,
                                        date_proposition=datetime.now(),
                                        date_reserve=datetime.now(),
                                        validator=validator,
                                        status="PENDING_V")
                        v.save()
                        tuto.sha_validation = tuto.sha_draft
                        tuto.save()
                    elif i < int(nb_tutos * (percent_tutos_validation_in_validation
                                             + percent_tutos_validation_with_validator)):
                        v = TValidation(tutorial=tuto,
                                        version=tuto.sha_draft,
                                        date_proposition=datetime.now())
                        v.save()
                        tuto.sha_validation = tuto.sha_draft
                        tuto.save()
                    elif i < int(nb_tutos * (percent_tutos_validation_in_validation
                                             + percent_tutos_validation_with_validator
                                             + percent_tutos_public)):
                        mep_tuto(tuto, tuto.sha_draft)
                        v = TValidation(tutorial=tuto,
                                        version=tuto.sha_draft,
                                        date_proposition=datetime.now(),
                                        date_reserve=datetime.now(),
                                        validator=validator,
                                        status="ACCEPT",
                                        comment_validator=fake.text(max_nb_chars=200),
                                        date_validation=datetime.now())
                        v.save()
                        tuto.sha_public = tuto.sha_draft
                        tuto.save()
                    sys.stdout.write(" Big Tuto {}/{}  \r".format(i+1, nb_tutos))
                    sys.stdout.flush()

                # Mini tutorials
                for i in range(0, nb_tutos):
                    tuto = MiniTutorialFactory(title=fake.text(max_nb_chars=80),
                                               description=fake.sentence(nb_words=15, variable_nb_words=True))
                    tuto.authors.add(profiles[i % nb_users].user)
                    tuto.subcategory.add(sub_categories[random.randint(0, nb_sub_categories-1)])
                    tutorials.append(tuto)
                    chap = ChapterFactory(tutorial=tutorials[j])
                    nb_ext = randint(0, nb_avg_extracts_in_tuto * 2)
                    for l in range(0, nb_ext):
                        ExtractFactory(chapter=chap,
                                       position_in_chapter=l,
                                       title=fake.text(max_nb_chars=80))
                    if i < int(nb_tutos * percent_tutos_validation_with_validator):
                        validator = staffs[random.randint(0, nb_staffs-1)]
                        v = TValidation(tutorial=tuto,
                                        version=tuto.sha_draft,
                                        date_proposition=datetime.now(),
                                        date_reserve=datetime.now(),
                                        validator=validator,
                                        status="PENDING_V")
                        v.save()
                        tuto.sha_validation = tuto.sha_draft
                        tuto.save()
                    elif i < int(nb_tutos * (percent_tutos_validation_in_validation
                                             + percent_tutos_validation_with_validator)):
                        v = TValidation(tutorial=tuto,
                                        version=tuto.sha_draft,
                                        date_proposition=datetime.now())
                        v.save()
                        tuto.sha_validation = tuto.sha_draft
                        tuto.save()
                    elif i < int(nb_tutos * (percent_tutos_validation_in_validation
                                             + percent_tutos_validation_with_validator
                                             + percent_tutos_public)):
                        mep_tuto(tuto, tuto.sha_draft)
                        v = TValidation(tutorial=tuto,
                                        version=tuto.sha_draft,
                                        date_proposition=datetime.now(),
                                        date_reserve=datetime.now(),
                                        validator=validator,
                                        status="ACCEPT",
                                        comment_validator=fake.text(max_nb_chars=200),
                                        date_validation=datetime.now())
                        v.save()
                        tuto.sha_public = tuto.sha_draft
                        tuto.save()
                    sys.stdout.write(" Mini Tuto {}/{}  \r".format(i+1, nb_tutos))
                    sys.stdout.flush()

                tps2 = time.time()
                cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


def load_articles(cli, size, fake):
    """
    Load articles
    """

    articles = []

    nb_arts = size * 10
    percent_arts_validation_in_validation = 0.4
    percent_arts_validation_with_validator = 0.2
    percent_arts_public = 0.3
    cli.stdout.write(u"Nombres d'articles à créer : {}".format(nb_arts))
    cli.stdout.write(u"Nombres d'articles en validations : {}"
                     .format(str(int(nb_arts * percent_arts_validation_in_validation))))
    cli.stdout.write(u"Nombres d'articles réservé en validations : {}"
                     .format(str(int(nb_arts * percent_arts_validation_with_validator))))
    cli.stdout.write(u"Nombres d'articles publiés : {}"
                     .format(str(int(nb_arts * percent_arts_public))))
    tps1 = time.time()
    nb_users = User.objects.count()
    if nb_users == 0:
        cli.stdout.write(u"Il n'y a aucun membre actuellement."
                         u"Vous devez rajouter les membre dans vos fixtures (member)")
    else:
        nb_sub_categories = SubCategory.objects.count()
        if nb_sub_categories == 0:
            cli.stdout.write(u"Il n'y a aucune catégories actuellement."
                             u"Vous devez rajouter les membre dans vos fixtures (category_content)")
        else:
            sub_categories = list(SubCategory.objects.all())
            profiles = list(Profile.objects.all())
            perms = list(Permission.objects.filter(codename__startswith='change_').all())
            staffs = list(User.objects.filter(groups__permissions__in=perms).all())
            nb_staffs = len(staffs)
            if nb_staffs == 0:
                cli.stdout.write(u"Il n'y a aucun staff actuellement."
                                 u"Vous devez rajouter les staffs dans vos fixtures (staff)")
            else:
                for i in range(0, nb_arts):
                    art = ArticleFactory(title=fake.text(max_nb_chars=80),
                                         description=fake.sentence(nb_words=15, variable_nb_words=True))
                    art.authors.add(profiles[i % nb_users].user)
                    art.subcategory.add(sub_categories[random.randint(0, nb_sub_categories-1)])
                    articles.append(art)

                    if i < int(nb_arts * percent_arts_validation_with_validator):
                        validator = staffs[random.randint(0, nb_staffs-1)]
                        v = AValidation(article=art,
                                        version=art.sha_draft,
                                        date_proposition=datetime.now(),
                                        date_reserve=datetime.now(),
                                        validator=validator,
                                        status="PENDING_V")
                        v.save()
                        art.sha_validation = art.sha_draft
                        art.save()
                    elif i < int(nb_arts * (percent_arts_validation_in_validation
                                            + percent_arts_validation_with_validator)):
                        v = AValidation(article=art,
                                        version=art.sha_draft,
                                        date_proposition=datetime.now())
                        v.save()
                        art.sha_validation = art.sha_draft
                        art.save()
                    elif i < int(nb_arts * (percent_arts_validation_in_validation
                                            + percent_arts_validation_with_validator
                                            + percent_arts_public)):
                        mep_art(art, art.sha_draft)
                        v = AValidation(article=art,
                                        version=art.sha_draft,
                                        date_proposition=datetime.now(),
                                        date_reserve=datetime.now(),
                                        validator=validator,
                                        status="ACCEPT",
                                        comment_validator=fake.text(max_nb_chars=200),
                                        date_validation=datetime.now())
                        v.save()
                        art.sha_public = art.sha_draft
                        art.pubdate = datetime.now()
                        art.save()
                    sys.stdout.write(" Article {}/{}  \r".format(i+1, nb_arts))
                    sys.stdout.flush()

                tps2 = time.time()
                cli.stdout.write(u"\nFait en {} sec".format(tps2 - tps1))


@transaction.atomic
class Command(BaseCommand):
    args = 'size=[low|medium|high] type=member,staff,gallery,category_forum,category_content'
    help = 'Load fixtures for ZdS'
    # python manage.py load_fixtures size=low module=staff racine=user

    def handle(self, *args, **options):
        default_size = "low"
        default_root = "user"
        default_module = ["member",
                          "staff",
                          "category_forum",
                          "category_content",
                          "forum",
                          "tag",
                          "topic",
                          "post",
                          "article",
                          "note",
                          "gallery",
                          "tutorial",
                          "reaction"]
        for arg in args:
            ps = arg.split("=")
            if len(ps) < 2:
                continue
            else:
                if ps[0] in ["size", "sizes", "taille", "level"]:
                    default_size = ps[1].split(",")[0]
                elif ps[0] in ["type", "types"]:
                    default_module = ps[1].split(",")
                elif ps[0] in ["racine"]:
                    default_root = ps[1].split(",")[0]

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
            load_member(self, size, fake, default_root)
        if "staff" in default_module:
            load_staff(self, size, fake, default_root)
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
        if "category_content" in default_module:
            load_categories_content(self, size, fake)
        if "article" in default_module:
            load_articles(self, size, fake)
        if "reaction" in default_module:
            load_comment_article(self, size, fake)
        if "tutorial" in default_module:
            load_tutorials(self, size, fake)
        if "note" in default_module:
            load_comment_tutorial(self, size, fake)
