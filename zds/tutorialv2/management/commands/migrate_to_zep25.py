# coding: utf-8

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_text
from django.utils.text import slugify

from zds import settings
from zds.tutorialv2.models.models_database import PublishableContent
from zds.utils.models import Category, SubCategory, CategorySubCategory, Tag
from zds.utils.mps import send_mp


def categories_to_tags():
    """
    Change all content categories to tags.

    :return: None
    """
    contents = PublishableContent.objects.all()
    for content in contents:
        categories = content.subcategory.all()
        for cat in categories:
            tag_title = smart_text(cat.slug.replace('-', ' ').strip().lower())
            current_tag = Tag.objects.filter(title=tag_title).first()
            if current_tag is None:
                current_tag = Tag(title=tag_title)
                current_tag.save()
                print("[ZEP-25] : Tag \"{}\" added".format(current_tag))
            content.tags.add(current_tag)
        content.save()


def update_categories():
    """
    Delete all categories and create new ones.

    :return: None
    """
    for cat in SubCategory.objects.all():
        cat.delete()
    for cat in Category.objects.all():
        cat.delete()
    for cat in CategorySubCategory.objects.all():
        cat.delete()
    print('[ZEP-25] : Categories and subcatagories deleted')
    categories = ['Informatique', 'Sciences de la nature', 'Sciences humaines et sociales', 'Autres']
    subcategories = [
        # Informatique
        [
            ('Bureautique et rédaction', 'Excel, LaTeX, Powerpoint, Word'),
            ('Matériel et électronique', 'Arduino, Disque dur, DIY, Electronique*, Mémoires, Ordinateur'),
            ('Programmation et algorithmique', '.NET, Ada, Algorithmique, C, C#, C++, Cobol, Fonctionnel, Génie logicie'
                                               'l, Haskell, Java, Julia, Lisp, Ocaml, Orienté objet, Python, Ruby, Vers'
                                               'ioning'),
            ('Site web', 'Accessibilité, Actionscript, Angular JS, CakePHP, Django, HTML/CSS, Java EE, JavaScript, Ngin'
                         'x, Node.js, Oxygen, PHP, Ruby On Rails, SEO/Réferencement*, Symfony, Websocket'),
            ('Systèmes d\'exploitation', 'Android, GNU/Linux, iOS, MAC OS, Windows, Windows Phone'),
            ('Autres', 'API, Base de données, FTP, Jeux vidéos, MySQL, Oracle, Protocole, Sécurité, TCP/IP'),
        ],
        # Sciences de la nature
        [
            ('Astronomie', 'Astronomie'),
            ('Géologie et géographie physique', 'Géologie'),
            ('Biologie', 'Biologie'),
            ('Physique', 'Physique'),
            ('Chimie', 'Chimie'),
            ('Mathématiques', 'Mathématiques'),
            ('Autres', 'Autres sciences de la nature')
        ],
        # Sciences humaines et sociales
        [
            ('Droit', 'Droit'),
            ('Histoire', 'Histoire'),
            ('Langues', 'Langues'),
            ('Psychologie', 'Psychologie, Pédagogie'),
            ('Économie', 'Économie'),
            ('Autres', 'Autres sciences humaines et sociales comme la géographie')
        ],
        # Autres
        [
            ('Arts, graphisme et multimédia', 'Graphisme 2D, Graphisme 3D, Musique, Son'),
            ('Communication et management', 'Monde du travail'),
            ('Zeste de Savoir', 'Zeste de Savoir'),
            ('Autres', 'Littérature, Interview')
        ]
    ]
    i = 0
    for category in categories:
        cat = Category()
        cat.title = category
        cat.description = category
        cat.position = i
        cat.slug = slugify(u'{}'.format(category))
        cat.save()
        print('[ZEP-25] : Category "{}" added'.format(cat))
        for subcategory in subcategories[i]:
            sub = SubCategory()
            sub.title = subcategory[0]
            sub.subtitle = subcategory[1]
            sub.slug = slugify(u'{}'.format(subcategory[0]))
            sub.save()
            print('[ZEP-25] : Subcategory "{}" added'.format(sub))
            catsubcat = CategorySubCategory()
            catsubcat.category = cat
            catsubcat.subcategory = sub
            catsubcat.save()
            print('[ZEP-25] : Relation "{}" <--> "{}" added'.format(cat, sub))
        i += 1


def alert_authors():
    """
    Send a private message to all authors for new tags system.

    :return: None
    """
    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
    users = []
    contents = PublishableContent.objects.all()
    for content in contents:
        authors = content.authors.all()
        for author in authors:
            if author not in users:
                users.append(author)
    for user in users:
        msg = 'Bonjour {0},\n\nDepuis la dernière version de Zeste de Savoir, tous les contenus (articles, tutoriels ' \
              'et bientôt tribunes libres) possèdent maintenant une nouvelle classification ([ZEP-25](https://zestede' \
              'savoir.com/forums/sujet/2378/zep-25-categorisation-des-articles-et-tutoriels/)). Les **tags** ont fait' \
              ' leur apparition et les catégories ont été revues afin de faciliter et d\'aléger cette classification.' \
              '\n\nLes anciennes catégories ont été transformées en tags et de nouvelles catégories plus générales on' \
              't été ajoutés. L\'équipe de Zeste de Savoir va (ou a déjà) changé les catégories des contenus publiés.' \
              '\n\nNous vous invitons à vérifier la catégorie de vos [articles](https://zestedesavoir.com/contenus/ar' \
              'ticles/{1}/) et [tutoriels](https://zestedesavoir.com/contenus/tutoriels/{1}/) mais également la perti' \
              'nence des tags et en ajouter si besoin.\n\n\nNous restons à votre disposition et votre écoute pour tou' \
              'tes suggestions ou remarques,\n\nL\'équipe de Zeste de Savoir'
        send_mp(
            bot,
            [user],
            'Changement de classification du contenu sur Zeste de Savoir',
            'Ce qui change pour vous en tant qu\'auteur',
            msg
        )
        print('[ZEP-25] : PM send to {}'.format(user))


@transaction.atomic
class Command(BaseCommand):
    help = 'Change all content categories to tags (ZEP-25).\n\n\nOptions:\n\n  No options run all commands (except he' \
           'lp) in this order : tags, categories, alert\n\n  alert         Send a private message to all authors for ' \
           'new tags system\n  categories    Delete all categories and create new ones\n  help          Show this mes' \
           'sage\n  tags          Change all content categories to tags'

    def handle(self, *args, **options):
        if len(args) > 0:
            if args[0] == 'alert':
                alert_authors()
            elif args[0] == 'categories':
                update_categories()
            elif args[0] == 'help':
                print(self.help)
            elif args[0] == 'tags':
                categories_to_tags()
            else:
                print('Unknow option.')
                print(self.help)
        else:
            categories_to_tags()
            update_categories()
            alert_authors()
