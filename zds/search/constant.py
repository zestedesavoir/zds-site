

MODEL_NAMES = [('sujets', 'Sujets du forum'),
               ('messages', 'Messages du forum'),
               ('article', 'Articles'),
               ('tutorial', 'Tutoriels'),
               ('opinion', 'Billets'),
               ('parts', 'Parties des tutoriels'),
               ('chapters', 'Chapitres des tutoriels'),
               ('extracts', 'Sections des tutoriels')]


def model_topic():
    return MODEL_NAMES[0][0]


def model_post():
    return MODEL_NAMES[1][0]


def model_article():
    return MODEL_NAMES[2][0]


def model_tutorial():
    return MODEL_NAMES[3][0]


def model_opinion():
    return MODEL_NAMES[4][0]


def model_part():
    return MODEL_NAMES[5][0]


def model_chapter():
    return MODEL_NAMES[6][0]


def model_extract():
    return MODEL_NAMES[7][0]
