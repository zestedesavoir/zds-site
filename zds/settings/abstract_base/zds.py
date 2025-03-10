from pathlib import Path

from django.utils.translation import gettext_lazy as _

from .base_dir import BASE_DIR
from .config import config

zds_config = config.get("zds", {})

LOGOUT_REDIRECT_URL = "homepage"

GEOIP_PATH = str(BASE_DIR / "geodata")
GEOIP_CITY = "GeoLite2-City.mmdb"

SEARCH_ENABLED = True

SEARCH_CONNECTION = {
    "nodes": [
        {
            "host": "localhost",
            "port": "8108",
            "protocol": "http",
        }
    ],
    "api_key": "xyz",
    "connection_timeout_seconds": 10,  # seconds; Gunicorn's default timeout is 30 s
}

# Anonymous [Dis]Likes. Authors of [dis]likes before those pk will never be shown
VOTES_ID_LIMIT = zds_config.get("VOTES_ID_LIMIT", 0)

THUMBNAIL_ALIASES = {
    "": {
        "avatar": {"size": (60, 60), "crop": True},
        "avatar_mini": {"size": (24, 24), "crop": True},
        "tutorial_illu": {"size": (60, 60), "crop": True},
        "article_illu": {"size": (60, 60), "crop": True},
        "content_thumb": {"size": (96, 96), "crop": True},
        "help_illu": {"size": (48, 48), "crop": True},
        "help_mini_illu": {"size": (26, 26), "crop": True},
        "gallery": {"size": (120, 120), "crop": True},
        "featured": {"size": (228, 228), "crop": True},
        "gallery_illu": {"size": (480, 270), "crop": True},
        "content": {"size": (960, 960), "crop": False},
        "social_network": {"size": (144, 144), "crop": True},
        #                           ^^^  ^^^ -> minimum dimensions of 144x144
        # https://developer.twitter.com/en/docs/tweets/optimize-with-cards/overview/summary
        "social_network_large": {"size": (600, 314), "crop": True},
    },
}

DEFAULT_ASSO_LINK = "https://www.helloasso.com/associations/zeste-de-savoir/adhesions/zeste-de-savoir-cotisations-2018"

global_weight_publishedcontent = 2
global_weight_topic = 2
global_weight_chapter = 1.5
global_weight_post = 0.8

ZDS_APP = {
    "site": {
        "name": "ZesteDeSavoir",
        "literal_name": "Zeste de Savoir",
        "slogan": "Zeste de Savoir, la connaissance pour tous et sans pépins",
        "abbr": "zds",
        "url": "https://zestedesavoir.com",
        "dns": "zestedesavoir.com",
        "email_contact": "zestedesavoir@gmail.com",
        "email_asso_accessibility": "association+accessibilite@zestedesavoir.com",
        "email_tech_accessibility": "technique+accessibilite@zestedesavoir.com",
        "email_noreply": "noreply@zestedesavoir.com",
        "forum_feedback_users": "/forums/communaute/bug-suggestions/",
        "contribute_link": "https://docs.zestedesavoir.com/contributing.html",
        "short_description": "",
        "long_description": "Zeste de Savoir est un site de partage de connaissances "
        "sur lequel vous trouverez des tutoriels de tous niveaux, "
        "des articles et des forums d’entraide animés par et pour "
        "la communauté.",
        "matomo_tracking_enabled": zds_config.get("matomo_tracking_enabled", False),
        "matomo_site_id": zds_config.get("matomo_site_id", 4),
        "matomo_url": zds_config.get("matomo_url", "https://matomo.zestedesavoir.com"),
        "matomo_token_auth": zds_config.get("matomo_token_auth", ""),
        "association": {
            "name": "Zeste de Savoir",
            "email": "zestedesavoir@gmail.com",
            "email_ca": "ca-zeste-de-savoir@googlegroups.com",
            "forum_ca_pk": 25,
            "subscribe_link": zds_config.get("association_subscribe_link", DEFAULT_ASSO_LINK),
        },
        "licenses": {
            "logo": {
                "code": "CC-BY",
                "title": "Creative Commons License",
                "description": "Licence Creative Commons Attribution - Pas d’Utilisation Commerciale - "
                "Partage dans les Mêmes Conditions 4.0 International.",
                "url_image": "http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png",
                "url_license": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
                "author": "MaxRoyo",
            },
            "cookies": {
                "code": "CC-BY",
                "title": "Licence Creative Commons",
                "description": "licence Creative Commons Attribution 4.0 International",
                "url_image": "http://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png",
                "url_license": "http://creativecommons.org/licenses/by-nc-sa/4.0/",
            },
            "source": {
                "code": "GPL v3",
                "url_license": "http://www.gnu.org/licenses/gpl-3.0.html",
                "provider_name": "Progdupeupl",
                "provider_url": "https://github.com/progdupeupl/pdp_website",
            },
            "licence_info_title": "http://zestedesavoir.com/tutoriels/281/le-droit-dauteur-creative-commons-et-les-lic"
            "ences-sur-zeste-de-savoir/",
            "licence_info_link": "Le droit d'auteur, Creative Commons et les licences sur Zeste de Savoir",
        },
        "hosting": {"name": "GANDI SAS", "address": "63-65 boulevard Massena - 75013 Paris - France"},
        "social": {
            "mastodon": "https://framapiaf.org/@ZesteDeSavoir",
            "facebook": "https://www.facebook.com/ZesteDeSavoir",
            "X": "https://x.com/ZesteDeSavoir",
            "github": "https://github.com/zestedesavoir/zds-site",
            "discord": "https://discord.com/invite/ue5MTKq",
        },
        "cnil": "1771020",
    },
    "github_projects": {
        "base_url": "https://github.com/{}".format,
        "bugtracker": "https://github.com/{}/issues".format,
        "issues_api": "https://api.github.com/repos/{}/issues".format,
        "default_repository": "zestedesavoir/zds-site",
        "repositories": [
            "zestedesavoir/zds-site",
            "zestedesavoir/zmarkdown",
        ],
    },
    "member": {
        "bot_account": zds_config.get("member_bot_username", "bot"),
        "anonymous_account": zds_config.get("member_anonymous_username", "anonymous"),
        "external_account": zds_config.get("member_external_username", "external"),
        "bot_group": "bot",
        "dev_group": "devs",
        "members_per_page": 100,
        "providers_per_page": 100,
        "hats_per_page": 50,
        "users_in_hats_list": 5,
        "requested_hats_per_page": 100,
        "update_last_visit_interval": 600,  # seconds
    },
    "hats": {
        "moderation": "Staff",
        "validation": "Staff",
        "hats_management": "Staff",
    },
    "gallery": {
        "image_max_size": 1024 * 1024,
        "gallery_per_page": 21,
        "images_per_page": 21,
    },
    "tutorial": {
        "home_number": 4,
    },
    "article": {"home_number": 3},
    "opinions": {
        "home_number": 5,
        "allow_pdf": zds_config.get("opinions_allow_pdf", True),
        "allow_epub": zds_config.get("opinions_allow_epub", True),
        "allow_zip": zds_config.get("opinions_allow_zip", True),
    },
    "content": {
        "repo_private_path": BASE_DIR / "contents-private",
        "repo_public_path": BASE_DIR / "contents-public",
        "extra_contents_dirname": "extra_contents",
        # can also be 'extra_content_generation_policy': 'SYNC'
        # or 'extra_content_generation_policy': 'NOTHING'
        "extra_content_generation_policy": "WATCHDOG",
        "extra_content_watchdog_dir": BASE_DIR / "watchdog-build",
        "max_tree_depth": 3,
        "default_licence_pk": 7,
        "content_per_page": 42,
        "max_last_publications_level_1": 6,
        "max_last_publications_level_2": 12,
        "max_last_publications_level_3": 12,
        "notes_per_page": 25,
        "helps_per_page": 20,
        "commits_per_page": 20,
        "suggestions_per_page": 2,
        "max_suggestion_search_results": 10,
        "mass_edit_goals_content_per_page": 25,
        "view_contents_by_goal_content_per_page": 42,
        "view_contents_by_label_content_per_page": 42,
        "feed_length": 5,
        "user_page_number": 5,
        "default_image": BASE_DIR / "fixtures" / "noir_black.png",
        "import_image_prefix": "archive",
        "maximum_slug_size": 150,
        "characters_per_minute": 1500,
        "editorial_line_link": "https://zestedesavoir.com/articles/3978/la-ligne-editoriale-officielle-de-zeste-de-savoir-2/",
        "epub_stylesheets": {
            "toc": Path("toc.css"),
            "full": BASE_DIR / "dist" / "css" / "zmd.css",
            "katex": BASE_DIR / "dist" / "css" / "katex.min.css",
        },
        "latex_template_repo": "NOT_EXISTING_DIR",
    },
    "forum": {
        "posts_per_page": 21,
        "topics_per_page": 21,
        "spam_limit_seconds": 60 * 15,
        "spam_limit_participant": 2,
        "beta_forum_id": zds_config.get("publications_being_written_forum_id", 1),
        "max_post_length": 1000000,
        "top_tag_max": 5,
        "home_number": 6,
        "old_post_limit_days": 90,
        # Exclude tags from top tags list. Tags listed here should not be relevant for most of users.
        # Be warned exclude too much tags can restrict performance
        "top_tag_exclu": ["bug", "suggestion", "tutoriel", "beta", "article"],
        "greetings": ["salut", "bonjour", "yo ", "hello", "bon matin", "tout le monde se secoue"],
        "description_size": 120,
        "max_similar_topics": 10,
    },
    "topic": {
        "home_number": 5,
    },
    "comment": {
        "max_pings": 15,
    },
    "featured_resource": {
        "featured_per_page": 100,
        "home_number": 5,
        "request_per_page": 50,
    },
    "notification": {
        "per_page": 50,
    },
    "paginator": {"folding_limit": 4},
    "search": {
        "results_per_page": 20,
        "search_groups": {
            "publishedcontent": (_("Contenus publiés"), ["publishedcontent", "chapter"]),
            "topic": (_("Sujets du forum"), ["topic"]),
            "post": (_("Messages du forum"), ["post"]),
        },
        "search_content_type": {
            "tutorial": (_("Tutoriels"), ["tutorial"]),
            "article": (_("Articles"), ["article"]),
            "opinion": (_("Billet"), ["opinion"]),
        },
        "search_validated_content": {
            "validated": (_("Contenus validés"), ["validated"]),
            "no_validated": (_("Contenus libres"), ["no_validated"]),
        },
        "boosts": {
            "publishedcontent": {
                "global": global_weight_publishedcontent,
                "if_validated": global_weight_publishedcontent * 1.5,
                "if_validated_and_multipage": global_weight_publishedcontent * 1.7,
                "if_opinion": global_weight_publishedcontent * 1.3,
                "if_opinion_not_picked": global_weight_publishedcontent * 1.1,
                "title": global_weight_publishedcontent * 4,
                "description": global_weight_publishedcontent * 2,
                "categories": global_weight_publishedcontent * 1,
                "subcategories": global_weight_publishedcontent * 1,
                "tags": global_weight_publishedcontent * 1,
                "text": global_weight_publishedcontent * 2,
            },
            "chapter": {
                "global": global_weight_chapter,
                "title": global_weight_chapter * 3,
                "text": global_weight_chapter * 2,
            },
            "topic": {
                "global": global_weight_topic,
                "if_solved": global_weight_topic * 1.1,
                "if_sticky": global_weight_topic * 1.2,
                "if_locked": global_weight_topic * 0.1,
                "title": global_weight_topic * 3,
                "subtitle": global_weight_topic * 2,
                "tags": global_weight_topic * 1,
            },
            "post": {
                "global": global_weight_post,
                "if_first": global_weight_post * 1.5,
                "if_useful": global_weight_post * 1.2,
                "ld_ratio_above_1": global_weight_post * 1.05,
                "ld_ratio_below_1": global_weight_post * 0.95,
                "text": global_weight_post,
            },
        },
    },
    "visual_changes": [],
    "display_search_bar": True,
    "zmd": {"server": "http://127.0.0.1:27272", "disable_pings": False},
    "very_top_banner": {},
}
