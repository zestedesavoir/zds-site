# coding: utf-8

# ZDS settings

import os


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SDZ_TUTO_DIR = ''

ZDS_APP = {
    'site': {
        'name': u'ZesteDeSavoir',
        'litteral_name': u'Zeste de Savoir',
        'slogan': u'Zeste de Savoir, la connaissance pour tous et sans pépins',
        'abbr': u'zds',
        'url': u'http://127.0.0.1:8000',
        'dns': u'zestedesavoir.com',
        'email_contact': u'communication@zestedesavoir.com',
        'email_noreply': u'noreply@zestedesavoir.com',
        'repository': u'https://github.com/zestedesavoir/zds-site',
        'short_description': u'',
        'long_description': u'Zeste de Savoir est un site de partage de connaissances '
                            u'sur lequel vous trouverez des tutoriels de tous niveaux, '
                            u'des articles et des forums d\'entraide animés par et pour '
                            u'la communauté.',
        'year': u'2014',
        'association': {
            'name': u'Zeste de Savoir',
            'fee': u'30 €',
            'email': u'association@zestedesavoir.com',
            'email_ca': u'ca-zeste-de-savoir@googlegroups.com'
        },
        'licenses': {
            'logo': {
                'code': u'CC-BY',
                'title': u'Creative Commons License',
                'description': u'Licence Creative Commons Attribution - Pas d’Utilisation Commerciale - Partage dans'
                               u' les Mêmes Conditions 4.0 International.',
                'url_image': u'http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png',
                'url_license': u'http://creativecommons.org/licenses/by-nc-sa/4.0/',
                'author': u'MaxRoyo'
            },
            'cookies': {
                'code': u'CC-BY',
                'title': u'Licence Creative Commons',
                'description': u'licence Creative Commons Attribution 4.0 International',
                'url_image': u'http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png',
                'url_license': u'http://creativecommons.org/licenses/by-nc-sa/4.0/'
            },
            'source': {
                'code': u'GPL v3',
                'url_license': u'http://www.gnu.org/licenses/gpl-3.0.html',
                'provider_name': u'Progdupeupl',
                'provider_url': u'http://progdupeu.pl',
            }
        },
        'hosting': {
            'name': u'OVH',
            'address': u'2 rue Kellermann - 59100 Roubaix - France'
        },
        'cnil': u'1771020',
    },
    'member': {
        'bot_account': u'admin',
        'anonymous_account': u'anonymous',
        'external_account': u'external',
        'members_per_page': 100,
    },
    'gallery': {
        'image_max_size': 1024 * 1024,
    },
    'article': {
        'repo_path': os.path.join(BASE_DIR, 'articles-data'),
    },
    'tutorial': {
        'repo_path': os.path.join(BASE_DIR, 'tutoriels-private'),
        'repo_public_path': os.path.join(BASE_DIR, 'tutoriels-public'),
        'default_license_pk': 7
    },
    'forum': {
        'posts_per_page': 21,
        'topics_per_page': 21,
        'spam_limit_seconds': 60 * 15,
        'spam_limit_participant': 2,
        'followed_topics_per_page': 21,
        'beta_forum_id': 1,
        'max_post_length': 1000000,
        'top_tag_max': 5,
    }
}
