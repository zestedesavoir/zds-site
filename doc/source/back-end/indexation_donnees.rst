========================
Le module de recherche ?
========================

La recherche se découpe en deux parties distinctes:
 - L'indexation des données
 - La recherche par l'utilisateur

L'indexation des données
=========================

**L'indexation** des données consiste à **rassembler toutes les données** sur lesquelles l'utilisateur va **pouvoir rechercher**. Elle est faite au prealable.
L'indexation est faite de telle façon qu'on puisse rechercher sur les éléments suivants:
 - Les tutoriels (Les parties, les chapitres, les extraits)
 - Les articles (titre, description, date de publication, contenu en markdown)
 - Les sujets (titre, sous titres, auteurs, le contenu en markdown, le nom du forum)
 - Les réponses au sujets (auteur et contenu en markdown)

L'indexation est réalisé à la demande, même si un jour, elle pourait être en `temps réel <https://zestedesavoir.com/forums/sujet/3334/indexation-en-temps-reel/>`_.

Aujourd'hui, l'indexation est réalisé toutes les trentaines de minutes, sur le serveur de production. Tous le contenu est ré-indexés à chaque fois, ce qui prend 100 pourcents du processus toutes les 5 minutes.
Des solutions sont présentes dans `la documentation <http://django-haystack.readthedocs.org/en/latest/searchindex_api.html#get-updated-field>`_, sans qu'on puisse réellement `les appliquées <https://github.com/zestedesavoir/zds-site/pull/2771>`_.

La recherche
============

L'utilisateur peut utiliser la recherche, en utilisant la "sidebar".

   .. figure:: ../images/search/sidebar.png

Des critères de recherche, peuvent être ajouté sur la page de recherche. Plus tard, on pourrais ajouter des facets, plus d'information sur `la ZEP correspondante <https://zestedesavoir.com/forums/sujet/1082/zep-15-navigation-a-facettes-a-travers-le-site/>`_.
Les critères de recherches sont uniquement sur le type de contenu (tutoriel, article, sujet, réponse).

Dans le code ?
==============

On utilise pour **l'indexation** une **librairie** en python **Haystack** et le **moteur de recherche Solr**.

    .. figure:: ../images/search/schema-recherche-lib.png

Pour l'indexation, on indique à Haystack quels contenu, on doit indexer. Haystack appelle une librairie Python nommée PySolr.
PySolr n'est jamais utilisé directement dans le code, on doit toujours passer par la librairie Haystack. PySolr éffectue des appels à une API REST exposé par le moteur de recherche Solr.

Pour la recherche, c'est le même principe, librairie Haystack -> librairie PySolr -> l'API REST de Solr.

Pourquoi avoir utilisé Solr, ne peut t-on pas appeller Solr directement ?
-------------------------------------------------------------------------

On pourrais directement appeler Solr mais Haystack nous propose plusieurs avantages:
 - Nous permet d'être indépendant, du moteur de recherche utilisé, aujourd'hui, on utilise Solr mais demain, on pourrait assez facilement le remplacer par un autre moteur de recherche telle-que `Xapian <http://xapian.org/>`_, `Elasticsearch <https://www.elastic.co/>`_, `Whoosh <http://whoosh.ca/>`_
 - Assez facile à utiliser
 - Nous permet d'avoir relativement facilement, les facets, la recherche spatiale, suggestions des mots clés, autocompletion, … .
 - Nous permet de généré les fichiers de configurations plus facilement.
 - Libre (BSD) et gratuit.

Pourquoi Solr et pas un autre moteur de recherche ?
---------------------------------------------------

Les principbux avantages sont:
 - Une interface web compléte
 - Libre et Gratuit
 - Multiplateforme
 - Simple à utiliser

Comment fonctionne le code de l'indexation ?
--------------------------------------------

Tout d'abord, avant d'attaquer le code, il faut bien faire la différence entre:

 - **Le contenus "indexés"**, c'est à dire le contenu sur lesquels **Solr va chercher** quand un utilisateur utilise la recherche.

 - **Le contenus "stocké"**, c'est le contenu qui va **être retourné aprés la recherche**. C'est très utile, si vous voulez afficher des informations supplémentaires lors de l'affichage des résultats. Par exemple, quand on indexe, un tutoriel, on peut souhaiter lors de l'affichage, afficher tous les noms des auteurs sans pour autant permettre à l'utilisateur de rechercher sur le nom des auteurs. C'est à ça que sert les informations stockés.

 - **Les champs** qui vont permettre de définir les **critères de recherches**.

**Chaque module** qui possède du contenu à indexer, possède **un fichier search_indexes.py**.
Ce fichier permet d'indiquer quels contenus vont être indexés et sur quels champs l'utilisateur pourrait faire sa recherche.

Pour chaque type de contenu, une classe est nécessaire, cette classe étend toujours deux classes de Haystack: indexes.SearchIndex, indexes.Indexable.

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

Le premier champ, permet de définir un fichier de templates, ou seront stockés les informations à **indexer** et les **informations stockés**.

Grâce au nom du module, et du champ, on peut déterminer ou ce trouve le fichier de templates. Le template, se trouve, par-défaut dans le dossier: templates/search/indexes/nom_module/nom_classe_nom_champs.txt.
Par exemple, le fichier template qui définit le contenus à indexer et les informations stockés pour les sujets sera dans templates/search/indexes/forum/post_text.txt.

Voici le fichier de template, on voit ici, qu'on indexe deux types d'informations: le nom de l'auteur et le contenu en markdown, retourné par la fonction Text.

.. sourcecode:: python

    {{ object.author.username }}
    {{ object.text }}

Les autres champs de la classe, forment les critères de recherches. C'est les champs sur lesquels, l'utilisateur pourrait rechercher si il le souhaite.
L'utilisateur pourrait donc rechercher, si on lui fournit l'interface graphique, sur le titre, le sous-titre, l'auteur ou la date de publication.

.. attention::

    Les champs de la classe ne sont pas forcément des contenus indexés (par-exemple, ici, le contenu n'est pas indexés), c'est à dire que par-défaut, si l'utilisateur ne précise pas le champs explicitement.
    Solr ne va pas recherché sur ces champs.

Le dernier champ est précisé comme "stocké" mais pas indéxés, c'est à dire que les données seront disponible dans l'affichage des résultats, on ne peut pas recherche autrement qu'en explicitant le nom du champ.

.. sourcecode:: python

        def get_model(self):
            return Topic

        def index_queryset(self, using=None):
            return self.get_model().objects.filter(is_visible=True).exclude(title="Spacefox est le plus fort!")

La premiére méthode permet de définir le modéle du contenus à indexer et la deuxième méthode, permet d'exclure du contenu qu'on ne voudrait pas indexer.

Plus d'information:
 - `Documentation de Haystack <http://django-haystack.readthedocs.org/en/v2.4.0/tutorial.html>`_

Comment lancer l'indexation et/ou comment vérifier les données indexés ?
------------------------------------------------------------------------

Il faut installer et démarrer Solr, régénérer le schema.xml et réindexer les données, pour cela, consulter la `documentation d'installation <../install/install-solr.rst>`_.

Cette procédure est nécessaire à chaque modification des critères d'indexation.

Si vous voulez, vérifier les données indexés, il faut vous rendre dans l'interface d'administration de Solr. Entrez dans un navigateur, l'adresse `http://localhost:8983/solr/ <http://localhost:8983/solr/>`_ pour vous rendre dans l'interface d'administration

Sélectionner dans la colonne à gauche, à l'aide du menu déroulant le nom de votre collection.

    .. figure:: ../images/search/webinterface-solr.png

Deux options s'offrent à vous:
 - Rechercher le contenu grâce à l'interface, « Query » dans Solr. Pour accéder à cette interface, cliquer sur "Query" dans le menu à gauche.
 .. figure:: ../images/search/query.png

 Vous arrivez sur l'interface, vous permettant de faire une recherche directement dans Solr.

 .. figure:: ../images/search/interface-query.png

 De nombreuses abbreviations sont utilisé dans cette interface, vous pouvez rechercher leurs significations dans la `Documentation de Solr <https://cwiki.apache.org/confluence/display/solr/Common+Query+Parameters>`_.

 Un seul champ va nous intéresser, il est nommé "q". Ce champs vous permet de définir les mots clés recherchés. Dans l'exemple, du dessus, j'ai choisi le mot clé Java.
 Cliquer sur "Execute Query", le bouton bleu en bas de l'interface, pour effectuer la recherche. Vous avez ainsi les résultats qui s'affichent dans la partie de gauche

 - Vous pouvez aussi avoir besoin de vérifier si tel champ indexe des données, ou quels sont ces données. Pour cela, il faut vous rendre dans l'interface "Schema browser".
 Pour cela, utilisez le menu de gauche.

 .. figure:: ../images/search/schemabrowser.png

Vous arrivez sur une nouvelle interface:

 .. figure:: ../images/search/interface-webbrowser.png

En haut, à gauche, vous devez définir le nom du champ, sélectionner en un grâce à la liste déroutante. Dans la capture, j'ai choisi le champ subtitle.

Vous pouvez lire très facilement si le champ est indexés ou/et stockés grâce au tableau sur la droite.

Une autre information, trés utile est de voir quels sont les mots indexés, pour cela cliquez sur le bouton "Load Term Info".

 .. figure:: ../images/search/bouton-loadterminfo.png

Un nouveau tableau s'affiche, avec les différents mots les plus utilisé:

 .. figure:: ../images/search/result-terminfo.png

Comment fonctionne le code de la recherche ?
--------------------------------------------

Le code de la recherche se situe principalement dans le module search. Le code est trés simple, dans le fichier urls.py

.. sourcecode:: python

        urlpatterns = patterns('haystack.views',
           url(r'^$', search_view_factory(
               view_class=CustomSearchView,
               template='search/search.html',
               form_class=CustomSearchForm
           ), name='haystack_search')

On a définis un CustomSearchView et un CustomSearchForm qui vont nous permettre de redéfinir les critères sur la recherche de contenu ainsi que le formulaire.

Les filtres pour la recherche, se trouve dans le get_results du fichier view.py.

Quels sont les fichiers de configuration important ?
====================================================

Les fichiers de configurations les plus important sont le fichier schema.xml et le fichier solrconfig.xml.
Ces deux fichiers sont stocké dans le dossiers d'installation de solr et dans les sous dossiers suivants: /example/solr/collection1/conf/schema.xml.

Le fichier schema.xml permet de définir les types de champs qu'on pourrait créé, par exemple, définir ce qu'est qu'un champ de type texte, ce que c'est qu'un de type date, … .
Il permet de définir aussi des filtres (et des tokenizers (des filtres qui découpent des mots)) lors de l'indexation du contenu et avant la recherche.

Le fichier de solrconfig.xml, permet de définir les paramètres de configuration du moteur de recherche. On a gardé les paramètres par-défaut.

La question qui se pose naturellement est pourquoi veut-on appliquer des filtres (et des tokenizers) avant l'indexation et avant la recherche ?

Tout simplement car il faut traiter le contenu avant de l'indexer car certains mots ne doivent pas apparaître dans l'indexation. Par exemple, les mots comme le, la, les, ou, de par ne sont pas des mots important et ne vont pas permettre de représenter ce que l'utilisateur cherche.

Il est aussi trés important d'enlever les radicaux et le pluriels des mots car ils  ne sont pas nécessaires.
Si un utilisateur veut rechercher, par exemple, la phrase "Les Cornichons n'aiment pas les poissons", lors de l'indexation et de la recherche, on va appliquer des filtres pour découper les mots on aura ainsi dans le contenu "Les" "Conichons", "n'aiment", "pas", "les", "poissons".
Ensuite le moteur de recherche, peut choisir d'enlever les pluriels, on aura donc "Le" "Conichon", "aime", "pas", "le", "poisson". On peut aussi de supprimer tous les mots pas ou peu important, on aura donc à la fin de cette étape: "Conichon", "aime", "pas", "poisson". Ces quatres mots formeront le contenus à indexer.

Le schema.xml comme dit plus haut permet de définir ces filtres, lors de la génération du fichier schema.xml par Haystack (la commande python manage.py build_solr_schema), les filtres sont ajoutés.
Le projet Zeste de Savoir à eu besoin de définir des filtres. En effet, les filtres par-défaut traite uniquement du contenu en Anglais. Quand la librairie Haystack va généré le fichier schema.xml, le projet va remplacer le templates de génération par celui du projet qui inclus les filtres.
Ce fichier de templates est définis dans templates/search_configuration/solr.xml. Les filtres appliqués sont dans la balise fieldType avec le name text_french.

Vous pouvez constater les filtres avec l'interface d'administration web de Solr.

Aller dans l'administration http://127.0.0.1:8983/solr/#, dans la liste déroulante sur votre gauche, choisissez "collection1". Puis juste en-dessous, cliquer sur le bouton 'Analysis'. Une nouvelle page s'ouvre,

 .. figure:: ../images/search/interface-listefiltres.png

Cette interface permet de savoir quels filtres sont appliqués et comment. Le champ à gauche, c'est pour l'indexation et à droite pour la recherche.

Taper une phrase d'exemple en français dans le champ à gauche comme dans la capture. Choisissez le champ, par-exemple: "text". Cliquer maintenant sur le bouton "Analyse Values" en bleu à droite. Vous avez un tableau avec chaque mot en colonne et sur les lignes c'est les résultats après chaque filtre, dans la première colonne vous avez le nom des filtres, si vous passez votre curseur dessus.
