============
La recherche
============

Principe
========

Comment faire une recherche ?
-----------------------------

La recherche se découpe en deux parties distinctes :

 - L'indexation des données
 - La recherche par l'utilisateur

L'indexation des données
++++++++++++++++++++++++

**L'indexation** des données consiste à **rassembler toutes les données** dans lesquelles l'utilisateur va **pouvoir rechercher**. Elle est faite au préalable.
Celle-ci est faite de telle façon qu'on puisse rechercher dans les éléments suivants :

 - Les contenus (article et tutoriels) ainsi que leurs chapitres (s'il s'agit d'un moyen ou *big*-tuto);
 - Les sujets ;
 - Les réponses aux sujets.

Cette indexation est réalisée à intervalle régulier (et de manière à n'indexer que les données qui ont changées).

La recherche
++++++++++++

L'utilisateur peut utiliser la recherche, en utilisant la recherche de `l'en-tête  <../front-end/structure-du-site.html#l-en-tete>`_, ou par la page d'accueil, si elle est disponible.

   .. figure:: ../images/design/en-tete.png
      :align: center

Des critères de recherche peuvent être ajoutés sur la page de recherche.
Le seul critère de recherche disponible actuellement est le type de résultat (contenu, sujet du forum ou message du forum).

   .. figure:: ../images/search/search-filters.png
      :align: center

Quelques mots sur Elasticsearch
-------------------------------

`Elasticsearch <https://www.elastic.co/>`_ (ES) est un serveur utilisant `Lucene <https://lucene.apache.org/>`_ (bibliothèque d'indexation et de recherche de texte) et permet d'indexer et de rechercher des données.
Il est possible de l'interroger à travers une interface de type REST à laquelle on communique via des requêtes écrites en JSON.
Ce projet propose également des API `bas <https://github.com/elastic/elasticsearch-py>`_ et `plus haut <https://github.com/elastic/elasticsearch-dsl-py>`_ niveau en python pour interagir avec le serveur, maintenues par l'équipe d'Elasticsearch.

Précédemment, ZdS utilisait `Haystack <https://django-haystack.readthedocs.io/>`_ pour communiquer avec `Solr <http://lucene.apache.org/solr/>`_ (équivalent à Elasticsearch) mais ces solutions ont été abandonnées par manque d'activité sur le dépôt de Haystack.

Phase d'indexation
++++++++++++++++++

ES classe ses données sous forme de documents, rassemblés dans un *index*. On peut avoir différent types de documents (*topics*, *posts*, contenus, chapitres dans ce cas-ci).

Lorsque les documents sont indexés, ils sont analysés afin d'en extraire les termes importants et de les simplifier (par défaut, "table" et "tables" ne sont pas le même mot, mais il est possible de faire en sorte que si).
Ce processus est effectué par l'*analyzer*, découpé en trois étapes:

.. sourcecode:: none

    Entrée > character filter > tokenizer > token filter > sortie

On retrouve:

+ *character filter*: tâche de nettoyage basique, telle qu'enlever les tags HTML. Il y en a `trois <https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-charfilters.html>`_ qui sont disponibles par défaut ;
+ *tokenizer*: découpe le texte en différents *tokens*. `Énormément <https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-tokenizers.html>`_ de *tokenizer* sont disponibles.
+ *token filter*: altère la liste de *tokens* obtenue pour les "normaliser" en modifiant, supprimant ou rajoutant des *tokens*. Typiquement: enlever certains mots (par exemple les *stopwords* "le", "la", "les" et autres en français), convertir le tout en minuscule, et ainsi de suite. Il en existe également `une pléthore <https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-tokenfilters.html>`_.

Ces différents filtres permettent d'éliminer le superflu afin de se concentrer sur l'essentiel : les *tokens* obtenus.
Par la suite, ES construit une table (un *index inversé*) reliant ces *tokens* aux documents qui les contiennent, qu'il utilise pour la recherche.

Sans entrer dans les détails, l'*analyzer* utilisé par ES pour ZdS :

+ Enlève les tags HTML (en pratique, l'indexation du texte se fait systématiquement sur le contenu converti en HTML et non sur le texte en *markdown*) ;
+ N'utilise par le *tokenizer* par défaut (découper en *token* après tout caractère non alpha-numérique, en gros) afin de conserver "c++" intact, par exemple ;
+ Utilise une série de *token filter*s orientés pour comprendre le français, parmi lesquels un *stopper* (pour enlever les prépositions, déterminants, ...) et un *stemmer* (qui se charge, à partir d'un mot, d'en extraire la racine. Par exemple "programmation", "programmer" ou "programmes" seront tout les trois interprétés et indexés de la même manière car ils partagent la même racine).

Les différents *tokens* qui resortent de cette phase d'analyse sont alors indexés, et c'est de ces *tokens* dont ES se servira ensuite pour la recherche, plutôt que de réaliser des recherches *full-text*.

La phase d'indexation est réalisée à l'aide de la commande ``python manage.py es_manager`` (voir ci-dessous).

Phase de recherche
++++++++++++++++++

Durant la phase de recherche, les documents sont classés par **score**, valeur que ES calcule comme étant le produit ``TF * IDF``, où la partie TF (*term frequencies*) est le nombre de fois qu'un terme apparait dans un document et IDF (*inverse document frequencies*) est la fréquence à laquelle ce terme apparait dans l'ensemble des documents indexés.

C'est en fonction de ce score que seront ensuite classés les résultats, du plus important au plus faible.
Il est possible de manipuler ce score afin d'obtenir les résultats les plus pertinents possible :

+ *Booster* le champ (à priori) : si le terme recherché est contenu dans un champ donné (par exemple le titre, ou une note de bas de page), le score est multiplié par le facteur de *boost* du champ.
+ *Booster* le score (à postériori): si le document obtenu possède d'autres propriétés (par exemple, *booster* le score si le *post* trouvé à "aidé l'auteur du sujet").
+ *Booster* un type de document par rapport à un autre : cas particulier du précédent.

Ces facteurs de *boost* sont modifiables soit directement dans le code de ZdS pour ce qui concerne les facteurs de *boost* sur les champs (voir ci-dessous), soit dans le ``settings.py`` en ce qui concerne les *boosts* à postériori (voir ci-dessous).


En pratique
===========

Configuration
-------------

La configuration de la connexion et de l'*index* se fait dans le ``settings.py``, à l'aide des trois variables suivantes :

.. sourcecode:: python

      ES_ENABLED = True

      ES_CONNECTIONS = {
          'default': {
              'hosts': ['localhost:9200'],
          }
      }

      ES_SEARCH_INDEX = {
          'name': 'zds_search',
          'shards': 5,
          'replicas': 0,
      }


La première active Elasticsearch pour ZdS.
La seconde permet de configurer la connexion à Elasticsearch. ``default`` est l'*alias* de la connexion, au cas où il serait nécessaire d'utiliser plusieurs *clusters*.
La troisième est la configuration de l'*index* avec son nom, son nombre de *shards* et de *replicas*.

Pour modifier les différents paramètres d'une recherche, c'est cette fois dans la variable ``ZDS_APP`` que ça se passe:

.. sourcecode:: python

      'search': {
        'mark_keywords': ['javafx', 'haskell', 'groovy', 'powershell', 'latex', 'linux', 'windows'],
        'results_per_page': 20,
        'search_groups': {
            'content': (
                _(u'Contenus publiés'), ['publishedcontent', 'chapter']
            ),
            'topic': (
                _(u'Sujets du forum'), ['topic']
            ),
            'post': (
                _(u'Messages du forum'), ['post']
            ),
        },
        'boosts': {
            'publishedcontent': {
                'global': 3.0,
                'if_article': 1.0,  # s'il s'agit d'un article
                'if_tutorial': 1.0,  # … d'un tuto
            },
            'topic': {
                'global': 2.0,
                'if_solved': 1.1,  # si le sujet est résolu
                'if_sticky': 1.2,  # si le sujet est en post-it
                'if_locked': 0.1,  # si le sujet est fermé
            },
            'chapter': {
                'global': 1.5,
            },
            'post': {
                'global': 1.0,
                'if_first': 1.2,  # si le post est le premier du topic
                'if_useful': 1.5,  # si le post a été marqué comme étant utile
                'ld_ratio_above_1': 1.05,  # si le ratio pouce vert/rouge est supérieur à 1
                'ld_ratio_below_1': 0.95,  # ... inférieur à 1.
            }
        }
    }

où ``'mark_keywords'`` liste les mots qui ne doivent pas être découpés par le *stemmer* (souvent des noms propres),
``'results_per_page'`` est le nombre de résultats affichés,
``'search_groups'`` définit les différents types de documents indexé et la manière dont il sont groupés quand recherchés (sur le formulaire de recherche),
et ``'boosts'`` les différents facteurs de *boost* appliqués aux différentes situations.

Puisque la phase de *stemming* advient à la fin de l'analyse, tous les mots listés dans ``'mark_keywords'``  doivent être en minuscule et sans éventuels déterminants.

Dans ``'boosts'``, on peut ensuite modifier le comportement de la recherche en choisissant différents facteurs de *boost*.
Chacune des valeurs multiplie le score (donc l'agrandit si elle est supérieure à 1 et le diminue si elle est inférieure à 1).
Un *boost global* (dans chacune des variables ``'global'``) est tout d'abord présent et permet de mettre en avant un type de document par rapport à un autre.
Ensuite, différentes situations peuvent modifier le score.

.. note::

      Ces valeurs sont données à titre indicatif et doivent être adaptées à la situation.

.. attention::

    Pour que les changements dans ``'mark_keywords'`` soient pris en compte, il est nécessaire de réindexer **tout** le contenu
    (grâce à ``python manage.py es_manager index_all``).

Indexer les données de ZdS
--------------------------

Une fois Elasticsearch `installé <../install/install-es.html>`_ puis configuré et lancé, la commande suivante est utilisée :

.. sourcecode:: bash

      python manage.py es_manager <action>

où ``<action>`` peut être

+ ``setup`` : crée et configure l'*index* (y compris le *mapping* et l'*analyzer*) dans le *cluster* d'ES ;
+ ``clear`` : supprime l'*index* du *cluster* d'ES et marque toutes les données comme "à indexer" ;
+ ``index_flagged`` : indexe les données marquées comme "à indexer" ;
+ ``index_all`` : invoque ``setup`` puis indexe toute les données (qu'elles soient marquées comme "à indexer" ou non).


La commande ``index_flagged`` peut donc être lancée de manière régulière (via un *cron* ou un timer *systemd*) afin d'indexer les nouvelles données ou les données modifiées de manière régulière.

.. note::

      Le caractère "à indexer" est fonction des actions effectuées sur l'objet Django (par défaut, à chaque fois que la méthode ``save()`` du modèle est appelée, l'objet est marqué comme "à indexer").
      Cette information est stockée dans la base de donnée MySQL.

Aspects techniques
==================

Indexation d'un modèle
----------------------


Afin d'être indexable, un modèle Django doit dériver de ``AbstractESDjangoIndexable`` (qui dérive de ``models.Model`` et de ``AbstractESIndexable``). Par exemple,

.. sourcecode:: python

      class Post(Comment, AbstractESDjangoIndexable):
          # ...


.. note::

    Le code est écrit de telle manière à ce que l'id utilisé par ES (champ ``_id``) corresponde à la *pk* du modèle (via la variable ``es_id``).
    Il est donc facile de récupérer un objet dans ES si on en connait la *pk*, à l'aide de ``GET /<nom de l'index>/<type de document>/<pk>``.

Différentes méthodes d'``AbstractESDjangoIndexable`` peuvent ou doivent ensuite être surchargées. Parmi ces dernières,

+ ``get_es_mapping()`` permet de définir le *mapping* d'un document, c'est à dire quels champs seront indexés avec quels types. Par exemple,

      .. sourcecode:: python

                @classmethod
                def get_es_mapping(cls):
                    es_mapping = super(Post, cls).get_es_mapping()

                    es_mapping.field('text_html', Text())
                    es_mapping.field('is_useful', Boolean())
                    es_mapping.field('position', Integer())
                    # ...

      ``Mapping`` est un type de donnée défini par ``elasticsearch_dsl`` (voir à ce sujet `la documentation <https://elasticsearch-dsl.readthedocs.io/en/latest/persistence.html#mappings>`_). Si le champ a le même nom qu'une propriété de votre classe, sa valeur sera automatiquement récupérée et indexée. À noter que vous pouvez également marquer une variable comme "à ne pas analyser" avec la variable ``index`` (par exemple, ``Text(index='not_analyzed')``) si vous voulez simplement stocker cette valeur mais ne pas l'utiliser pour effectuer une recherche dessus. On peut également indiquer la valeur du facteur de *boost* avec ``boost`` (par exemple, ``Text(boost=2.0)``).

      .. note::

            Elasticsearch requiert que deux champs portant le même nom dans le même *index* (même si ils sont issus de types de document différents) aient le même *mapping*.
            Ainsi, tous les champs ``title`` doivent être de type ``Text(boost=1.5)`` et ``tags`` de type ``Keyword(boost=2.0)``.

+ ``get_es_django_indexable()`` permet de définir quels objets doivent être récupérés et indexés. Cette fonction permet également d'utiliser ``prefetch_related()`` ou ``select_related()`` pour éviter les requêtes inutiles. Par exemple,

      .. sourcecode:: python

          @classmethod
          def get_es_django_indexable(cls, force_reindexing=False):
              q = super(Post, cls).get_es_django_indexable(force_reindexing)\
                  .prefetch_related('topic')\
                  .prefetch_related('topic__forum')

      où ``q`` est un *queryset* Django.

+ ``get_es_document_source()`` permet de gérer des cas où le champ n'est pas directement une propriété de la classe, ou si cette propriété ne peut pas être indexée directement :

      .. sourcecode:: python

                    def get_es_document_source(self, excluded_fields=None):
                          excluded_fields = excluded_fields or []
                          excluded_fields.extend(
                              ['topic_title', 'forum_title', 'forum_pk', 'forum_get_absolute_url'])

                          data = super(Post, self).get_es_document_source(excluded_fields=excluded_fields)

                          data['topic_title'] = self.topic.title
                          data['forum_pk'] = self.topic.forum.pk
                          data['forum_title'] = self.topic.forum.title
                          data['forum_get_absolute_url'] = self.topic.forum.get_absolute_url()

                          return data

      Dans cet exemple (issu de la classe ``Post``), on voit que certains champs ne peuvent être directement indexés car ils appartiennent au *topic* et au *forum* parent. Il sont donc exclus du mécanisme par défaut (via la variable ``excluded_fields``), leur valeur est récupérée et définie par après.


Finalement, il est important **pour chaque type de document** d'attraper le signal de pré-suppression avec la fonction ``delete_document_in_elasticsearch()``, afin qu'un document supprimé par Django soit également supprimé de Elasticsearch.
Cela s'effectue comme suit (par exemple pour la classe ``Post``):

.. sourcecode:: python

      @receiver(pre_delete, sender=Post)
      def delete_post_in_elasticsearch(sender, instance, **kwargs):
          return delete_document_in_elasticsearch(instance)

Plus d'informations sur les méthodes qui peuvent être surchargées sont disponibles `dans la documentation technique <../back-end-code/searchv2.html>`_.

.. attention::

      À chaque fois que vous modifiez le *mapping* d'un document dans ``get_es_mapping()``, tout l'*index* **doit** être reconstruit **et** indexé.
      N'oubliez donc pas de mentionner cette action à lancer manuellement dans le *update.md*.

Le cas particulier des contenus
-------------------------------

La plupart des informations des contenus, en particulier les textes, `ne sont pas indexés dans la base de donnée <contents.html#aspects-techniques-et-fonctionnels>`_.

Il a été choisi de n'inclure dans Elasticsearch que les chapitres de ces contenus (anciennement, les introductions et conclusions des parties étaient également incluses).
Ce sont les contenus HTML qui sont indexés et non leur version écrite en *markdown*, afin de rester cohérent avec ce qui se fait pour les *posts*.
Les avantages de cette décision sont multiples :

+ Le *parsing* est déjà effectué et n'a pas à être refait durant l'indexation ;
+ Moins de fichiers à lire (pour rappel, les différentes parties d'un contenu `sont rassemblées en un seul fichier <contents.html#processus-de-publication>`_ à la publication) ;
+ Pas besoin d'utiliser Git durant le processus d'indexation ;


L'indexation des chapitres (représentés par la classe ``FakeChapter``, `voir ici <../back-end-code/tutorialv2.html#zds.tutorialv2.models.database.FakeChapter>`_) est effectuée en même temps que l'indexation des contenus publiés (``PublishedContent``).
En particulier, c'est la méthode ``get_es_indexable()`` qui est surchargée, profitant du fait que cette méthode peut renvoyer n'importe quel type de document à indexer.

.. sourcecode:: python

    @classmethod
    def get_es_indexable(cls, force_reindexing=False):
        """Overridden to also include
        """

        index_manager = ESIndexManager(**settings.ES_SEARCH_INDEX)
        last_pk = 0
        objects_source = super(PublishedContent, cls).get_es_indexable(force_reindexing)
        objects = list(objects_source.filter(pk__gt=last_pk)[:PublishedContent.objects_per_batch])
        while objects:
            chapters = []

            for content in objects:
                versioned = content.load_public_version()

                if versioned.has_sub_containers():  # chapters are only indexed for middle and big tuto

                    # delete possible previous chapters
                    if content.es_already_indexed:
                        index_manager.delete_by_query(
                            FakeChapter.get_es_document_type(), ES_Q('match', _routing=content.es_id))

                    # (re)index the new one(s)
                    for chapter in versioned.get_list_of_chapters():
                        chapters.append(FakeChapter(chapter, versioned, content.es_id))
            last_pk = objects[-1].pk
            objects = list(objects_source.filter(pk__gt=last_pk)[:PublishedContent.objects_per_batch])
            yield chapters
            yield objects



Le code tient aussi compte du fait que la classe ``PublishedContent`` `gère le changement de slug <contents.html#le-stockage-en-base-de-donnees>`_ afin de maintenir le SEO.
Ainsi, la méthode ``save()`` est modifiée de manière à supprimer toute référence à elle même et aux chapitres correspondants si un objet correspondant au même contenu mais avec un nouveau slug est créé.

.. note::

    Dans ES, une relation de type parent-enfant (`cf. documentation <https://www.elastic.co/guide/en/elasticsearch/guide/2.x/parent-child.html>`_) est définie entre les contenus et les chapitres correspondants.
    Cette relation est utilisée pour la suppression, mais il est possible de l'exploiter à d'autres fins.
