from django.utils.translation import ugettext_lazy as _

MODEL_TOPIC = 'sujets'
MODEL_POST = 'messages'
MODEL_ARTICLE = 'article'
MODEL_TUTORIAL = 'tutorial'
MODEL_OPINION = 'opinion'
MODEL_PART = 'parts'
MODEL_CHAPTER = 'chapters'
MODEL_EXTRACT = 'extracts'

MODEL_NAMES = [
    (MODEL_TOPIC, _('Sujets du forum')),
    (MODEL_POST, _('Messages du forum')),
    (MODEL_ARTICLE, _('Articles')),
    (MODEL_TUTORIAL, _('Tutoriels')),
    (MODEL_OPINION, _('Billets')),
    (MODEL_PART, _('Parties des tutoriels')),
    (MODEL_CHAPTER, _('Chapitres des tutoriels')),
    (MODEL_EXTRACT, _('Sections des tutoriels'))
]


def model_topic():
    return MODEL_TOPIC


def model_post():
    return MODEL_POST


def model_article():
    return MODEL_ARTICLE


def model_tutorial():
    return MODEL_TUTORIAL


def model_opinion():
    return MODEL_OPINION


def model_part():
    return MODEL_PART


def model_chapter():
    return MODEL_CHAPTER


def model_extract():
    return MODEL_EXTRACT
