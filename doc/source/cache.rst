========
Le cache
========

Cette page détaille tout ce qui a trait au cache dans Zeste de Savoir. Comme le cache impacte à la fois le *front-end* et le *back-end*, il a droit à sa page dédiée.

Règles d'implémentation
=======================

Les systèmes de cache peuvent être très puissants et gérer beaucoup de cas différents ; hélas il est très facile d'en faire une soupe imbuvable et de provoquer des bugs mystiques et impossibles à reproduire.

Pour éviter les prises de tête et conserver une application propre, tout cache sur Zeste de Savoir doit respecter les règles suivantes :

1. Le cache est **facultatif**. Le site conserve des **performances acceptables sans cache** :
    - Ça garanti les performances en cas d'échec de cache (*cache miss*)
    - Si le cache est désactivé (problème serveur, développement...) l'application fonctionne
2. Le cache est **inoffensif** :
   - Aucune donnée sensible ne peut se retrouver dans le cache. Jamais. Dans aucun cas.
   - Si jamais un bug provoque une fuite de cache (*donnée de cache servie à la mauvaise personne*), les conséquences sont sans importance.
3. Le cache est **efficace**. Si c'est pour gagner 1 ms, ce n'est pas la peine.
4. Le cache est **invalidé** autant que faire se peut. Parce que c'est toujours mieux d'avoir un cache long et correctement invalidé plutôt que de devoir le rendre presque inefficace à cause de *timeouts* très courts imposés pour garder une cohérence dans les données.

Implémentation technique
========================

1. Définir un **identifiant**. Caractères autorisés : ``a-z0-9_``
    - C'est le nom de fragment de cache
    - C'est la clé de *timeout* dans les paramètres
2. Définir la **clé de cache**
3. Vérifier les **cas d'invalidation**
4. Vérifier que toutes les règles d'implémentation vont bien être respectées
5. Définir la durée de cache dans le fichier ``settings.py``, paramètre ``CACHE_TIMEOUTS``.
6. Implémenter le cache ! (définition des blocs, vues, ... à cacher ; invalidations ...).
7. Mise à jour de cette documentation.

Les caches implémentés
======================

*Type* dans les tableaux correspond au `type de cache Django <https://docs.djangoproject.com/en/1.7/topics/cache/>`.

*Usage* dans les tableaux correspond à l'endroit où est défini le bloc caché.

Blocs des articles
-------------------

Il s'agit des blocs visuels de présentation des articles que l'on trouve par exemple sur la page d'accueil ou sur la liste des articles.

==================  =====================================================================
Identifiant         article_item
Type                Template fragment caching
Clé de cache        identifiant + clé primaire de l'article + "link" + "show_description"
Usage               templates/article/includes/article_item.part.html
Temps de cache      1 heure
Cas d'invalidation  La sauvegarde d'un article invalide l'entrée correspondante
==================  =====================================================================

``link`` et ``show_description`` dans la clé de cache sont les deux paramètres de même nom passés au *template* ``article/includes/article_item.part.html``.

Comme l'ajout de commentaires sauvegarde l'article lui-même (lien vers le dernier commentaire), ce cas est automatiquement géré.

Blocs des tutoriels
-------------------

Il s'agit des blocs visuels de présentation des tutoriels que l'on trouve par exemple sur la page d'accueil ou sur la liste des tutoriels.

==================  ============================================================
Identifiant         tutorial_item
Type                Template fragment caching
Clé de cache        identifiant + clé primaire du tutoriel + "beta" + "show_description"
Usage               templates/tutorial/includes/tutorial_item.part.html
Temps de cache      1 heure
Cas d'invalidation  La sauvegarde d'un tutoriel invalide l'entrée correspondante
==================  ============================================================

``beta`` et ``show_description``  dans la clé de cache sont les deux paramètres de même nom passés au *template*``tutorial/includes/tutorial_item.part.html``.

Blocs "À la une"
----------------

Il s'agit du bloc des éléments à la une sur la page d'accueil

==================  =================================================================
Identifiant         home_featured_resources
Type                Template fragment caching
Clé de cache        identifiant (une seule clé de cache, donc)
Usage               templates/home.html
Temps de cache      1 heure
Cas d'invalidation  La sauvegarde d'un une quelconque invalide cette entrée de cache.
==================  =================================================================

Menu principal "Tutoriels / Articles / Forums"
----------------------------------------------

Il s'agit du bloc "Tutoriels / Articles / Forums" du menu principal.

==================  ===========================================================
Identifiant         header_menu
Type                Template fragment caching
Clé de cache        identifiant + clé primaire de l'utilisateur (User) connecté
Usage               templates/base.html
Temps de cache      1 heure
Cas d'invalidation  Aucun
==================  ===========================================================

Le menu "Tutoriels / Articles / Forum" est toujours le même pour un utilisateur donné (ou presque, ça doit bouger 2 fois dans les semaines très riches en nouvelles catégories). Par contre, l'invalidation serait très casse-pieds à faire, puisque la plupart du temps modifier l'utilisateur ne change pas son menu. Comme le menu ne contient aucune donné sensible, on peut avoir donc un élément faux dans le menu pendant 1h max.
