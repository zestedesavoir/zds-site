from os.path import join
from pathlib import Path

from django.utils.translation import gettext_lazy as _

from .config import config
from .base_dir import BASE_DIR


zds_config = config.get('zds', {})


GEOIP_PATH = join(BASE_DIR, 'geodata')


ES_ENABLED = True

ES_CONNECTIONS = {
    'default': {
        'hosts': ['localhost:9200'],
    }
}

ES_SEARCH_INDEX = {
    'name': 'zds_search',
    'shards': 3,
    'replicas': 0,
}


# Anonymous [Dis]Likes. Authors of [dis]likes before those pk will never be shown
VOTES_ID_LIMIT = zds_config.get('VOTES_ID_LIMIT', 0)


THUMBNAIL_ALIASES = {
    '': {
        'avatar': {'size': (60, 60), 'crop': True},
        'avatar_mini': {'size': (24, 24), 'crop': True},
        'tutorial_illu': {'size': (60, 60), 'crop': True},
        'article_illu': {'size': (60, 60), 'crop': True},
        'content_thumb': {'size': (96, 96), 'crop': True},
        'help_illu': {'size': (48, 48), 'crop': True},
        'help_mini_illu': {'size': (26, 26), 'crop': True},
        'gallery': {'size': (120, 120), 'crop': True},
        'featured': {'size': (228, 228), 'crop': True},
        'gallery_illu': {'size': (480, 270), 'crop': True},
        'content': {'size': (960, 960), 'crop': False},
    },
}


ZDS_APP = {
    'site': {
        'name': 'ZesteDeSavoir',
        'literal_name': 'Zeste de Savoir',
        'slogan': 'Zeste de Savoir, la connaissance pour tous et sans pépins',
        'abbr': 'zds',
        'url': 'https://zestedesavoir.com',
        'dns': 'zestedesavoir.com',
        'email_contact': 'zestedesavoir@gmail.com',
        'email_noreply': 'noreply@zestedesavoir.com',
        'forum_feedback_users': '/forums/communaute/bug-suggestions/',
        'contribute_link': 'https://docs.zestedesavoir.com/contributing.html',
        'short_description': '',
        'long_description': 'Zeste de Savoir est un site de partage de connaissances '
                            'sur lequel vous trouverez des tutoriels de tous niveaux, '
                            'des articles et des forums d’entraide animés par et pour '
                            'la communauté.',
        'googleAnalyticsID': zds_config.get('google_analytics_id'),
        'googleTagManagerID': zds_config.get('google_tag_manager_id'),
        'association': {
            'name': 'Zeste de Savoir',
            'fee': zds_config.get('association_fee', '20 €'),
            'email': 'zestedesavoir@gmail.com',
            'email_ca': 'ca-zeste-de-savoir@googlegroups.com',
            'forum_ca_pk': 25
        },
        'repository': {
            'url': 'https://github.com/zestedesavoir/zds-site',
            'bugtracker': 'https://github.com/zestedesavoir/zds-site/issues',
            'api': 'https://api.github.com/repos/zestedesavoir/zds-site',
            'tags': [
                'C-Back', 'C-Front', 'C-API', 'C-Documentation', 'C-Infra', 'S-Bug', 'S-Régression',
                'S-Évolution'
            ]
        },
        'licenses': {
            'logo': {
                'code': 'CC-BY',
                'title': 'Creative Commons License',
                'description': 'Licence Creative Commons Attribution - Pas d’Utilisation Commerciale - '
                               'Partage dans les Mêmes Conditions 4.0 International.',
                'url_image': 'http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png',
                'url_license': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
                'author': 'MaxRoyo'
            },
            'cookies': {
                'code': 'CC-BY',
                'title': 'Licence Creative Commons',
                'description': 'licence Creative Commons Attribution 4.0 International',
                'url_image': 'http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png',
                'url_license': 'http://creativecommons.org/licenses/by-nc-sa/4.0/'
            },
            'source': {
                'code': 'GPL v3',
                'url_license': 'http://www.gnu.org/licenses/gpl-3.0.html',
                'provider_name': 'Progdupeupl',
                'provider_url': 'http://pdp.microjoe.org',
            },
            'licence_info_title': 'http://zestedesavoir.com/tutoriels/281/le-droit-dauteur-creative-commons-et-les-lic'
                                  'ences-sur-zeste-de-savoir/',
            'licence_info_link': 'Le droit d\'auteur, Creative Commons et les licences sur Zeste de Savoir'
        },
        'hosting': {
            'name': 'GANDI SAS',
            'address': '63-65 boulevard Massena - 75013 Paris - France'
        },
        'social': {
            'facebook': 'https://www.facebook.com/ZesteDeSavoir',
            'twitter': 'https://twitter.com/ZesteDeSavoir',
            'googleplus': 'https://plus.google.com/u/0/107033688356682807298'
        },
        'cnil': '1771020',
    },
    'member': {
        'bot_account': zds_config.get('member_bot_username', 'admin'),
        'anonymous_account': zds_config.get('member_anonymous_username', 'anonymous'),
        'external_account': zds_config.get('member_external_username', 'external'),
        'bot_group': 'bot',
        'dev_group': 'devs',
        'members_per_page': 100,
        'providers_per_page': 100,
        'hats_per_page': 50,
        'users_in_hats_list': 5,
        'requested_hats_per_page': 100,
        'update_last_visit_interval': 600,  # seconds
        'old_smileys_allowed': False,
        'old_smileys_cookie_key': 'use_old_smileys',
    },
    'hats': {
        'moderation': 'Staff',
        'validation': 'Staff',
        'hats_management': 'Staff',
    },
    'gallery': {
        'image_max_size': 1024 * 1024,
        'gallery_per_page': 21,
        'images_per_page': 21,
    },
    'tutorial': {
        'home_number': 4,
    },
    'article': {
        'home_number': 3
    },
    'opinions': {
        'home_number': 5
    },
    'content': {
        'repo_private_path': join(BASE_DIR, 'contents-private'),
        'repo_public_path': join(BASE_DIR, 'contents-public'),
        'extra_contents_dirname': 'extra_contents',
        # can also be 'extra_content_generation_policy': 'WATCHDOG'
        # or 'extra_content_generation_policy': 'NOTHING'
        'extra_content_generation_policy': 'SYNC',
        'extra_content_watchdog_dir': join(BASE_DIR, 'watchdog-build'),
        'max_tree_depth': 3,
        'default_licence_pk': 7,
        'content_per_page': 42,
        'max_last_publications_level_1': 6,
        'max_last_publications_level_2': 12,
        'max_last_publications_level_3': 12,
        'notes_per_page': 25,
        'helps_per_page': 20,
        'commits_per_page': 20,
        'feed_length': 5,
        'user_page_number': 5,
        'default_image': join(BASE_DIR, 'fixtures', 'noir_black.png'),
        'import_image_prefix': 'archive',
        'build_pdf_when_published': True,
        'maximum_slug_size': 150,
        'characters_per_minute': 1500,
        'editorial_line_link':
        'https://zestedesavoir.com/articles/222/la-ligne-editoriale-officielle-de-zeste-de-savoir/',
        'epub_stylesheets': {
            'toc': Path('toc.css'),
            'full': Path(BASE_DIR) / 'dist' / 'css' / 'zmd.css',
            'katex': Path(BASE_DIR) / 'dist' / 'css' / 'katex.min.css'
        },
        'latex_template_repo': 'NOT_EXISTING_DIR'
    },
    'forum': {
        'posts_per_page': 21,
        'topics_per_page': 21,
        'spam_limit_seconds': 60 * 15,
        'spam_limit_participant': 2,
        'beta_forum_id': zds_config.get('publications_being_written_forum_id', 1),
        'max_post_length': 1000000,
        'top_tag_max': 5,
        'home_number': 5,
        'old_post_limit_days': 90,
        # Exclude tags from top tags list. Tags listed here should not be relevant for most of users.
        # Be warned exclude too much tags can restrict performance
        'top_tag_exclu': ['bug', 'suggestion', 'tutoriel', 'beta', 'article']
    },
    'topic': {
        'home_number': 5,
    },
    'comment': {
        'max_pings': 15,
        # allow to mention (and notify) members in messages
        'enable_pings': True,
    },
    'featured_resource': {
        'featured_per_page': 100,
        'home_number': 5,
    },
    'notification': {
        'per_page': 50,
    },
    'paginator': {
        'folding_limit': 4
    },
    'search': {
        'mark_keywords': ['javafx', 'haskell', 'groovy', 'powershell', 'latex', 'linux', 'windows'],
        'results_per_page': 20,
        'search_groups': {
            'content': (
                _('Contenus publiés'), ['publishedcontent', 'chapter']
            ),
            'topic': (
                _('Sujets du forum'), ['topic']
            ),
            'post': (
                _('Messages du forum'), ['post']
            ),
        },
        'boosts': {
            'publishedcontent': {
                'global': 3.0,
                'if_article': 1.0,
                'if_tutorial': 1.0,
                'if_medium_or_big_tutorial': 1.5,
                'if_opinion': 0.66,
                'if_opinion_not_picked': 0.5
            },
            'topic': {
                'global': 2.0,
                'if_solved': 1.1,
                'if_sticky': 1.2,
                'if_locked': 0.1,
            },
            'chapter': {
                'global': 1.5,
            },
            'post': {
                'global': 1.0,
                'if_first': 1.2,
                'if_useful': 1.5,
                'ld_ratio_above_1': 1.05,
                'ld_ratio_below_1': 0.95,
            }
        }
    },
    'visual_changes': [],
    'display_search_bar': True,
    'zmd': {
        'server': 'http://127.0.0.1:27272',
        'disable_pings': False
    },
    'stats_ga_viewid': 'ga:86962671'
}
