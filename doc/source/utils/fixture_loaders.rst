===========================================
Le chargement de jeux de données (fixtures)
===========================================

Zeste de Savoir étant un projet très complet il est nécessaire de pouvoir charger un ensemble de jeux de données
de manière automatique pour créer une nouvelle instance à des fins de test ou pour forker le site.

Pour faciliter la tâche, trois outils sont mis à disposition des développeurs, testeurs et utilisateurs.

Les données sérialisables pour une base fonctionnelle
-----------------------------------------------------

Un premier ensemble de données simples est accessible par la commande intégrée à django ``python manage.py loaddata``.

Cette commande s'attend à une liste de fichier au format yaml et supporte les *wildcards*.
Nous possédons un ensemble de données sérialisées dans le dossier fixtures:

- ``categories.yaml`` : contient le chargement de 3 catégories de tutoriels, 2 sous catégories de tutoriels rangées dans les bonnes catégories parentes
- ``forums.yaml`` : contient le chargment de 4 catégories de forum et de 10 forums dans ces catégories
- ``licences.yaml`` : contient le chargement de 2 licences dont la licence par défaut (tous droit réservés)
- ``mps.yaml`` : **nécessite le chargement des users**, contient la création d'un MP d'un membre à un admin
- ``topics.yaml``: **nécessite le chargement des users**, contient la création de plusieurs topics dans les forums dont un résolu
- ``users.yaml``: Crée 6 utilisateurs:
    - admin/admin avec les droits d'administration
    - staff/staff faisant partie du groupe staff
    - user/user un utilisateur normal et sans problème
    - ïtrema/ïtrema un utilisateur normal, sans problème mais qui aime l'utf8
    - Anonymous/anonymous : le compte d'anonymisation
    - External/external: le compte pour accueillir les cours externes des auteurs ne voulant pas devenir membre ou quittant le site
    - decal/decal: le compte qui possède un identifiant ``Profile`` différent de l'identifiant ``user`` pour permettre de tester des cas ou ces id sont différents
- ``oauth_applications.yaml``: crée une application de test `pour l'API <../api.html>`_:
    - ``client_id``: ``w14aIFqE7z90ti1rXE8hCRMRUOPBP4rXpfLZIKmT`` ;
    - ``client_secret``: ``0q4ee800NWs8cSHa0FIbkTLwEncMqYHOCAxNkt9zRmd10bRk1J18TkbviO5QHy2b66ggzyLADm79tJw5BQf2XfApPnk0nogcFaYhtNO33uNlzzT8sXfxu3zzBFu5Wejv``.
- ``group.yaml``: crée les descriptions de deux groupes de la page d'accueil (staff et groupe technique)

De ce fait, le moyen le plus simple de charger l'ensemble des données de base est la commande ``make fixtures``.

Les données complexes voire les scénarios
-----------------------------------------

Certaines données, pour exister, ont besoin de ressources supplémentaires qui ne sont pas forcément sérialisables.
Par exemple un tutoriel a besoin d'un dépôt git, une option d'aide (ZEP 03) a besoin d'une icône qui sera accessible depuis
le web...

Ces données ont besoin d'être traitées par une routine avant d'être créées. Ces routines existent déjà dans les objets
appelés Factory qui sont dans chacun des fichiers ``factories.py`` de tous les modules.

Pour utiliser ces fabriques d'objet, vous aurez une nouvelle fois recours au format yaml afin de décrire les
fabriques que vous désirez utiliser ainsi que les paramètres à envoyer auxdites fabriques.

Le format du fichier est celui-ci:

.. sourcecode:: yaml

    -   factory: zds.module.factories.YourFactory
        fields:
            champ_string: "valeur1"
            champ_int: 0

    -   factory: zds.utils.factories.YourFactory
        fields:
            champ_string: "valeur2"
            champ_int: 1

Les fichiers de factory déjà existant sont rangés dans le dossier ``fixtures/advanced``.

Pour utiliser un fichier yaml de factory, il vous suffit de lancer la commande ``python manage.py load_factory_data chemin_vers_vos_fichier.yaml``.
Cette méthode est compatible avec les *wildcards*.

Pour utiliser les factories, il vous faudra vous référer à la documentation de ces dernières puisque les champs associés peuvent
être de deux types :

- les champs de base qui sont aussi présents avec la même orthographe dans le modèle de données
- les champs personnalisés qui sont faits pour indiquer des comportements complémentaires à la commande
  par exemple, avec la zds.utils.HelpWrittingFactory, utiliser ``fixture_image_path`` vous permettra de renseigner le chemin relatif de l'image dans le dossier ``fixtures`` plutôt que le chemin absolu.

Bien que ce module soit optionnel, si vous désirez qu'il soit possible de demander de l'aide sur les tutoriels et articles,
il vous faudra utiliser ``python manage.py load_factory_data fixtures/advanced/aide_tuto_media.yaml``.

Tester sur un jeu de données massif
-----------------------------------

.. attention::
    L'utilisation de la commande qui suit peut prendre du temps

Afin de tester avec un jeu de données qui se rapproche le plus possible de ce qui peut se trouver en exploitation, et aussi
trouver une variété suffisante pour être confiant en vos tests, nous avons développé une commande qui génère une immense
quantité de données.

Pour l'utiliser il suffit de lancer ``python manage.py load_fixtures --size=SIZE --all``.

.. note::

    Vous pouvez ajouter ``--racine`` qui permet de changer la base pour le nommage des utilisateurs (« user » par défaut).
    Vous pouvez ne créer les éléments que d'un module précis (ou de quelques-uns) via des options telles que ``--forum``.
    Ces options ne sont pas utilisables quand ``--all`` est ajouté.

Les types à charger sont en fait les modèles de données qui seront créés.

Chaque modèle de données aura son propre *coefficient de création* c'est à dire le nombre d'éléments qui seront créés de base.
Ce coefficient sera à multiplier par le *coefficient de taille* dirrigé par :

- size=low : *coefficient de taille* = 1
- size=medium: *coefficient de taille* = 2
- size=high: *coefficient de taille* = 3

+---------------------------------+-----------------------------------+-----------------------------+
|Type                             | Modèles créés                     | *coefficient de création*   |
+=================================+===================================+=============================+
|member                           |Profile (simple membres)           |10                           |
+---------------------------------+-----------------------------------+-----------------------------+
|staff                            |Profile (avec droit de staff)      |3                            |
+---------------------------------+-----------------------------------+-----------------------------+
|gallery                          |Gallery/UserGallery (au hasard)    |1 (par user)                 |
|                                 +-----------------------------------+-----------------------------+
|                                 |Image                              |3 (par gallery)              |
+---------------------------------+-----------------------------------+-----------------------------+
|category_forum                   |forum.Category                     |4                            |
+---------------------------------+-----------------------------------+-----------------------------+
|category_content                 |Licence                            | Plusieurs [#lic]_           |
|                                 +-----------------------------------+-----------------------------+
|                                 |utils.Category                     |5                            |
|                                 +-----------------------------------+-----------------------------+
|                                 |utils.SubCategory                  |10                           |
+---------------------------------+-----------------------------------+-----------------------------+
|forum                            |utils.Forum                        |8                            |
+---------------------------------+-----------------------------------+-----------------------------+
|tag                              |Tag                                |30                           |
+---------------------------------+-----------------------------------+-----------------------------+
|topic                            |Topic (dont *sticky* et *locked*)  |10                           |
+---------------------------------+-----------------------------------+-----------------------------+
|post                             |Post                               |20 (par topic) [#moy]_       |
+---------------------------------+-----------------------------------+-----------------------------+
|comment                          |ContentReaction                    |20 (par contenu) [#moy]_     |
+---------------------------------+-----------------------------------+-----------------------------+
|tutorial et article              |PublishableContent [#cv2]_         |10                           |
+---------------------------------+-----------------------------------+-----------------------------+



.. [#lic] Les licences suivantes seront créée : "CB-BY", "CC-BY-ND", "CC-BY-ND-SA", "CC-BY-SA", "CC", "CC-BY-IO" et "Tout-Droits"
.. [#cv2] C'est à dire 60% en validation (dont 20% réservés) et 30% publiés. S'il sagit de tutoriels, 50% de petits, 30% de moyen et 20% de *bigs*.
.. [#moy] Ce nombre est une moyenne, le nombre réel est choisi au hasard autour de cette moyenne
