MODEL_TOPIC='sujets'
MODEL_POST='messages'
MODEL_ARTICLE='article'
MODEL_TUTORIAL='tutorial'
MODEL_OPINION='opinion'
MODEL_PART='parts'
MODEL_CHAPTER='chapters'
MODEL_EXTRACT='extracts'


MODEL_NAMES=[
    (MODEL_TOPIC, 'Sujets du forum'),
    (MODEL_POST, 'Messages du forum'),
    (MODEL_ARTICLE, 'Articles'),
    (MODEL_TUTORIAL, 'Tutoriels'),
    (MODEL_OPINION, 'Billets'),
    (MODEL_PART, 'Parties des tutoriels'),
    (MODEL_CHAPTER, 'Chapitres des tutoriels'),
    (MODEL_EXTRACT, 'Sections des tutoriels')
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
