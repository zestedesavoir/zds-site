============
La recherche
============

Principe
========

Comment faire une recherche ?
-----------------------------

La recherche se découpe en deux parties distinctes :

 - L'indexation des données
 - La recherche par l'utilisateur

L'indexation des données
++++++++++++++++++++++++

**L'indexation** des données consiste à **rassembler toutes les données** dans
lesquelles l'utilisateur va **pouvoir rechercher**. Elle est faite au
préalable.  Celle-ci est faite de telle façon qu'on puisse rechercher dans les
éléments suivants :

 - Les contenus (article, tutoriels et billets) ainsi que leurs chapitres (s'il
   s'agit d'un moyen ou *big*-tuto) ;
 - Les sujets ;
 - Les réponses aux sujets.

Cette indexation est réalisée à intervalle régulier (et de manière à n'indexer
que les données qui ont changé).

La recherche
++++++++++++

L'utilisateur peut utiliser la recherche, en utilisant la recherche de
`l'en-tête  <../front-end/structure-du-site.html#l-en-tete>`_, ou par la page
d'accueil, si elle est disponible.

   .. figure:: ../images/design/en-tete.png
      :align: center

Des critères de recherche peuvent être ajoutés sur la page de recherche.  Le
seul critère de recherche disponible actuellement est le type de résultat
(contenu, sujet du forum ou message du forum).

   .. figure:: ../images/search/search-filters.png
      :align: center

Quelques mots sur Typesense
-------------------------------

`Typesense <https://typesense.org/>`_ est un moteur de recherche qui permet
d’indexer et de rechercher des données. Typesense offre une interface de type
REST pour interroger son index, mais nous utilisons plutôt le module Python
dédié.

Phase d'indexation
++++++++++++++++++

Typesense organise les données sous forme de documents, regroupés dans des
collections. On peut avoir différent types de collections (par exemple pour
Zeste de Savoir : *topics*, *posts*, contenus, chapitres, etc).

La phase d'indexation est réalisée à l'aide de la commande ``python manage.py
search_engine_manager`` (voir ci-dessous).

Phase de recherche
++++++++++++++++++

Durant la phase de recherche, les documents sont classés par ``text_match``,
valeur qui représente le score de correspondance avec le texte recherché. Ce
score dépend des champs que l'on souhaite indexer, il est calculé selon
plusieurs métriques :

+ *Fréquence* : elle correspond au nombre de fois qu’un terme apparaît dans un
  document ;
+ *Distance d'édition* : si un terme de la requête n'est pas trouvé dans les
  documents, Typesense recherchera des mots qui diffèrent de la requête d'un
  certain nombre de caractères (``num_typos``) en ajoutant, supprimant ou
  remplaçant des caractères ;
+ *Proximité* : si la requête est constituée de plusieurs termes et que ces
  termes sont proches alors le score sera plus élevé. Par exemple, si la
  requête est "moteur de recherche". Le titre *Typesense est un moteur de
  recherche* aura un meilleur score que le titre *La recherche d'un nouveau
  moteur thermique à pistons rotatifs* ;
+ *Ordre des champs* : si on a indiqué qu'on recherche selon les champs *titre*
  et *description* (dans cet ordre), alors le score sera plus important si le
  terme est trouvé dans le champ *titre* ;
+ *Pondération des champs* : si un document possède un champ *titre* et un
  champ *description*, alors avec des poids supérieur pour le champ *titre*, le
  score sera plus élevé si le terme est trouvé dans le titre.

Les différents poids sont modifiables directement dans les paramètres de Zeste
de Savoir (voir ci-dessous).

Il est possible de rechercher dans plusieurs collections en une seule requête,
avec un mécanisme que Typesense appele le `Federated Multi-Search
<https://typesense.org/docs/0.24.1/api/federated-multi-search.html#multi-search-parameters>`_.

En pratique
===========

Configuration
-------------

La configuration de la connexion se fait dans le fichier
``settings/abstract_base/zds.py``, à l'aide des deux variables suivantes :

.. sourcecode:: python

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
        "connection_timeout_seconds": 2,
    }


La première active le moteur de recherche, la seconde permet de configurer la
connexion au moteur de recherche.

Pour indiquer, les poids associés à chacune des collections, il faut modifier
les variables suivantes dans ``settings/abstract_base/zds.py`` :

.. sourcecode:: python

    global_weight_publishedcontent = 3 # contenus publiés (billets, tutoriaux, articles)
    global_weight_topic = 2 # sujets de forum
    global_weight_chapter = 1.5 # chapitres
    global_weight_post = 1 # messages d'un sujet de forum


Il est possible de modifier les différents paramètres de la recherche dans
``settings/abstract_base/zds.py`` :

.. sourcecode:: python

    "search": {
        "mark_keywords": ["javafx", "haskell", "groovy", "powershell", "latex", "linux", "windows"],
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
                "if_validated": 2.0,  # s'il s'agit d'une publication validée (article ou tuto)
                "if_validated_and_multipage": 2.5, # s'il s'agit d'une publication validée sur plusieurs pages (medium ou big)
                "if_opinion": 1.66, # s'il s'agit d'un billet
                "if_opinion_not_picked": 1.5, # s'il s'agit d'un billet non mis en avant sur la page d'accueil

                # poids des différents champs :
                "title": global_weight_publishedcontent * 3,
                "description": global_weight_publishedcontent * 2,
                "categories": global_weight_publishedcontent * 1,
                "subcategories": global_weight_publishedcontent * 1,
                "tags": global_weight_publishedcontent * 1,
                "text": global_weight_publishedcontent * 2,
            },
            "topic": {
                "global": global_weight_topic,
                "if_solved": 1.1, # s'il s'agit d'un sujet résolu
                "if_sticky": 1.2, # s'il s'agit d'un sujet épinglé
                "if_locked": 0.1, # s'il s'agit d'un sujet fermé

                # poids des différents champs :
                "title": global_weight_topic * 3,
                "subtitle": global_weight_topic * 2,
                "tags": global_weight_topic * 1,
            },
            "chapter": {
                "global": global_weight_chapter,

                # poids des différents champs :
                "title": global_weight_chapter * 3,
                "text": global_weight_chapter * 2,
            },
            "post": {
                "global": global_weight_post,
                "if_first": 1.2, # s'il s'agit d'un message en première position
                "if_useful": 1.5, # s'il s'agit d'un message jugé utile
                "ld_ratio_above_1": 1.05, # si le ratio pouce vert/rouge est supérieur à 1
                "ld_ratio_below_1": 0.95, # si le ratio pouce vert/rouge est inférieur à 1
                "text_html": global_weight_post, # poids du champ
            },
        },


+ ``results_per_page`` est le nombre de résultats affichés,
+ ``search_groups`` définit les différents types de documents indexés et la
  manière dont ils sont groupés sur le formulaire de recherche,
+ ``search_content_type`` définit les différents types de contenus publiés et
  la manière dont ils sont groupés sur le formulaire de recherche,
+ ``search_validated_content``  définit les différentes validations des contenus
  publiés et la manière dont elles sont groupées sur le formulaire de recherche,
+ ``boosts`` contient les différents facteurs de *boost* appliqués aux
  différentes situations. Modifier ces valeurs permet de changer l'ordre des
  résultats retourés lors d'une recherche.


Indexer les données
-------------------

Une fois Typesense `installé <../install/extra-install-search-engine.html>`_, configuré et lancé, la commande suivante est utilisée :

.. sourcecode:: bash

      python manage.py search_engine_manager <action>

où ``<action>`` peut être :

+ ``setup`` : crée et configure le *client* Typesense (y compris la création des
  *collections* avec *schémas*) ;
+ ``clear`` : supprime toutes les *collections* du *client* Typesense et marque
  toutes les données comme "à indexer" ;
+ ``index_flagged`` : indexe les données marquées comme "à indexer" ;
+ ``index_all`` : invoque ``setup`` puis indexe toute les données (qu'elles
  soient marquées comme "à indexer" ou non).


La commande ``index_flagged`` peut donc être lancée de manière régulière afin
d'indexer les nouvelles données ou les données modifiées.

.. note::

      Le caractère "à indexer" est fonction des actions effectuées sur l'objet
      Django (par défaut, à chaque fois que la méthode ``save()`` du modèle est
      appelée, l'objet est marqué comme "à indexer").
      Cette information est stockée dans la base de donnée MySQL.

Aspects techniques
==================

Indexation d'un modèle
----------------------


Afin d'être indexable, un modèle Django doit dériver de
``AbstractSearchIndexableModel`` (qui dérive de ``models.Model`` et de
``AbstractSearchIndexable``). Par exemple :

.. sourcecode:: python

      class Post(Comment, AbstractSearchIndexableModel):
          # ...


.. note::

    Le code est écrit de manière à ce que l'id utilisé par Typesense (champ
    ``id``) corresponde à la *pk* du modèle (via la variable
    ``search_engine_id``). De cette façon, si on en connait la *pk* d'un objet
    Django, il est possible de récupérer l'objet Typesense correspondant à
    l'aide de ``GET /collections/<nom de la collection>/documents/<pk>``.

Différentes méthodes de la classe ``AbstractSearchIndexableModel`` peuvent ou
doivent ensuite être surchargées :

+ ``get_search_document_schema()`` permet de définir le *schéma* d'un document, c'est
  à dire quels champs seront indexés avec quels types. Par exemple :

      .. sourcecode:: python

                @classmethod
                def get_search_document_schema(cls):
                    search_engine_schema = super().get_search_document_schema()

                    search_engine_schema["fields"] = [
                        {"name": "topic_pk", "type": "int64"},
                        {"name": "forum_pk", "type": "int64"},
                        {"name": "topic_title", "type": "string", "facet": True},
                    # ...

      Les schémas Typesense sont des `dictionnaires
      <https://typesense.org/docs/0.23.0/api/collections.html#with-pre-defined-schema>`_.
      On indique également dans les schémas un poids de recherche qui est
      calculé selon différent critères, ce champ correspond au boost que reçoit
      le contenu lors de la phase de recherche.

+ ``get_indexable_objects`` permet de définir quels objets doivent être
  récupérés et indexés. Cette fonction permet également d'utiliser
  ``prefetch_related()`` ou ``select_related()`` pour minimiser le nombre de
  requêtes SQL. Par exemple :

      .. sourcecode:: python

          @classmethod
          def get_indexable_objects(cls, force_reindexing=False):
              q = super(Post, cls).get_indexable_objects(force_reindexing)\
                  .prefetch_related('topic')\
                  .prefetch_related('topic__forum')

      où ``q`` est un *queryset* Django.

+ ``get_document_source()`` permet de gérer des cas où le champ n'est pas
  directement une propriété de la classe, ou si cette propriété ne peut pas
  être indexée directement :

      .. sourcecode:: python

          def get_document_source(self, excluded_fields=None):
              excluded_fields = excluded_fields or []
              excluded_fields.extend(["tags", "forum_pk", "forum_title", "forum_get_absolute_url", "pubdate", "weight"])

              data = super().get_document_source(excluded_fields=excluded_fields)
              data["tags"] = [tag.title for tag in self.tags.all()]
              data["forum_pk"] = self.forum.pk
              data["forum_title"] = self.forum.title
              data["forum_get_absolute_url"] = self.forum.get_absolute_url()
              data["pubdate"] = date_to_timestamp_int(self.pubdate)
              data["text"] = clean_html(self.text_html)
              data["weight"] = self._get_search_weight()

              return data

      Dans cet exemple (issu de la classe ``Post``), on voit que certains
      champs ne peuvent être directement indexés car ils appartiennent au
      *topic* et au *forum* parent. Il sont donc exclus du mécanisme par défaut
      (via la variable ``excluded_fields``) et leur valeur est récupérée et
      définie dans la suite de la méthode.

      Cet exemple permet également de remarquer que le contenu indéxé ne
      contient jamais de balises HTML (c'est le rôle de la fonction
      ``clean_html()``). Il est ainsi possible d'afficher de façon sûre le
      contenu renvoyé par Typesense (utile en particulier pour afficher les
      balises ``<mark>`` pour surligner les termes recherchés).


Finalement, il est important **pour chaque type de document** d'attraper le
signal de pré-suppression en base de données, afin que le document soit
également supprimé du moteur de recherche.

Plus d'informations sur les méthodes qui peuvent être surchargées sont
disponibles `dans la documentation technique
<../back-end-code/search.html>`_.

.. attention::

      À chaque fois que vous modifiez la définition d'un schéma d'une
      collection dans ``get_search_document_schema()``, toutes les données doivent
      être réindexées.

Le cas particulier des contenus
-------------------------------

La plupart des informations des contenus, en particulier les textes, `ne sont
pas stockés dans la base de données
<contents.html#aspects-techniques-et-fonctionnels>`_.

Il a été choisi de n'inclure dans le moteur de recherche que les chapitres de
ces contenus (anciennement, les introductions et conclusions des parties
étaient également incluses). Ce sont les contenus HTML qui sont indexés et non
leur version écrite en Markdown, afin de rester cohérent avec ce qui se fait
pour les *posts*. Les avantages de cette décision sont multiples :

+ Le *parsing* est déjà effectué et n'a pas à être refait durant l'indexation ;
+ Moins de fichiers à lire (pour rappel, les différentes parties d'un contenu
  `sont rassemblées en un seul fichier
  <contents.html#processus-de-publication>`_ à la publication) ;
+ Pas besoin d'utiliser Git durant le processus d'indexation ;


L'indexation des chapitres (représentés par la classe ``FakeChapter``, `voir
ici
<../back-end-code/tutorialv2.html#zds.tutorialv2.models.database.FakeChapter>`_)
est effectuée en même temps que l'indexation des contenus publiés
(``PublishedContent``). En particulier, c'est la méthode ``get_indexable()``
qui est surchargée, profitant du fait que cette méthode peut renvoyer n'importe
quel type de document à indexer.

Le code tient aussi compte du fait que la classe ``PublishedContent`` `gère le
changement de slug <contents.html#le-stockage-en-base-de-donnees>`_ afin de
maintenir le SEO.  Ainsi, la méthode ``save()`` est modifiée de manière à
supprimer toute référence à elle même et aux chapitres correspondants si un
objet correspondant au même contenu mais avec un nouveau slug est créé.
