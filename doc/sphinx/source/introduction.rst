.. _introduction_toplevel:

==================
Installation
==================

Zeste de Savoir est un site internet communautaire codé à l'aide du framework Django 1.6 et de Python 2.7

Lien du site : `zestedesavoir <http://www.zestedesavoir.com>`_

Si vous voulez installer et démarrer une instance locale de ZdS, vous devez cliquer sur le lien correspondant à votre système d'exploitation.

.. toctree::
   :maxdepth: 2

   install/install-windows
   install/install-os-x
   install/install-linux

Il est possible de personnaliser ZdS pour n'importe quel site communautaire de partage. Un ensemble de paramètres est disponible dans le fichier ``settings.py`` via un dictionnaire. Vous pourrez donc écraser ces variables par défaut dans votre fichier ``settings_prod.py``. Le dictionnaire de variables relatives au site est donc le suivant :

.. sourcecode:: python

    ZDS_APP = {
        'site': {
            'name': u"ZesteDeSavoir",
            'litteral_name': u"Zeste de Savoir",
            'slogan': u"Zeste de Savoir, la connaissance pour tous et sans pépins",
            'abbr': u"zds",
            'url': u"http://127.0.0.1:8000",
            'dns': u"zestedesavoir.com",
            'email_contact': u"communication@zestedesavoir.com",
            'email_noreply': u"noreply@zestedesavoir.com",
            'repository': u"https://github.com/zestedesavoir/zds-site",
            'short_description': u"",
            'long_description': u"Zeste de Savoir est un site de partage de connaissances "
                                u"sur lequel vous trouverez des tutoriels de tous niveaux, "
                                u"des articles et des forums d'entraide animés par et pour "
                                u"la communauté.",
            'year': u"2014",
            'association': {
                'name': u"Zeste de Savoir",
                'fee': u"30 €",
                'email': u"association@zestedesavoir.com",
                'email_ca': u"ca-zeste-de-savoir@googlegroups.com"
            },
            'hosting': {
                'name': u"OVH",
                'address': u"2 rue Kellermann - 59100 Roubaix - France"
            },
            'cnil': u"1771020",
        },
        'member': {
            'bot_account': u"admin",
            'members_per_page': 100,
        },
        'gallery': {
            'image_max_size': 1024 * 1024,
        },
        'article': {
            'repo_path': os.path.join(SITE_ROOT, 'articles-data'),
        },
        'tutorial': {
            'repo_path': os.path.join(SITE_ROOT, 'tutoriels-private'),
            'repo_public_path': os.path.join(SITE_ROOT, 'tutoriels-public'),
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

