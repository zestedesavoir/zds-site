import collections
import contextlib
import logging
import random
import sys
import time

from datetime import datetime

from django.core.management.base import BaseCommand
from random import randint
from faker import Factory
from zds.utils.templatetags.emarkdown import emarkdown

from zds.forum.factories import CategoryFactory, ForumFactory, TopicFactory, PostFactory
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.member.factories import StaffProfileFactory, ProfileFactory
from django.contrib.auth.models import User, Permission
from zds.member.models import Profile
from zds.forum.models import Forum, Topic, Category as FCategory
from zds.utils.models import Tag, Category as TCategory, CategorySubCategory, SubCategory, Licence
from zds.utils import slugify
from django.conf import settings
from django.db import transaction, IntegrityError
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, \
    Validation as CValidation, ContentReactionFactory
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.publication_utils import publish_content


def load_member(cli, size, fake, root, *_):
    """
    Load members
    """
    nb_users = size * 10
    cli.stdout.write('Nombres de membres à créer : {}'.format(nb_users))
    tps1 = time.time()
    cpt = 1
    # member in settings
    users_set = ['admin',
                 settings.ZDS_APP['member']['external_account'],
                 settings.ZDS_APP['member']['anonymous_account']]
    for default_user in users_set:
        current_user = Profile.objects.filter(user__username=default_user).first()
        if current_user is None:
            profile = ProfileFactory(user__username=default_user)
            profile.user.set_password(default_user)
            profile.user.first_name = default_user
            profile.user.email = fake.free_email()
            if default_user == 'admin':
                profile.user.is_superuser = True
                profile.user.is_staff = True
            with contextlib.suppress(IntegrityError):
                profile.user.save()
                profile.site = fake.url()
                profile.biography = fake.text(max_nb_chars=200)
                profile.last_ip_address = fake.ipv4()
                profile.save()

    for i in range(0, nb_users):
        while Profile.objects.filter(user__username='{}{}'.format(root, cpt)).count() > 0:
            cpt += 1
        profile = ProfileFactory(user__username='{}{}'.format(root, cpt))
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
        sys.stdout.write(' User {}/{}  \r'.format(i + 1, nb_users))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def load_staff(cli, size, fake, root, *_):
    """
    Load staff
    """
    nb_staffs = size * 3
    cli.stdout.write('Nombres de staffs à créer : {}'.format(nb_staffs))
    tps1 = time.time()
    cpt = 1
    for i in range(0, nb_staffs):
        while Profile.objects.filter(user__username='{}staff{}'.format(root, cpt)).count() > 0:
            cpt += 1
        profile = StaffProfileFactory(user__username='{}staff{}'.format(root, cpt))
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
        sys.stdout.write(' Staff {}/{}  \r'.format(i + 1, nb_staffs))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def load_gallery(cli, size, fake, *_, **__):
    """
    Load galleries
    """
    nb_galleries = size * 1
    nb_images = size * 3
    cli.stdout.write('Nombres de galéries à créer par utilisateur: {}'.format(nb_galleries))
    cli.stdout.write("Nombres d'images à créer par gallerie: {}".format(nb_images))
    tps1 = time.time()
    nb_users = User.objects.count()
    if nb_users == 0:
        cli.stdout.write("Il n'y a aucun membre actuellement. "
                         'Vous devez rajouter les membres dans vos fixtures (member)')
        return
    profiles = list(Profile.objects.all())
    for user_index in range(0, nb_users):
        for gallery_index in range(0, nb_galleries):
            gal = GalleryFactory(title=fake.text(max_nb_chars=80), subtitle=fake.text(max_nb_chars=200))
            UserGalleryFactory(user=profiles[user_index].user, gallery=gal)
            __push_images_into_gallery(gal, user_index, gallery_index, nb_galleries, nb_images, nb_users)
    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def __push_images_into_gallery(gal, i, j, nb_galleries, nb_images, nb_users):
    for k in range(0, nb_images):
        ImageFactory(gallery=gal)
        sys.stdout.write(' User {}/{}  \tGallery {}/{}  \tImage {}/{}  \r'.
                         format(i + 1, nb_users, j + 1, nb_galleries, k + 1, nb_images))
        sys.stdout.flush()


def load_categories_forum(cli, size, fake, *_, **__):
    """
    Load categories
    """
    nb_categories = size * 4
    cli.stdout.write('Nombres de catégories de forum à créer : {}'.format(nb_categories))
    tps1 = time.time()
    for i in range(0, nb_categories):
        cat = CategoryFactory(position=i + 1)
        cat.title = fake.word()
        cat.save()
        sys.stdout.write(' Cat. {}/{}  \r'.format(i + 1, nb_categories))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def load_forums(cli, size, fake, *_, **__):
    """
    Load forums
    """
    nb_forums = size * 8
    cli.stdout.write('Nombres de Forums à créer : {}'.format(nb_forums))
    tps1 = time.time()
    nb_categories = FCategory.objects.count()
    if nb_categories == 0:
        cli.stdout.write("Il n'y a aucune catgorie actuellement. "
                         'Vous devez rajouter les categories de forum dans vos fixtures (category_forum)')
    else:
        categories = list(FCategory.objects.all())
        for i in range(0, nb_forums):
            with contextlib.suppress(IntegrityError):
                forum = ForumFactory(category=categories[i % nb_categories],
                                     position_in_category=(i / nb_categories) + 1)
                forum.title = fake.word()
                forum.subtitle = fake.sentence(nb_words=15, variable_nb_words=True)
                forum.save()
            sys.stdout.write(' Forum {}/{}  \r'.format(i + 1, nb_forums))
            sys.stdout.flush()
        tps2 = time.time()
        cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def load_tags(cli, size, fake, *_, **__):
    """
    Load tags
    """
    nb_tags = size * 30
    cli.stdout.write('Nombres de Tags de forum à créer : {}'.format(nb_tags))
    tps1 = time.time()
    for i in range(0, nb_tags):
        title = fake.word()
        with contextlib.suppress(IntegrityError):
            tag, created = Tag.objects.get_or_create(title=title.lower())
            logging.getLogger(cli.__class__.__name__).debug('tag=%s is_new=%s', tag, created)
        sys.stdout.write(' Tag {}/{}  \r'.format(i + 1, nb_tags))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def load_topics(cli, size, fake, *_, **__):
    """
    Load topics
    """
    nb_topics = size * 10
    cli.stdout.write('Nombres de Topics à créer : {}'.format(nb_topics))
    tps1 = time.time()
    nb_forums = Forum.objects.count()
    if nb_forums == 0:
        cli.stdout.write("Il n'y a aucun forum actuellement. "
                         'Vous devez rajouter les forums dans vos fixtures (forum)')
        return
    forums = list(Forum.objects.all())
    nb_users = User.objects.count()
    if nb_users == 0:
        cli.stdout.write("Il n'y a aucun membre actuellement. "
                         'Vous devez rajouter les membres dans vos fixtures (member)')
        return
    profiles = list(Profile.objects.all())
    nb_tags = Tag.objects.count()
    if nb_tags == 0:
        cli.stdout.write("Il n'y a aucun tag actuellement. "
                         'Vous devez rajouter les tags dans vos fixtures (tag)')
        return
    for i in range(0, nb_topics):
        with contextlib.suppress(IntegrityError):
            topic = TopicFactory(forum=forums[i % nb_forums], author=profiles[i % nb_users].user)
            topic.solved_by = profiles[i % nb_users].user if i % 5 else None
            topic.is_locked = i % 10 == 0
            topic.is_sticky = i % 15 == 0
            nb_rand_tags = random.randint(0, 5)
            add_generated_tags_to_topic(nb_rand_tags, nb_tags, topic)
            topic.title = fake.text(max_nb_chars=80)
            topic.subtitle = fake.text(max_nb_chars=200)
            topic.save()
            PostFactory(topic=topic, author=topic.author, position=1)
        sys.stdout.write(' Topic {}/{}  \r'.format(i + 1, nb_topics))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def add_generated_tags_to_topic(nb_rand_tags, nb_tags, topic):
    for _ in range(0, nb_rand_tags):
        my_random_tag = Tag.objects.filter(pk=random.randint(1, nb_tags)).first()
        if my_random_tag:
            topic.tags.add(my_random_tag)


def load_posts(cli, size, fake, *_, **__):
    """
    Load posts
    """
    nb_avg_posts_in_topic = size * 20
    cli.stdout.write('Nombres de messages à poster en moyenne dans un sujet : {}'.format(nb_avg_posts_in_topic))
    tps1 = time.time()
    nb_topics = Topic.objects.count()
    if nb_topics == 0:
        cli.stdout.write("Il n'y a aucun topic actuellement. "
                         'Vous devez rajouter les topics dans vos fixtures (topic)')
        return
    topics = list(Topic.objects.all())
    nb_users = User.objects.count()
    if nb_users == 0:
        cli.stdout.write("Il n'y a aucun membre actuellement. "
                         'Vous devez rajouter les membres dans vos fixtures (member)')
        return
    __generate_topic_and_post(cli, fake, nb_avg_posts_in_topic, nb_topics, nb_users, topics, tps1)


def __generate_topic_and_post(cli, fake, nb_avg_posts_in_topic, nb_topics, nb_users, topics, tps1):
    profiles = list(Profile.objects.all())
    for topic_index in range(0, nb_topics):
        nb_posts = randint(0, nb_avg_posts_in_topic * 2) + 1
        for post_index in range(1, nb_posts):
            post = PostFactory(topic=topics[topic_index], author=profiles[post_index % nb_users].user,
                               position=post_index + 1)
            post.text = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
            post.text_html = emarkdown(post.text)
            post.is_useful = int(nb_posts * 0.3) > 0 and post_index % int(nb_posts * 0.3) == 0
            post.save()
            sys.stdout.write(' Topic {}/{}  \tPost {}/{}  \r'.format(topic_index + 1,
                                                                     nb_topics, post_index + 1, nb_posts))
            sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def load_categories_content(cli, size, fake, *_, **__):
    """
    Load categories and subcategories for tutorial and article
    """

    lics = ['CB-BY', 'CC-BY-ND', 'CC-BY-ND-SA', 'CC-BY-SA', 'CC', 'CC-BY-IO', 'Tout-Droits']
    for lic in lics:
        ex = Licence.objects.filter(code=lic).all()
        if len(ex) is 0:
            licence = Licence(code=lic, title=lic, description='')
            licence.save()
            cli.stdout.write('Note: ajout de la licence {}'.format(lic))
    categories = []
    sub_categories = []
    nb_categories = size * 5
    nb_sub_categories = size * 10
    cli.stdout.write('Nombres de catégories de contenus à créer : {}'.format(nb_categories))
    cli.stdout.write('Nombres de sous-catégories de contenus à créer : {}'.format(nb_sub_categories))
    tps1 = time.time()
    for i in range(0, nb_categories):
        ttl = str(i) + ' ' + fake.job()
        cat = TCategory(title=ttl,
                        description=fake.sentence(nb_words=15, variable_nb_words=True),
                        slug=slugify(ttl))
        cat.save()
        categories.append(cat)
        sys.stdout.write(' Cat. {}/{}  \r'.format(i + 1, nb_categories))
        sys.stdout.flush()

    for i in range(0, nb_sub_categories):
        with contextlib.suppress(IntegrityError):
            ttl = str(i * 10) + str(i) + ' ' + fake.word()
            subcat = SubCategory(title=ttl,
                                 subtitle=fake.sentence(nb_words=5, variable_nb_words=True),
                                 slug=slugify(ttl))
            subcat.save()
            sub_categories.append(subcat)
        sys.stdout.write(' SubCat. {}/{}  \r'.format(i + 1, nb_sub_categories))
        sys.stdout.flush()

    for i in range(0, nb_sub_categories):
        with contextlib.suppress(IntegrityError):
            catsubcat = CategorySubCategory(category=categories[i % nb_categories],
                                            subcategory=sub_categories[i],
                                            is_main=True)
            catsubcat.save()
        sys.stdout.write(' CatSubCat. {}/{}  \r'.format(i + 1, nb_sub_categories))
        sys.stdout.flush()

    tps2 = time.time()
    cli.stdout.write('\nFait en {} sec'.format(tps2 - tps1))


def load_comment_content(cli, size, fake, *_, **__):
    """
    Load content's comments
    """
    nb_avg_posts = size * 20
    cli.stdout.write('Nombres de messages à poster en moyenne : {}'.format(nb_avg_posts))
    tps1 = time.time()
    contents = list(PublishableContent.objects.filter(sha_public__isnull=False))
    nb_contents = len(contents)
    profiles = list(Profile.objects.all())
    nb_users = len(profiles)
    for i in range(0, nb_contents):
        nb_posts = randint(0, nb_avg_posts * 2)
        post = None
        for j in range(0, nb_posts):
            post = ContentReactionFactory(
                related_content=contents[i], author=profiles[j % nb_users].user, position=j + 1)
            post.text = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
            post.text_html = emarkdown(post.text)
            post.save()
            sys.stdout.write('Contenu {}/{}  \tCommentaire {}/{}  \r'. format(i + 1, nb_contents, j + 1, nb_posts))
            sys.stdout.flush()
        contents[i].last_note = post
        contents[i].save()
    tps2 = time.time()
    cli.stdout.write('\nFait en {:.3f} sec'.format(tps2 - tps1))


def load_contents(cli, size, fake, _type, *_, **__):
    """Create v2 contents"""

    nb_contents = size * 10
    percent_contents_in_validation = 0.2
    percent_contents_with_validator = 0.1
    percent_contents_public = 0.6
    percent_mini = 0.5
    percent_medium = 0.3
    percent_big = 0.2
    nb_avg_containers_in_content = size
    nb_avg_extracts_in_content = size

    is_articles = _type == 'ARTICLE'
    is_tutorials = _type == 'TUTORIAL'
    is_opinion = _type == 'OPINION'

    textual_type = 'article'
    if is_tutorials:
        textual_type = 'tutoriel'
    elif is_opinion:
        textual_type = 'billet'

    # small introduction
    cli.stdout.write('À créer: {:d} {}s'.format(nb_contents, textual_type), ending='')

    if is_tutorials:
        cli.stdout.write(' ({:g} petits, {:g} moyens et {:g} grands)'
                         .format(nb_contents * percent_mini, nb_contents * percent_medium, nb_contents * percent_big))
    else:
        cli.stdout.write('')

    cli.stdout.write(
        ' - {:g} en brouillon'.format(
            nb_contents *
            (1 - percent_contents_public - percent_contents_in_validation - percent_contents_with_validator)))
    if is_opinion:
        cli.stdout.write(
            " - {:g} publiés et {:g} approuvés en page d'accueil".format(
                nb_contents * (percent_contents_in_validation + percent_contents_with_validator),
                nb_contents * percent_contents_with_validator))
    else:
        cli.stdout.write(
            ' - {:g} en validation (dont {:g} réservés)'
            .format(nb_contents * (percent_contents_in_validation + percent_contents_with_validator),
                    nb_contents * percent_contents_with_validator))
    cli.stdout.write(' - {:g} publiés'.format(nb_contents * percent_contents_public))

    tps1 = time.time()

    # create tables with 0=draft, 1=in validation, 2=reserved, 3=published
    what_to_do = []
    for created_content_index in range(nb_contents):
        what = 0  # in draft
        if created_content_index < percent_contents_public * nb_contents:
            what = 3
        elif created_content_index < (percent_contents_public + percent_contents_with_validator) * nb_contents:
            what = 2
        elif created_content_index >= (1 - percent_contents_in_validation) * nb_contents:
            what = 1
        what_to_do.append(what)

    # create a table with 0=mini, 1=medium, 2=big
    content_sizes = []
    for created_content_index in range(nb_contents):
        sz = 0
        if created_content_index < percent_big * nb_contents:
            sz = 2
        elif created_content_index >= (1 - percent_medium) * nb_contents:
            sz = 1
        content_sizes.append(sz)

    # shuffle the whole thing
    random.shuffle(what_to_do)
    random.shuffle(content_sizes)

    # checks that everything is ok
    users = list(Profile.objects.all())
    nb_users = len(users)
    sub_categories = list(SubCategory.objects.all())
    nb_sub_categories = len(sub_categories)
    if nb_users == 0:
        cli.stdout.write("Il n'y a aucun membre actuellement. "
                         'Vous devez rajouter les membre dans vos fixtures (member)')
        return

    if nb_sub_categories == 0:
        cli.stdout.write("Il n'y a aucune catégories actuellement."
                         'Vous devez rajouter les catégories dans vos fixtures (category_content)')
        return

    perms = list(Permission.objects.filter(codename__startswith='change_').all())
    staffs = list(User.objects.filter(groups__permissions__in=perms).all())
    nb_staffs = len(staffs)

    if nb_staffs == 0:
        cli.stdout.write("Il n'y a aucun staff actuellement."
                         'Vous devez rajouter les staffs dans vos fixtures (staff)')
        return

    licenses = list(Licence.objects.all())
    nb_licenses = len(licenses)

    if nb_licenses == 0:
        cli.stdout.write("Il n'y a aucune licence actuellement."
                         'Vous devez rajouter les licences dans vos fixtures (category_content)')
        return

    # create and so all:
    for created_content_index in range(nb_contents):
        sys.stdout.write('Création {} : {}/{}  \r'.format(textual_type, created_content_index + 1, nb_contents))

        current_size = content_sizes[created_content_index]
        action_flag = what_to_do[created_content_index]

        # creation:
        content = PublishableContentFactory(
            type=_type,
            title=fake.text(max_nb_chars=60),
            description=fake.sentence(nb_words=15, variable_nb_words=True))

        versioned = content.load_version()

        generate_text_for_content(current_size, fake, is_articles, is_opinion, nb_avg_containers_in_content,
                                  nb_avg_extracts_in_content, versioned)
        # add some informations:
        author = users[random.randint(0, nb_users - 1)].user
        content.authors.add(author)
        UserGalleryFactory(gallery=content.gallery, mode='W', user=author)
        content.licence = licenses[random.randint(0, nb_licenses - 1)]
        content.sha_draft = versioned.sha_draft
        content.subcategory.add(sub_categories[random.randint(0, nb_sub_categories - 1)])
        content.save()

        # then, validation if needed:
        if action_flag > 0:
            if is_opinion:
                publish_opinion(content, action_flag, versioned)
            else:
                validate_edited_content(content, fake, nb_staffs, staffs, action_flag, versioned)

        sys.stdout.flush()

    tps2 = time.time()
    cli.stdout.write('\nFait en {:.3f} sec'.format(tps2 - tps1))


def validate_edited_content(content, fake, nb_staffs, staffs, to_do, versioned):
    valid = CValidation(
        content=content, version=content.sha_draft, date_proposition=datetime.now(), status='PENDING')
    valid.comment_validator = fake.text(max_nb_chars=200)
    content.sha_validation = content.sha_draft
    if to_do > 1:  # reserve validation
        valid.date_reserve = datetime.now()
        valid.validator = staffs[random.randint(0, nb_staffs - 1)]
        valid.status = 'PENDING_V'
    if to_do > 2:  # publish content
        valid.comment_validator = fake.text(max_nb_chars=80)
        valid.status = 'ACCEPT'
        valid.date_validation = datetime.now()
        content.sha_public = content.sha_draft

        published = publish_content(content, versioned)
        content.public_version = published
    valid.save()
    content.save()


def generate_text_for_content(current_size, fake, is_articles, is_opinion, nb_avg_containers_in_content,
                              nb_avg_extracts_in_content, versioned):
    if current_size == 0 or is_articles or is_opinion:
        for _ in range(random.randint(1, nb_avg_extracts_in_content * 2)):
            ExtractFactory(container=versioned, title=fake.text(max_nb_chars=60), light=False)
    else:
        for _ in range(random.randint(1, nb_avg_containers_in_content * 2)):
            container = ContainerFactory(parent=versioned, title=fake.text(max_nb_chars=60))

            handle_content_with_chapter_and_parts(container, current_size, fake, nb_avg_containers_in_content,
                                                  nb_avg_extracts_in_content)


def publish_opinion(content, action_flag, versioned):
    if action_flag >= 1:
        content.sha_public = content.sha_draft
        if action_flag == 1:
            content.sha_picked = content.sha_draft
    published = publish_content(content, versioned)
    content.public_version = published
    content.save()


def handle_content_with_chapter_and_parts(container, current_size, fake, nb_avg_containers_in_content,
                                          nb_avg_extracts_in_content):
    if current_size == 1:  # medium size tutorial
        for k in range(random.randint(1, nb_avg_extracts_in_content * 2)):
            ExtractFactory(container=container, title=fake.text(max_nb_chars=60), light=False)
    else:  # big-size tutorial
        for k in range(random.randint(1, nb_avg_containers_in_content * 2)):
            subcontainer = ContainerFactory(parent=container, title=fake.text(max_nb_chars=60))

            for l in range(random.randint(1, nb_avg_extracts_in_content * 2)):
                ExtractFactory(container=subcontainer, title=fake.text(max_nb_chars=60), light=False)


ZDSResource = collections.namedtuple('zdsresource', ['name', 'description', 'callback', 'extra_args'])


@transaction.atomic
class Command(BaseCommand):

    zds_resource_config = [
        ZDSResource('member', 'basic users', load_member, tuple()),
        ZDSResource('staff', 'privileged users', load_staff, tuple()),
        ZDSResource('category_forum', 'categories for forums', load_categories_forum, tuple()),
        ZDSResource('category_content', 'categories for contents', load_categories_content, tuple()),
        ZDSResource('forum', 'forums', load_forums, tuple()),
        ZDSResource('tag', 'tags for forum topics', load_tags, tuple()),
        ZDSResource('topic', 'forum topics', load_topics, tuple()),
        ZDSResource('post', 'forum message', load_posts, tuple()),
        ZDSResource('gallery', 'image gallery for each member', load_gallery, tuple()),
        ZDSResource('article', 'article-typed publications, in draft, in validation and published',
                    load_contents, ('ARTICLE',)),
        ZDSResource('tutorial', 'tutorial-typed publications, in draft, in validation and published',
                    load_contents, ('TUTORIAL',)),
        ZDSResource('opinion', 'opinion-typed publications, in draft and published',
                    load_contents, ('OPINION',)),
        ZDSResource('comment', 'publication reactions.', load_comment_content, tuple()),
    ]

    def add_arguments(self, parser):
        parser.add_argument('--racine', action='store', default='user', type=str, dest='user_prefix',
                            help='The prefix for users. Default: user.')
        parser.add_argument('--size', action='store', default='low', dest='size', choices=['low', 'medium', 'high'],
                            type=str, help='Size level: low (x1), medium (x2) or high (x3). Default: low.')
        all_vs_one_per_one_switch = parser.add_mutually_exclusive_group()
        all_vs_one_per_one_switch.add_argument_group('all').add_argument('--all', dest='modules', action='store_const',
                                                                         const=self.__class__.zds_resource_config)
        group = all_vs_one_per_one_switch.add_argument_group('one_per_one')
        for zds_module in self.__class__.zds_resource_config:
            group.add_argument('--{}'.format(zds_module.name.replace('_', '-')), dest='modules',
                               help='add new {}.'.format(zds_module.description), action='append_const',
                               const=zds_module)

    help = """
        Load fixtures for ZdS

        Examples:
            All:
                python manage.py load_fixtures
            All with high size:
                python manage.py load_fixtures size=high
            Only users with medium size and a different prefix than bare "user":
                python manage.py load_fixtures --size=medium --member --staff --racine=john
    """

    def handle(self, *args, **options):
        size_map = {'low': 1, 'medium': 2, 'high': 3}
        size = size_map.get(options['size'], 1)
        default_root = options['user_prefix']
        populated_modules = options['modules']

        fake = Factory.create(locale='fr_FR')
        module_order = ('member', 'staff', 'gallery', 'category_forum', 'forum', 'tag', 'topic', 'post',
                        'category_content', 'tutorial', 'article', 'opinion', 'comment')
        populated_modules.sort(key=lambda zds_module: module_order.index(zds_module.name))
        for zds_module in populated_modules:
            zds_module.callback(self, size, fake, *zds_module.extra_args, root=default_root)
