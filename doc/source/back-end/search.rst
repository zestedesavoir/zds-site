============
La recherche
============

La recherche se découpe en deux parties distinctes :
 - L'indexation des données
 - La recherche par l'utilisateur

L'indexation des données
========================

**L'indexation** des données consiste à **rassembler toutes les données** sur lesquelles l'utilisateur va **pouvoir rechercher**. Elle est faite au préalable.
L'indexation est faite de telle façon qu'on puisse rechercher sur les éléments suivants :

 - Les tutoriels (les parties, les chapitres, les extraits)
 - Les articles (titre, description, date de publication, contenu en markdown)
 - Les sujets (titre, sous-titre, auteurs, le contenu en markdown, le nom du forum)
 - Les réponses au sujets (auteur et contenu en markdown)

L'indexation est réalisée à la demande, même si un jour, elle pourrait être en `temps réel <https://zestedesavoir.com/forums/sujet/3334/indexation-en-temps-reel/>`_.

Aujourd'hui, l'indexation est réalisée toutes les trentaines de minutes, sur le serveur de production. Tout le contenu est ré-indexé à chaque fois, ce qui prend 100 pourcents du processus toutes les 5 minutes.
Des solutions sont présentes dans `la documentation d'Haystack (en) <http://django-haystack.readthedocs.org/en/latest/searchindex_api.html#get-updated-field>`_, sans qu'on puisse réellement `les appliquer <https://github.com/zestedesavoir/zds-site/pull/2771>`_.

La recherche
============

L'utilisateur peut utiliser la recherche, en utilisant la recherche de `l'en-tête  <../front-end/structure-du-site.html#l-en-tete>`_.

   .. figure:: ../images/design/en-tete.png
      :align: center

Des critères de recherche, peuvent être ajoutés sur la page de recherche. Plus tard, on pourrait ajouter des facets, plus d'information sur `la ZEP correspondante <https://zestedesavoir.com/forums/sujet/1082/zep-15-navigation-a-facettes-a-travers-le-site/>`_.
Les critères de recherches sont uniquement sur le type de contenu (tutoriel, article, sujet, réponse).

Dans le code ?
==============

On utilise pour **l'indexation** une **bibliothèque** Python nommée **Haystack** et le **moteur de recherche Solr**.

    .. figure:: ../images/search/schema-recherche-lib.png
       :align: center

Pour l'indexation, on indique à Haystack quels contenus on doit indexer. Haystack appelle une bibliothèque Python nommée PySolr.
PySolr n'est jamais utilisé directement dans le code, on doit toujours passer par la bibliothèque Haystack. PySolr effectue des appels à une API REST exposée par le moteur de recherche Solr.

Pour la recherche, c'est le même principe : bibliothèque Haystack -> bibliothèque PySolr -> l'API REST de Solr.

Pourquoi avoir utilisé Haystack, ne peut t-on pas appeller Solr directement ?
-----------------------------------------------------------------------------

On pourrait directement appeler Solr mais Haystack nous propose plusieurs avantages :
 - Nous permet d'être indépendant, du moteur de recherche utilisé, aujourd'hui, on utilise Solr mais demain, on pourrait assez facilement le remplacer par un autre moteur de recherche tel que `Xapian (en) <http://xapian.org/>`_, `Elasticsearch (en) <https://www.elastic.co/>`_ ou `Whoosh (en) <http://whoosh.ca/>`_
 - Assez facile à utiliser
 - Nous permet d'avoir relativement facilement, les facets, la recherche spatiale, suggestions des mots clés, autocomplétion…
 - Nous permet de générer les fichiers de configuration plus facilement.
 - Libre (BSD) et gratuit.

Pourquoi Solr et pas un autre moteur de recherche ?
---------------------------------------------------

Les principaux avantages sont :
 - Une interface web complète
 - Libre et Gratuit
 - Multiplateforme
 - Simple à utiliser

Comment fonctionne le code de l'indexation ?
--------------------------------------------

Tout d'abord, avant d'attaquer le code, il faut bien faire la différence entre :

 - **Le contenu "indexé"**, c'est-à-dire le contenu sur lequel **Solr va chercher** quand un utilisateur utilise la recherche.

 - **Le contenu "stocké"**, c'est le contenu qui va **être retourné après la recherche**. C'est très utile, si vous voulez afficher des informations supplémentaires lors de l'affichage des résultats. Par exemple, quand on indexe, un tutoriel, on peut souhaiter lors de l'affichage, afficher tous les noms des auteurs sans pour autant permettre à l'utilisateur de rechercher sur le nom des auteurs. C'est à ça que servent les informations stockés.

 - **Les champs** qui vont permettre de définir les **critères de recherches**.

**Chaque module** qui possède du contenu à indexer, possède **un fichier ``search_indexes.py``**.
Ce fichier permet d'indiquer quels contenus vont être indexés et sur quels champs l'utilisateur pourrait faire sa recherche.

Pour chaque type de contenu, une classe est nécessaire, cette classe étend toujours deux classes de Haystack : ``indexes.SearchIndex`` et ``indexes.Indexable``.

Prenons un exemple, cette classe permet d'indexer les sujets du forum.

.. sourcecode:: python

    class TopicIndex(indexes.SearchIndex, indexes.Indexable):
        """Indexes topic data"""
        text = indexes.CharField(document=True, use_template=True)
        title = indexes.CharField(model_attr='title')
        subtitle = indexes.CharField(model_attr='subtitle')
        author = indexes.CharField(model_attr='author')
        pubdate = indexes.DateTimeField(model_attr='pubdate', stored=True, indexed=False)

        def get_model(self):
            return Topic

        def index_queryset(self, using=None):
            return self.get_model().objects.filter(is_visible=True)

Le premier champ, permet de définir un fichier de *template*, ou seront gardées les informations à **indexer** et les **informations stockés**.

Grâce au nom du module, et du champ, on peut déterminer où ce trouve le fichier de *template*. Le *template*, se trouve, par défaut dans le dossier ``templates/search/indexes/nom_module/nom_classe_nom_champs.txt``.
Par exemple, le fichier *template* qui définit le contenu à indexer et les informations stockés pour les sujets sera dans ``templates/search/indexes/forum/post_text.txt``.

Voici le fichier de *template*, on voit ici, qu'on indexe deux types d'informations : le nom de l'auteur et le contenu en markdown, retourné par la fonction ``Text``.

.. sourcecode:: python

    {{ object.author.username }}
    {{ object.text }}

Les autres champs de la classe, forment les critères de recherches. C'est les champs sur lesquels, l'utilisateur pourrait rechercher s'il le souhaite.
L'utilisateur pourrait donc rechercher, si on lui fournit l'interface graphique, sur le titre, le sous-titre, l'auteur ou la date de publication.

.. attention::

    Les champs de la classe ne sont pas forcément des contenus indexés (par exemple, ici, le contenu n'est pas indexé), c'est-à-dire que par défaut, si l'utilisateur ne précise pas le champ explicitement.
    Solr ne va pas rechercher sur ces champs.

Le dernier champ est précisé comme "stocké" mais pas indexé, c'est-à-dire que les données seront disponibles dans l'affichage des résultats, on ne peut pas rechercher autrement qu'en explicitant le nom du champ.

.. sourcecode:: python

        def get_model(self):
            return Topic

        def index_queryset(self, using=None):
            return self.get_model().objects.filter(is_visible=True).exclude(title="Spacefox est le plus fort!")

La première méthode permet de définir le modèle du contenu à indexer et la deuxième méthode, permet d'exclure du contenu qu'on ne voudrait pas indexer.

Plus d'information :
 - `Documentation de Haystack (en) <http://django-haystack.readthedocs.org/en/v2.3.1/tutorial.html>`_

Le cas particulier de l'indexation des tutoriels et articles
------------------------------------------------------------

Depuis la ZEP-12, les tables dans la base de données pour les parties, chapitres et extraits ont été supprimées.

Les contenus (tutoriels et articles) sont stockés dans des tables spéciales qui ne servent qu'à l'indexation.
Ces tables sont nommés ``SearchIndexContent``, ``SearchIndexContainer``, ``SearchIndexExtract``, ``SearchIndexAuthors`` et ``SearchIndexTag``.

Mais ces tables doivent-être remplies, il est impossible de le faire à la publication de façon synchrone et bloquante, car cette opération prend du temps et des I/O. Pour rappel,

- I/O : ``2 + 2 * nombre de conteneurs + nombre d'extraits`` (bien que cette opération se fasse au travers d'une archive compressée ZIP, ce qui modifie les performances)
- Pour la base de données :
   - En suppression : ``1 + nombre de conteneurs + nombre d'extraits``,
   - En ajout : ``1 + nombre de conteneurs + nombre d'extraits``

Pour rappel, lors de la publication d'un contenu, dans la table ``PublishableContent``, le champ ``must_reindex`` est passé à ``True`` indiquant que le contenu doit-être ré-indexé.

Plus tard, souvent avant l'utilisation de la commande ``python manage.py rebuild_index``, la commande ``python manage.py index_content`` est utilisée.
Elle permet de copier les données des articles et tutoriels dans les tables de recherche. Elle utilise pour cela la version du contenu qui est stocké dans le fichier ZIP généré à la publication, afin de gagner du temps.

Vous pouvez trouver plus d'information, sur cette commande `ici <#utilisation-de-la-commande-index-content>`_.

Comment lancer l'indexation et/ou comment vérifier les données indexées ?
-------------------------------------------------------------------------

Il faut installer et démarrer Solr, régénérer le ``schema.xml`` et réindexer les données, pour cela, consulter la `documentation d'installation <../install/install-solr.html>`_.

Cette procédure est nécessaire à chaque modification des critères d'indexation.

Si vous voulez, vérifier les données indexées, il faut vous rendre dans l'interface d'administration de Solr. Entrez dans un navigateur, l'adresse `http://localhost:8983/solr/ <http://localhost:8983/solr/>`_ pour vous rendre dans l'interface d'administration.

Sélectionnez dans la colonne à gauche, à l'aide du menu déroulant le nom de votre collection.

    .. figure:: ../images/search/webinterface-solr.png
       :align: center

Deux options s'offrent à vous :
 - Rechercher le contenu grâce à l'interface, « Query » dans Solr. Pour accéder à cette interface, cliquer sur "Query" dans le menu à gauche.
 .. figure:: ../images/search/query.png
    :align: center

 Vous arrivez sur l'interface, vous permettant de faire une recherche directement dans Solr.

 .. figure:: ../images/search/interface-query.png
    :align: center

 De nombreuses abbréviations sont utilisées dans cette interface, vous pouvez rechercher leurs significations dans la `documentation de Solr (en) <https://cwiki.apache.org/confluence/display/solr/Common+Query+Parameters>`_.

 Un seul champ va nous intéresser, il est nommé "q". Ce champs vous permet de définir les mots-clés recherchés. Dans l'exemple, du dessus, j'ai choisi le mot clé "Java".
 Cliquez sur "Execute Query", le bouton bleu en bas de l'interface, pour effectuer la recherche. Vous avez ainsi les résultats qui s'affichent dans la partie de gauche.

 - Vous pouvez aussi avoir besoin de vérifier si tel champ indexe des données, ou quelles sont ces données. Pour cela, il faut vous rendre dans l'interface "Schema browser".
 Pour cela, utilisez le menu de gauche.

 .. figure:: ../images/search/schemabrowser.png
    :align: center

Vous arrivez sur une nouvelle interface :

 .. figure:: ../images/search/interface-webbrowser.png
    :align: center

En haut, à gauche, vous devez définir le nom du champ, sélectionnez-en un grâce à la liste déroutante. Dans la capture, j'ai choisi le champ "subtitle".

Vous pouvez lire très facilement si le champ est indexé ou/et stocké grâce au tableau sur la droite.

Une autre information, très utile est de voir quels sont les mots indexés, pour cela cliquez sur le bouton "Load Term Info".

 .. figure:: ../images/search/bouton-loadterminfo.png
    :align: center

Un nouveau tableau s'affiche, avec les différents mots les plus utilisés :

 .. figure:: ../images/search/result-terminfo.png
    :align: center

Comment fonctionne le code de la recherche ?
--------------------------------------------

Le code de la recherche se situe principalement dans le module ``search``. Le code est très simple, dans le fichier ``urls.py`` :

.. sourcecode:: python

        urlpatterns = patterns('haystack.views',
           url(r'^$', search_view_factory(
               view_class=CustomSearchView,
               template='search/search.html',
               form_class=CustomSearchForm
           ), name='haystack_search')

On a défini un ``CustomSearchView`` et un ``CustomSearchForm`` qui vont nous permettre de redéfinir les critères sur la recherche de contenu ainsi que le formulaire.

Les filtres pour la recherche, se trouvent dans le ``get_results`` du fichier ``views.py``.

Quels sont les fichiers de configuration importants ?
=====================================================

Les fichiers de configurations les plus importants sont le fichier ``schema.xml`` et le fichier ``solrconfig.xml``.
Ces deux fichiers sont stockés dans le dossier d'installation de Solr à l'intérieur du sous-dossier ``example/solr/collection1/conf/``.

Le fichier ``schema.xml`` permet de définir les types de champs qu'on pourrait créer, par exemple, définir ce qu'est un champ de type texte, ce qu'en est un de type date…
Il permet de définir aussi des filtres (et des *tokenizers* (des filtres qui découpent des mots)) lors de l'indexation du contenu et avant la recherche.

Le fichier de ``solrconfig.xml``, permet de définir les paramètres de configuration du moteur de recherche. On a gardé les paramètres par défaut.

La question qui se pose naturellement est pourquoi veut-on appliquer des filtres (et des *tokenizers*) avant l'indexation et avant la recherche ?

Tout simplement car il faut traiter le contenu avant de l'indexer car certains mots ne doivent pas apparaître dans l'indexation. Par exemple, les mots comme "le", "la", "les", "ou", "de", "par" ne sont pas des mots importants et ne vont pas permettre de représenter ce que l'utilisateur cherche.

Il est aussi très important d'enlever les radicaux et les pluriels des mots car ils ne sont pas nécessaires.
Si un utilisateur veut rechercher, par exemple, la phrase "Les Cornichons n'aiment pas les poissons", lors de l'indexation et de la recherche, on va appliquer des filtres pour découper les mots. On aura ainsi dans le contenu "Les" "Conichons", "n'aiment", "pas", "les", "poissons".
Ensuite le moteur de recherche, peut choisir d'enlever les pluriels, on aura donc "Le" "Conichon", "aime", "pas", "le", "poisson". On peut aussi choisir de supprimer tous les mots pas ou peu importants, on aura donc à la fin de cette étape : "Conichon", "aime", "pas", "poisson". Ces quatres mots formeront le contenu à indexer.

Le ``schema.xml`` comme dit plus haut permet de définir ces filtres, lors de la génération du fichier ``schema.xml`` par Haystack (la commande ``python manage.py build_solr_schema``), les filtres sont ajoutés.
Le projet Zeste de Savoir a eu besoin de définir des filtres. En effet, les filtres par défaut traitent uniquement du contenu en anglais. Quand la bibliothèque Haystack va générer le fichier ``schema.xml``, le projet va remplacer le *template* de génération par celui du projet qui inclut les filtres.
Ce fichier de *template* est défini dans ``templates/search_configuration/solr.xml``. Les filtres appliqués sont dans la balise ``fieldType`` avec le nom ``text_french``.

Vous pouvez constater les filtres avec l'interface d'administration web de Solr.

Allez dans l'administration `http://localhost:8983/solr/ <http://localhost:8983/solr/>`_, dans la liste déroulante sur votre gauche et choisissez "collection1". Puis juste en-dessous, cliquez sur le bouton "Analysis". Une nouvelle page s'ouvre,

 .. figure:: ../images/search/interface-listefiltres.png
    :align: center

Cette interface permet de savoir quels filtres sont appliqués et comment. Le champ à gauche, c'est pour l'indexation et à droite pour la recherche.

Tapez une phrase d'exemple en français dans le champ à gauche comme dans la capture. Choisissez le champ, par exemple "text". Cliquez maintenant sur le bouton "Analyse Values" en bleu à droite. Vous avez un tableau avec chaque mot en colonne et sur les lignes ce sont les résultats après chaque filtre, dans la première colonne vous avez le nom des filtres, si vous passez votre curseur dessus.

Utilisation de la commande ``index_content``
--------------------------------------------

Cette commande permet de recopier les informations du contenu dans les tables spécifiques pour l'indexation. Ces contenus ne peuvent en effet pas être indexés directement (Solr ne permet pas d'indexer les fichiers), l'utilisation de cette commande est donc nécessaire.

.. attention::

    Ne pas lancer en même temps, la commande ``index_content`` et la commande ``rebuild_index`` de Solr.

Elle possède plusieurs options, vous pouvez les consulter en utilisant la commande ``python manage.py index_content -h`` ou en lisant directement le code source dans le fichier ``zds/search/management/commands/index_content.py``.

Si vous utilisez directement la commande ``python manage.py index_content`` sans argument, tous les objets ``SearchIndex*`` correspondant aux contenus (articles et tutoriels) sont supprimés puis à nouveau recopiés dans les tables de recherche.

La commande ``index_content`` peut recevoir des arguments : les *pk* correspondant aux ``PublishableContent``. Un exemple serait ``python manage.py index_content 1 2 12``: si vous préciser ces arguments, les informations des contenus 1, 2 et 12 seront recopiées dans les tables de recherche.

L'option ``--only-flagged`` peut être uilisée. Elle permet de sélectionner uniquement les contenus (articles et tutoriels) qui ont le champ ``must_reindex`` à ``True``, afin de ne ré-indexer que ce qui est nécesssaire.
