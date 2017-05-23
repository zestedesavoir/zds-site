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
from zds.gallery.factories import GalleryFactory, UserGalleryFactory, ImageFactory
from zds.member.factories import StaffProfileFactory, ProfileFactory
from django.contrib.auth.models import User, Permission
from zds.member.models import Profile
from zds.forum.models import Forum, Topic, Category as FCategory
from zds.utils.models import Tag, Category as TCategory, CategorySubCategory, SubCategory, Licence
from zds.utils import slugify
from zds import settings
from django.db import transaction
from zds.tutorialv2.factories import PublishableContentFactory, ContainerFactory, ExtractFactory, \
    Validation as CValidation, ContentReactionFactory
from zds.tutorialv2.models.models_database import PublishableContent
from zds.tutorialv2.publication_utils import publish_content


def load_member(cli, size, fake, root):
    """
    Load members
    """
    nb_users = size * 10
    cli.stdout.write(u'Nombres de membres à créer : {}'.format(nb_users))
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
    cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_staff(cli, size, fake, root):
    """
    Load staff
    """
    nb_staffs = size * 3
    cli.stdout.write(u'Nombres de staffs à créer : {}'.format(nb_staffs))
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
    cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_gallery(cli, size, fake):
    """
    Load galleries
    """
    nb_galleries = size * 1
    nb_images = size * 3
    cli.stdout.write(u'Nombres de galéries à créer par utilisateur: {}'.format(nb_galleries))
    cli.stdout.write(u"Nombres d'images à créer par gallerie: {}".format(nb_images))
    tps1 = time.time()
    nb_users = User.objects.count()
    if nb_users == 0:
        cli.stdout.write(u"Il n'y a aucun membre actuellement. "
                         u'Vous devez rajouter les membres dans vos fixtures (member)')
    else:
        profiles = list(Profile.objects.all())
        for i in range(0, nb_users):
            for j in range(0, nb_galleries):
                gal = GalleryFactory(title=fake.text(max_nb_chars=80), subtitle=fake.text(max_nb_chars=200))
                UserGalleryFactory(user=profiles[i].user, gallery=gal)
                for k in range(0, nb_images):
                    ImageFactory(gallery=gal)
                    sys.stdout.write(' User {}/{}  \tGallery {}/{}  \tImage {}/{}  \r'.
                                     format(i + 1, nb_users, j + 1, nb_galleries, k + 1, nb_images))
                    sys.stdout.flush()
        tps2 = time.time()
        cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_categories_forum(cli, size, fake):
    """
    Load categories
    """
    nb_categories = size * 4
    cli.stdout.write(u'Nombres de catégories de forum à créer : {}'.format(nb_categories))
    tps1 = time.time()
    for i in range(0, nb_categories):
        cat = CategoryFactory(position=i + 1)
        cat.title = fake.word()
        cat.save()
        sys.stdout.write(' Cat. {}/{}  \r'.format(i + 1, nb_categories))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_forums(cli, size, fake):
    """
    Load forums
    """
    nb_forums = size * 8
    cli.stdout.write(u'Nombres de Forums à créer : {}'.format(nb_forums))
    tps1 = time.time()
    nb_categories = FCategory.objects.count()
    if nb_categories == 0:
        cli.stdout.write(u"Il n'y a aucune catgorie actuellement. "
                         u'Vous devez rajouter les categories de forum dans vos fixtures (category_forum)')
    else:
        categories = list(FCategory.objects.all())
        for i in range(0, nb_forums):
            forum = ForumFactory(category=categories[i % nb_categories],
                                 position_in_category=(i / nb_categories) + 1)
            forum.title = fake.word()
            forum.subtitle = fake.sentence(nb_words=15, variable_nb_words=True)
            forum.save()
            sys.stdout.write(' Forum {}/{}  \r'.format(i + 1, nb_forums))
            sys.stdout.flush()
        tps2 = time.time()
        cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_tags(cli, size, fake):
    """
    Load tags
    """
    nb_tags = size * 30
    cli.stdout.write(u'Nombres de Tags de forum à créer : {}'.format(nb_tags))
    tps1 = time.time()
    for i in range(0, nb_tags):
        title = fake.word()
        tag, created = Tag.objects.get_or_create(title=title.lower())
        sys.stdout.write(' Tag {}/{}  \r'.format(i + 1, nb_tags))
        sys.stdout.flush()
    tps2 = time.time()
    cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_topics(cli, size, fake):
    """
    Load topics
    """
    nb_topics = size * 10
    cli.stdout.write(u'Nombres de Topics à créer : {}'.format(nb_topics))
    tps1 = time.time()
    nb_forums = Forum.objects.count()
    if nb_forums == 0:
        cli.stdout.write(u"Il n'y a aucun forum actuellement. "
                         u'Vous devez rajouter les forums dans vos fixtures (forum)')
    else:
        forums = list(Forum.objects.all())
        nb_users = User.objects.count()
        if nb_users == 0:
            cli.stdout.write(u"Il n'y a aucun membre actuellement. "
                             u'Vous devez rajouter les membres dans vos fixtures (member)')
        else:
            profiles = list(Profile.objects.all())
            nb_tags = Tag.objects.count()
            if nb_tags == 0:
                cli.stdout.write(u"Il n'y a aucun tag actuellement. "
                                 u'Vous devez rajouter les tags dans vos fixtures (tag)')
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
                    PostFactory(topic=topic, author=topic.author, position=1)
                    sys.stdout.write(' Topic {}/{}  \r'.format(i + 1, nb_topics))
                    sys.stdout.flush()
                tps2 = time.time()
                cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_posts(cli, size, fake):
    """
    Load posts
    """
    nb_avg_posts_in_topic = size * 20
    cli.stdout.write(u'Nombres de messages à poster en moyenne dans un sujet : {}'.format(nb_avg_posts_in_topic))
    tps1 = time.time()
    nb_topics = Topic.objects.count()
    if nb_topics == 0:
        cli.stdout.write(u"Il n'y a aucun topic actuellement. "
                         u'Vous devez rajouter les topics dans vos fixtures (topic)')
    else:
        topics = list(Topic.objects.all())
        nb_users = User.objects.count()
        if nb_users == 0:
            cli.stdout.write(u"Il n'y a aucun membre actuellement. "
                             u'Vous devez rajouter les membres dans vos fixtures (member)')
        else:
            profiles = list(Profile.objects.all())
            for i in range(0, nb_topics):
                nb_posts = randint(0, nb_avg_posts_in_topic * 2) + 1
                for j in range(1, nb_posts):
                    post = PostFactory(topic=topics[i], author=profiles[j % nb_users].user, position=j + 1)
                    post.text = fake.paragraph(nb_sentences=5, variable_nb_sentences=True)
                    post.text_html = emarkdown(post.text)
                    if int(nb_posts * 0.3) > 0:
                        if j % int(nb_posts * 0.3) == 0:
                            post.is_useful = True
                    post.save()
                    sys.stdout.write(' Topic {}/{}  \tPost {}/{}  \r'.format(i + 1, nb_topics, j + 1, nb_posts))
                    sys.stdout.flush()
            tps2 = time.time()
            cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_categories_content(cli, size, fake):
    """
    Load categories and subcategories for tutorial and article
    """

    lics = ['CB-BY', 'CC-BY-ND', 'CC-BY-ND-SA', 'CC-BY-SA', 'CC', 'CC-BY-IO', 'Tout-Droits']
    for lic in lics:
        ex = Licence.objects.filter(code=lic).all()
        if len(ex) is 0:
            licence = Licence(code=lic, title=lic, description='')
            licence.save()
            cli.stdout.write(u'Note: ajout de la licence {}'.format(lic))
    categories = []
    sub_categories = []
    nb_categories = size * 5
    nb_sub_categories = size * 10
    cli.stdout.write(u'Nombres de catégories de contenus à créer : {}'.format(nb_categories))
    cli.stdout.write(u'Nombres de sous-catégories de contenus à créer : {}'.format(nb_sub_categories))
    tps1 = time.time()
    for i in range(0, nb_categories):
        ttl = fake.word() + str(i)
        cat = TCategory(title=ttl,
                        description=fake.sentence(nb_words=15, variable_nb_words=True),
                        slug=slugify(ttl))
        cat.save()
        categories.append(cat)
        sys.stdout.write(' Cat. {}/{}  \r'.format(i + 1, nb_categories))
        sys.stdout.flush()

    for i in range(0, nb_sub_categories):
        ttl = fake.word() + str(i * 10) + str(i)
        subcat = SubCategory(title=ttl,
                             subtitle=fake.sentence(nb_words=5, variable_nb_words=True),
                             slug=slugify(ttl))
        subcat.save()
        sub_categories.append(subcat)
        sys.stdout.write(' SubCat. {}/{}  \r'.format(i + 1, nb_sub_categories))
        sys.stdout.flush()

    for i in range(0, nb_sub_categories):
        catsubcat = CategorySubCategory(category=categories[i % nb_categories],
                                        subcategory=sub_categories[i],
                                        is_main=True)
        catsubcat.save()
        sys.stdout.write(' CatSubCat. {}/{}  \r'.format(i + 1, nb_sub_categories))
        sys.stdout.flush()

    tps2 = time.time()
    cli.stdout.write(u'\nFait en {} sec'.format(tps2 - tps1))


def load_comment_content(cli, size, fake):
    """
    Load content's comments
    """
    nb_avg_posts = size * 20
    cli.stdout.write(u'Nombres de messages à poster en moyenne : {}'.format(nb_avg_posts))
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
    cli.stdout.write(u'\nFait en {:.3f} sec'.format(tps2 - tps1))


def load_contents(cli, _type, size, fake):
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

    textual_type = u'article'
    if is_tutorials:
        textual_type = u'tutoriel'
    elif is_opinion:
        textual_type = u'billet'

    # small introduction
    cli.stdout.write(u'À créer: {:d} {}s'.format(nb_contents, textual_type), ending='')

    if is_tutorials:
        cli.stdout.write(u' ({:g} petits, {:g} moyens et {:g} grands)'
                         .format(nb_contents * percent_mini, nb_contents * percent_medium, nb_contents * percent_big))
    else:
        cli.stdout.write('')

    cli.stdout.write(
        u' - {:g} en brouillon'.format(
            nb_contents *
            (1 - percent_contents_public - percent_contents_in_validation - percent_contents_with_validator)))
    if is_opinion:
        cli.stdout.write(
            u' - {:g} publiés et aprouvés'.format(
                nb_contents * (percent_contents_in_validation + percent_contents_with_validator),
                nb_contents * percent_contents_with_validator))
    else:
        cli.stdout.write(
            u' - {:g} en validation (dont {:g} réservés)'
            .format(nb_contents * (percent_contents_in_validation + percent_contents_with_validator),
                    nb_contents * percent_contents_with_validator))
    cli.stdout.write(u' - {:g} publiés'.format(nb_contents * percent_contents_public))

    tps1 = time.time()

    # create tables with 0=draft, 1=in validation, 2=reserved, 3=published
    what_to_do = []
    for i in range(nb_contents):
        what = 0  # in draft
        if i < percent_contents_public * nb_contents:
            what = 3
        elif i < (percent_contents_public + percent_contents_with_validator) * nb_contents:
            what = 2
        elif i >= (1 - percent_contents_in_validation) * nb_contents:
            what = 1
        what_to_do.append(what)

    # create a table with 0=mini, 1=medium, 2=big
    content_sizes = []
    for i in range(nb_contents):
        sz = 0
        if i < percent_big * nb_contents:
            sz = 2
        elif i >= (1 - percent_medium) * nb_contents:
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
        cli.stdout.write(u"Il n'y a aucun membre actuellement. "
                         u'Vous devez rajouter les membre dans vos fixtures (member)')
        return

    if nb_sub_categories == 0:
        cli.stdout.write(u"Il n'y a aucune catégories actuellement."
                         u'Vous devez rajouter les catégories dans vos fixtures (category_content)')
        return

    perms = list(Permission.objects.filter(codename__startswith='change_').all())
    staffs = list(User.objects.filter(groups__permissions__in=perms).all())
    nb_staffs = len(staffs)

    if nb_staffs == 0:
        cli.stdout.write(u"Il n'y a aucun staff actuellement."
                         u'Vous devez rajouter les staffs dans vos fixtures (staff)')
        return

    licenses = list(Licence.objects.all())
    nb_licenses = len(licenses)

    if nb_licenses == 0:
        cli.stdout.write(u"Il n'y a aucune licence actuellement."
                         u'Vous devez rajouter les licences dans vos fixtures (category_content)')
        return

    # create and so all:
    for i in range(nb_contents):
        sys.stdout.write('Création {} : {}/{}  \r'.format(textual_type, i + 1, nb_contents))

        current_size = content_sizes[i]
        to_do = what_to_do[i]

        # creation:
        content = PublishableContentFactory(
            type=_type,
            title=fake.text(max_nb_chars=60),
            description=fake.sentence(nb_words=15, variable_nb_words=True))

        versioned = content.load_version()

        if current_size == 0 or is_articles or is_opinion:
            for j in range(random.randint(1, nb_avg_extracts_in_content * 2)):
                ExtractFactory(container=versioned, title=fake.text(max_nb_chars=60), light=False)
        else:
            for j in range(random.randint(1, nb_avg_containers_in_content * 2)):
                container = ContainerFactory(parent=versioned, title=fake.text(max_nb_chars=60))

                if current_size == 1:  # medium size tutorial
                    for k in range(random.randint(1, nb_avg_extracts_in_content * 2)):
                        ExtractFactory(container=container, title=fake.text(max_nb_chars=60), light=False)
                else:  # big-size tutorial
                    for k in range(random.randint(1, nb_avg_containers_in_content * 2)):
                        subcontainer = ContainerFactory(parent=container, title=fake.text(max_nb_chars=60))

                        for l in range(random.randint(1, nb_avg_extracts_in_content * 2)):
                            ExtractFactory(container=subcontainer, title=fake.text(max_nb_chars=60), light=False)

        # add some informations:
        author = users[random.randint(0, nb_users - 1)].user
        content.authors.add(author)
        UserGalleryFactory(gallery=content.gallery, mode='W', user=author)
        content.licence = licenses[random.randint(0, nb_licenses - 1)]
        content.sha_draft = versioned.sha_draft
        content.subcategory.add(sub_categories[random.randint(0, nb_sub_categories - 1)])
        content.save()

        # then, validation if needed:
        if to_do > 0:
            if is_opinion:
                if to_do >= 1:
                    content.sha_public = content.sha_draft
                    if to_do == 1:
                        content.sha_picked = content.sha_draft
                published = publish_content(content, versioned)
                content.public_version = published
                content.save()

            else:
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

        sys.stdout.flush()

    tps2 = time.time()
    cli.stdout.write(u'\nFait en {:.3f} sec'.format(tps2 - tps1))


@transaction.atomic
class Command(BaseCommand):

    zds_modules = ','.join([
        'member',
        'staff',
        'category_forum',
        'category_content',
        'forum',
        'tag',
        'topic',
        'post',
        'note',
        'gallery',
        'article',
        'tutorial',
        'opinion',
        'comment',
        'reaction'
    ])

    def add_arguments(self, parser):
        parser.add_argument('racine', action='store', nargs='?', default='user', type=str,
                            help='The prefix for users. Default: user.')
        parser.add_argument('size', action='store', nargs='?', default='low', choices=['low', 'medium', 'high'],
                            type=str, help='Size level: low (x1), medium (x2) or high (x3). Default: low.')
        parser.add_argument('type', action='store', nargs='*', type=str, default=self.zds_modules,
                            help='Type of content you want to create. You could add many types separated by a comma. '
                                 'Default: all types.')

    help = '''Load fixtures for ZdS

Examples:
    All:
        python manage.py load_fixtures
    All with high size:
        python manage.py load_fixtures size=high
    Only users with medium size and a different racine:
        python manage.py load_fixtures size=medium type=member,staff racine=john'''

    def handle(self, *args, **options):
        default_size = options.get('size', 'low')
        default_root = options.get('racine', 'user')
        default_module = options.get('type', self.zds_modules)

        if default_size == 'low':
            size = 1
        elif default_size == 'medium':
            size = 2
        elif default_size == 'high':
            size = 3
        else:
            size = 1
        fake = Factory.create(locale='fr_FR')

        if 'member' in default_module:
            load_member(self, size, fake, default_root)
        if 'staff' in default_module:
            load_staff(self, size, fake, default_root)
        if 'gallery' in default_module:
            load_gallery(self, size, fake)
        if 'category_forum' in default_module:
            load_categories_forum(self, size, fake)
        if 'forum' in default_module:
            load_forums(self, size, fake)
        if 'tag' in default_module:
            load_tags(self, size, fake)
        if 'topic' in default_module:
            load_topics(self, size, fake)
        if 'post' in default_module:
            load_posts(self, size, fake)
        if 'category_content' in default_module:
            load_categories_content(self, size, fake)
        if 'tutorial' in default_module:
            load_contents(self, 'TUTORIAL', size, fake)
        if 'article' in default_module:
            load_contents(self, 'ARTICLE', size, fake)
        if 'opinion' in default_module:
            load_contents(self, 'OPINION', size, fake)
        if 'comment' in default_module:
            load_comment_content(self, size, fake)
