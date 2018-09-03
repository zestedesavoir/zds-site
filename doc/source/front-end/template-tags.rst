===================================
Elements de templates personnalisés
===================================

Le dossier ``zds/utils/templatetags/`` contient un ensemble de tags et filtres personnalisés pouvant être utilisés dans les gabarits (*templates*),
`voir à ce sujet la documentation de Django <https://docs.djangoproject.com/fr/1.8/howto/custom-template-tags/>`_.

La majorité de ces modules proposent aussi des fonctions proposant les même fonctionnalités depuis le reste du code
Python.

append_query_params
=============

L'élément ``append_query_params`` permet de rajouter des paramètres à la requête ``GET`` courante. Par exemple, sur une page
``module/toto``, le code de template suivant :

.. sourcecode:: html

    {% load append_query_params %}
    <a href="{% append_query_params key1=var1,key2=var2 %}">Mon lien</a>

produira le code suivant :

.. sourcecode:: html

    <a href="module/toto?key1=1&key2=2">Mon lien</a>

si le contenu de ``var1`` est ``1`` et le contenu de ``var2`` est ``2``.

Le module ``captureas``
=======================

Ce module défini l'élément ``captureas``, qui permet de demander d'effectuer le rendu d'un bloc de gabarit et de stocker son contenu dans
une variable. Ainsi le code suivant :

.. sourcecode:: html

    {% load captureas %}
    {% captureas var2 %}
    {% for i in 'xxxxxxxxxx' %}
    {{forloop.counter0}}
    {% endfor %}
    {% endcaptureas %}

ne produit rien en sortie mais affecte le résultat du bloc entre les éléments ``{% captureas var2 %}`` et
``{% endcaptureas %}``, soit ``0123456789``, dans la variable de gabarit ``var2``

Le module ``date``
==================

Plusieurs filtres sont disponibles dans ce module.

``format_date``
---------------

Ce filtre formate une date au format ``DateTime`` destiné à être affiché sur le site :

.. sourcecode:: html

    {% load date %}
    {{ date|format_date }}

``tooltip_date``
----------------

Ce filtre effectue la même chose que ``format_date`` mais à destination des ``tooltip``.

``humane_time``
---------------

Formate une date au format *Nombre de seconde depuis Epoch* en un élément lisible. Ainsi :

.. sourcecode:: html

    {% load date %}
    {{ date_epoch|humane_time }}

sera rendu :

.. sourcecode:: html

    jeudi 01 janvier 1970 à 00h00

Si le contenu de ``date_epoch`` etait de ``42``.

``from_elasticsearch_date``
---------------------------

Par défaut, Elasticsearch stocke ces dates au format ``yyyy-MM-dd'T'HH:mm:ss.SSSZ``
(il s'agit du format ``strict_date_time``, voir à ce sujet `la documentation d'Elasticsearch <https://www.elastic.co/guide/en/elasticsearch/reference/5.1/mapping-date-format.html>`_).
Ce filtre transforme cette date en une date que les autres filtres de ce module peuvent exploiter.

Le module ``email_obfuscator``
==============================

Ces filtres sont principalement fondés sur https://github.com/morninj/django-email-obfuscator.


``obfuscate``
-------------

L'adresse de courriel va être encodée avec des caractères ASCII pour la protéger des robots :


.. sourcecode:: html

    {% load email_obfuscator %}
    {{ 'your@email.com'|obfuscate }}


``obfuscate_mailto``
--------------------

Ce *templatetag* ajoute en plus un ``mailto``. Il prend un paramètre optionnel qui permet d'avoir un texte personnalisé dans
la balise ``<a>`` :

.. sourcecode:: html

    {% load email_obfuscator %}
    {{ 'your@email.com'|obfuscate_mailto:"my custom text" }}

Ce qui donnera :

.. sourcecode:: html

    <a href="&#109;&#97;&#105;&#108;&#116;&#111;&#58;&#121;&#111;&#117;&#114;&#64;&#101;&#109;&#97;&#105;&#108;&#46;&#99;&#111;&#109;">my custom text</a>


``obfuscate_mailto_top_subject``
--------------------------------

Identique sur le fonctionnement à ``obfuscate_mailto``, ce *templatetag* ajoute en plus un sujet (qui remplace le champ
pouvant être inséré entre les balises ``<a>`` et ``</a>``) ainsi que ``target="_top"``.

Il est utilisé sur la page « Contact ».

Exemple :

.. sourcecode:: html

    {% load email_obfuscator %}
    {{ 'association@zestedesavoir.com'|obfuscate_mailto_top_subject:"Contact communication" }}

Ce qui sera rendu de la manière suivante:

.. sourcecode:: html

    <a href="&#109;&#97;&#105;&#108;&#116;&#111;&#58;&#97;&#115;&#115;&#111;&#99;&#105;&#97;&#116;&#105;&#111;&#110;&#64;&#122;&#101;&#115;&#116;&#101;&#100;&#101;&#115;&#97;&#118;&#111;&#105;&#114;&#46;&#99;&#111;&#109;&#63;&#83;&#117;&#98;&#106;&#101;&#99;&#116;&#61;&#67;&#111;&#110;&#116;&#97;&#99;&#116;&#32;&#99;&#111;&#109;&#109;&#117;&#110;&#105;&#99;&#97;&#116;&#105;&#111;&#110;" target="_top">&#97;&#115;&#115;&#111;&#99;&#105;&#97;&#116;&#105;&#111;&#110;&#64;&#122;&#101;&#115;&#116;&#101;&#100;&#101;&#115;&#97;&#118;&#111;&#105;&#114;&#46;&#99;&#111;&#109;</a>

On conviendra du fait que c'est parfaitement illisible ;)

Le module ``emarkdown``
=======================

Ce module défini des filtres utilisés dans la transformation du markdown en HTML ou le traitement du markdown.

Markdown vers HTML
------------------

Il permet de rendre un texte Markdown en HTML. Il y a deux commandes :

- ``emarkdown`` pour une transformation classique ;
- ``emarkdown_inline`` pour une transformation uniquement des éléments *inline* et donc pas de blocs (c'est utilisé pour les
  signatures des membres).


Markdown vers Markdown
----------------------

Ces élements sont utilisés dans le cadre de la transformation du markdown avant d'être traité par ``Pandoc`` lors de la
génération des fichiers PDF et EPUB des tutos :

- ``shift_heading_1`` : Décale les titres de 1 niveau (un titre de niveau 1 devient un titre de niveau 2, etc.)
- ``shift_heading_2`` : Décale les titres de 2 niveaux (un titre de niveau 1 devient un titre de niveau 3, etc.)
- ``shift_heading_3`` : Décale les titres de 3 niveaux (un titre de niveau 1 devient un titre de niveau 4, etc.)

Le module ``htmldiff``
=========================

Ce module définit le tag ``htmldiff`` qui affiche la différence entre deux chaînes de caractères, en utilisant `difflib (en) <https://docs.python.org/2/library/difflib.html>`__. Le code généré est un tableau HTML à l'intérieur d'une div. Il est employé pour afficher le *diff* des tutoriels et des articles.

.. sourcecode:: html

    {% load htmldiff %}
    {% htmldiff "Hello world!" "Hello world!!!" %}
    {% htmldiff "Hello Pierre!" "Hello Peter!" %}

Le module ``interventions``
===========================

Les filtres de ce module sont utilisés pour récupérer et traiter la liste des interventions de l'utilisateur.

``is_read``
-----------

Employé sur un *topic*, renvoit si l'utilisateur courant a lu ou non le topic considéré. Par exemple, le code suivant mettra la classe "unread" si le *topic* n'as pas été lu par l'utilisateur :

.. sourcecode:: html

    {% load interventions %}
    <span class="{% if not topic|is_read %}unread{% endif %}">{{ topic.title}}</span>



``humane_delta``
----------------

Ce filtre renvoit le texte correspondant à une période donnée, si utilisé comme suis :

.. sourcecode:: html

    {% load interventions %}
    {{ period|humane_delta }}

En fonction de la valeur de ``period``, les chaines de caractères suivantes seront renvoyées :

- ``1`` : ``Aujourd'hui`` ;
- ``2`` : ``Hier`` ;
- ``3`` : ``Cette semaine`` ;
- ``4`` : ``Ce mois-ci`` ;
- ``5`` : ``Cette année``.


``followed_topics``
-------------------

Ce filtre renvoit la liste des *topics* suivis par l'utilisateur, sous la forme d'un dictionaire :

.. sourcecode:: html

    {% load interventions %}
    {% with followedtopics=user|followed_topics %}
        {% for period, topics in followedtopics.items %}
        ...
        {% endfor %}
    {% endwith %}

où ``period`` est un nombre au format attendu par ``humane_delta`` (entre 1 et 5, voir plus haut) et ``topics`` la liste des *topics* dont le dernier message est situé dans cette période de temps. Les *topics* sont des objets ``Topic`` (`voir le détail de son implémentation ici <../back-end-code/forum.html#zds.forum.models.Topic>`__).

``interventions_topics``
------------------------

Ce filtre récupère la liste des notifications non lues sur des modèles notifiables excluant les messages privés:

.. sourcecode:: html

    {% load interventions %}
    {% with unread_posts=user|interventions_topics %}
        {% for unread in unread_posts %}
        ...
        {% endfor %}
    {% endwith %}

Dans ce cas, la variable ``unread`` est un dictionnaire contentant 4 champs:

- ``unread.url`` donne l'URL du premier *post* non lu (ayant généré la notification) ;
- ``unread.author`` contient l'auteur de ce *post* ;
- ``unread.pubdate`` donne la date de ce *post* ;
- ``unread.title`` donne le titre du *topic*, article ou tutoriel dont est issus le post.


``interventions_privatetopics``
-------------------------------

Ce filtre récupère la liste des MPs non-lus :

.. sourcecode:: html

    {% load interventions %}
    {% with unread_posts=user|interventions_privatetopics %}
        {% for unread in unread_posts %}
        ...
        {% endfor %}
    {% endwith %}

Dans ce cas, ``topic`` est un objet de type ``PrivateTopic`` (`voir son implémentation ici <../back-end-code/private-message.html#zds.mp.models.PrivateTopic>`__)

``alerts_list``
---------------

Récupère la liste des alertes (si l'utilisateur possède les droits pour le faire) :

.. sourcecode:: html

    {% load interventions %}
    {% with alerts_list=user|alerts_list %}
        {% for alert in alerts_list.alerts %}
        ...
        {% endfor %}
    {% endwith %}

``alert_list`` est un dictionnaire contenant 2 champs:

- ``alerts`` : Les 10 alertes les plus récentes (détail ci-dessous) ;
- ``nb_alerts`` : Le nombre total d'alertes existantes.


``alerts`` énuméré souvent en ``alert`` est aussi un dictionnaire contenant 4 champs:

- ``alert.url`` donne l'URL du *post* ayant généré l'alerte ;
- ``alert.username`` contient le nom de l'auteur de l'alerte ;
- ``alert.pubdate`` donne la date à laquelle l'alerte à été faite ;
- ``alert.topic`` donne le texte d'alerte.

``waiting_count``
-----------------

Récupère le nombre de tutoriels ou d'articles dans la zone de validation n'ayant pas été réservés par un validateur.

.. sourcecode:: html

    {% load interventions %}
    {% with waiting_tutorials_count="TUTORIAL"|waiting_count waiting_articles_count="ARTICLE"|waiting_count %}
        ...
    {% endwith %}

Le filtre doit être appelé sur ``"TUTORIAL"`` pour récupérer le nombre de tutoriels en attente et sur ``"ARTICLE"`` pour le nombre d'articles.

``humane_delta``
----------------

Permet d'afficher une période en lettres. Fait le lien entre le label d'un jour et sa clé.

.. sourcecode:: html

    {% load interventions %}
    {% for period, topics in followedtopics.items %}
       <h4>{{ period|humane_delta }}</h4>
    {% endfor %}

Le module ``profiles``
======================

``user``
--------

Pour un objet de type ``Profile`` (`voir son implémentation <../back-end-code/member.html#zds.member.models.Profile>`__), ce filtre récupère son objet ``User`` correspondant (`voir les informations sur cet objet dans la documentation de Django <https://docs.djangoproject.com/fr/1.8/topics/auth/default/#user-objects>`__).

Par exemple, le code suivant affichera le nom de l'utilisateur :

.. sourcecode:: html

    {% load profiles %}
    {% with user=profile|user %}
        Je suis {{ user.username }}
    {% endwith %}

``profile``
-----------

Fait l'opération inverse du filtre ``user`` : récupère un objet ``Profile`` à partir d'un objet ``User``.

Par exemple, le code suivant affichera un lien vers le profil de l'utilisateur :

.. sourcecode:: html

    {% load profiles %}
    {% with profile=user|profile %}
        <a href="{{ profile.get_absolute_url }}">{{ user.username }}</a>
    {% endwith %}


``state``
---------

À partir d'un objet ``User``, ce filtre récupère "l'état" de l'utilisateur. Par exemple, il peut être employé comme décris ci-dessous:

.. sourcecode:: html

    {% load profiles %}
    {% with user_state=user|state %}
    ...
    {% endwith %}


où ``user_state`` peut alors valoir une des 4 chaines de caractères suivantes, indiquant un état particulier, **ou rien** :

- ``STAFF`` : l'utilisateur est membre du staff ;
- ``LS`` : l'utilisateur est en mode lecture seule ;
- ``DOWN`` : l'utilisateur n'a pas encore validé son compte ;
- ``BAN`` : l'utilisateur est bani.

Ce *templatetag* est employé pour l'affichage des badges. Vous trouverez plus d'informations `dans la documentation des membres <../back-end/member.html>`__ concernant les différents états dans lesquels peut se trouver un utilisateur et ce qu'ils signifient.

Le module ``roman``
===================

Défini le filtre ``roman``, qui transforme un nombre entier en chiffre romain, utilisé pour l'affichage du sommaire des tutoriels. Par exemple, le code suivant :

.. sourcecode:: html

    {% load roman %}
    {{ 453|roman }}

affichera ``CDLIII``, qui est bien la façon d'écrire 453 en chiffres romain.

Le module ``set``
=================

Ce module défini l'élément ``set``, permetant de définir de nouvelles variables, il est donc complémentaire au module ``captureas``.

Le code suivant permet de définir la variable ``var`` comme valant ``True`` :

.. sourcecode:: html

    {% load set %}
    {% set True as var %}

Bien entendu, il est possible d'assigner à une variable la valeur d'une autre. Soit la variable ``var``, définie de la manière suivante dans le code Python :

.. sourcecode:: python

    var = {'value': u'test'}
    # passage de la variable à l'affichage du gabarit
    # ...

Si on écrit le code suivant dans le gabarit :

.. sourcecode:: html

    {% load set %}
    {% set var.value as value %}
    {{ value }}

alors celle-ci affichera bien ``test``.

.. attention::

    Il n'est actuellement pas possible d'employer des filtres à l'intérieur de cet élément.


Le module ``topbar``
====================

Ce module est utilisé pour récupéré les catégories dans le but de les afficher dans `le menu <structure-du-site.html#le-menu>`__ et dans la liste des tutoriels et articles.

``topbar_forum_categories``
------------------

Ce filtre récupère les forums, classés par catégorie.

.. sourcecode:: html

    {% with top=user|topbar_forum_categories %}
        {% for title, forums in top.categories.items %}
        ...
        {% endfor %}
        {% for tag in top.tags %}
        ...
        {% endfor %}
    {% endwith %}

où,

- ``top.categories`` est un dictionaire contenant le nom de la catégorie (ici ``title``) et la liste des forums situés dans cette catégorie (ici ``forums``), c'est-à-dire une liste d'objets de type ``Forum`` (`voir le détail de l'implémentation de cet objet ici <../back-end-code/forum.html#zds.forum.models.Forum>`__).
- ``top.tags`` contient une liste des 5 *tags* les plus utilisés, qui sont des objets de type ``Tag`` (`voir le détail de l'implémentation de cet objet ici <../back-end-code/utils.html#zds.utils.models.Tag>`__). Certains tags peuvent être exclus de cette liste. Pour exclure un tag, vous devez l'ajouter dans la configuration (top_tag_exclu dans le settings.py).


``topbar_publication_categories``
--------------------------

Ce filtres renvoit une liste des catégories utilisées dans les articles/tutoriels publiés.

Par exemple, pour les tutoriels, on retrouvera le code suivant:

.. sourcecode:: html

    {% with categories="TUTORIAL"|topbar_publication_categories %}
        {% for title, subcats in categories.items %}
            ...
        {% endfor %}
    {% endwith %}

où ``categories`` est un dictionnaire contenant le nom de la catégorie (ici ``title``) et une liste des sous-catégories correspondantes (ici ``subcats``), c'est-à-dire un *tuple* de la forme ``titre, slug``

Le module ``feminize``
======================

Permet de générer les déterminants et pronoms adéquats en fonction du mot suivant dynamiquement généré. Typiquement
ce templatetag est utile dans le cas de la hiérarchie des tutoriels où vous pouvez avoir *"une partie"* ou *"un chapitre"*.

Ce templatetag est basé sur deux dictionnaires de mots : le premier qui associe le déterminant masculin à son homologue
féminin est le second qui associe un mot à un booléen qui indique s'il est féminin ``True`` ou masculin ``False``.

Exemple :

.. sourcecode:: html


    {% load feminize %}
    {{ "le"|feminize:"partie" }} partie <!-- affiche "la partie" si vous êtes en langue française -->

.. attention::

    le templatetag ``feminize`` est internationalisé. Il est également **sensible à la casse**.

Le module ``times``
===================

Permet de générer une liste de nombre pour itérer dessus, utile dans les boucles.

Exemple :

.. sourcecode:: html

    {% load times %}
    {% for i in 25|times %}
        je suis dans l'itération {{ i }}
    {% endfor %}

Le module ``target_tree``
=========================

Ce module défini un *templatetag* utilisé dans le module de tutoriel (v2) dans le but de générer la hiérarchie des tutos et l'arbre
des déplacements possibles d'un élément. Il s'agit d'un wrapper autour de ``zds.tutorialv2.utils.get_target_tagged_tree``.

Exemple :

.. sourcecode:: html

    {% load target_tree %}
    {% for element in child|target_tree %}
            <option value="before:{{element.0}}"
            {% if not element.3 %} disabled {% endif %}>
                 &mdash;&mdash;{% for _ in element.2|times %}&mdash;{% endfor %}{{ element.1 }}
            </option>
    {% endfor %}

Le module ``url_category``
==========================

Ce module défini un *templatetag* permetant d'accéder à l'url des listes de tutoriels et articles filtrés par tag. Il est employé pour l'affichage des *tags* des tutoriels et articles.

Exemple :

.. sourcecode:: html

    {% if content.subcategory.all|length > 0 %}
        <ul class="taglist" itemprop="keywords">
            {% for catofsubcat in content.subcategory.all %}
                <li><a href="{{ catofsubcat|category_url:content }}">{{ catofsubcat.title }}</a></li>
            {% endfor %}
        </ul>
    {% endif %}

Le module ``displayable_authors``
=================================

Ce module permet d'avoir un "versionnage graphique" des auteurs. En effet lorsqu'un tutoriel est publié il se peut que les auteurs ayant participé à sa publication ne soient plus les mêmes dans le futur.
Par exemple, l'auteur principal du tuto peut avoir demandé de l'aide pour écrire la suite du tuto. Il serait injuste de mettre cette seconde personne en tant qu'auteur de la version publiée puisqu'elle n'a pas participé à sa rédaction.

Exemple :

.. sourcecode:: html

    {% load displayable_authors %}
    {% for authors in content|displayable_authors:True %}
       <!-- here display all author for public version -->
    {% endfor %}
    {% for authors in content|displayable_authors:False %}
       <!-- here display all author for draft version -->
    {% endfor %}

Le module ``elasticsearch``
===========================

``highlight``

Permet de mettre en surbrillance les résultats d'une recherche.

Exemple :

.. sourcecode:: html

    {% if search_result.text %}
        {% highlight search_result "text" %}
    {% endif %}

Le module ``joinby``
===========================

Ce module permet de lister le contenu d'un itérable en une seule ligne. C'est un équivalent un peu plus flexible de la fonction ``str.join`` en Python. Le séparateur peut être modifié et une option permet d'utiliser le même séparateur pour le dernier élément. Par défaut, le mot "et" est utilisé pour précéder le dernier élément.

Exemple :

.. sourcecode:: html

    {% joinby fruits %}
    {% joinby fruits ';' final_separator=';' %}

.. sourcecode:: text

    Clémentine, Orange et Citron
    Clémentine;Orange;Citron
