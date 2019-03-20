=========================
Les fichiers de manifeste
=========================

Chaque contenu publiable (tutoriel et article) est décrit par un fichier de manifeste écrit au format JSON.

Ce fichier de manifeste a pour but d'exprimer, versionner et instancier les informations et méta-informations du contenu tout au long du workflow de publication.

Les informations en question sont l'architecture, les titres, les liens vers les sources, les informations de license ainsi que la version du fichier de manifeste lui-même.

Le fichier de manifeste est intrinsèquement lié à un interpréteur qui est inclus dans le module de contenu associé.

Les versions du manifeste
=========================

Nomenclature
------------

La version du manifeste (et de son interpréteur) suit une nomenclature du type "semantic version" (SemVer), c'est-à-dire que la version est séparée en trois parties selon le format v X.Y.Z

- X : numéro de version majeur
- Y : numéro de version à ajout fonctionnel mineur
- Z : numéro de version de correction de bug

Plus précisément :

- L'incrémentation de X signifie que la nouvelle version est potentiellement incompatible avec la version X-1. Un outil de migration doit alors être créé.
- L'incrémentation de Y signifie que la nouvelle version possède une compatibilité descendante avec la version X.Y-1 mais que la compatibilité ascendante n'est pas assurée. C'est-à-dire que le nouvel interpréteur peut interpréter un manifeste de type X.Y-1
  mais l'ancien interpréteur ne peut pas interpréter un manifeste X.Y. Le cas typique d'incrémentation de Y est le passage d'obligatoire à optionnel d'un champ du manifeste.
- L'incrémentation de Z assure la compatibilité ascendante ET descendante, les cas typiques d'incrémentation de Z est l'ajout d'un champ optionnel au manifeste.

Sauf cas exceptionnel, la numérotation de X commence à 1, la numérotation de Y commence à 0, la numérotation de Z commence à 0.

La version du manifeste est donnée par le champ éponyme situé à la racine du manifeste ( ``{ version: "2.0.0"}``).
L'absence du champ version est interprétée comme ``{version: "1.0"}``.
Les 0 non significatifs sont optionnels ainsi ``{version: "1"}`` est strictement équivalent à ``{version: "1.0"}`` lui-même strictement équivalent à ``{version: "1.0.0"}``.

Version 2.1
-----------

La version 2.1 est la version actuellement utilisée.
Le manifest voit l'arrivée d'un nouvel élément non obligatoire ``ready_to_publish`` qui sera utilisé sur tous les éléments de type ``Container``.
Cet élément permet de marquer qu'une partie ou un chapitre est prêt à être publié. Lorsque la valeur est à ``False``, la partie ou le chapitre
sont simplement ignorés du processus de publication.

Lorsque l'attribut n'est pas renseigné, il est supposé *truthy*.


Version 2.0
-----------



.. sourcecode:: js

    {
        "object": "container",
        "slug": "un-tutoriel",
        "title": "Un tutoriel",
        "introduction": "introduction.md",
        "conclusion": "conclusion.md",
        "version": 2,
        "description": "Une description",
        "type": "TUTORIAL",
        "licence": "Beerware",
        "children": [
            {
                "object": "container",
                "slug": "titre-de-mon-chapitre",
                "title": "Titre de mon chapitre",
                "introduction": "titre-de-mon-chapitre/introduction.md",
                "conclusion": "titre-de-mon-chapitre/conclusion.md",
                "children": [
                    {
                        "object": "extract",
                        "slug": "titre-de-mon-extrait",
                        "title": "Titre de mon extrait",
                        "text": "titre-de-mon-chapitre/titre-de-mon-extrait.md"
                    },
                    (...)
                ]
            },
            (...)
        ]
    }

1. ``type`` : Le type de contenu, vaut "TUTORIAL" ou "ARTICLE". *Si ce champ est absent ou invalide, le type vaudra par défaut "TUTORIAL".*
2. ``description`` : La description du contenu. Est affichée comme sous-titre dans la page finale. **Obligatoire**
3. ``title`` : Le titre du contenu. **Obligatoire**
4. ``slug`` : slug du contenu qui permet de faire une url SEO-friendly. Pour rappel, `certaines contraintes doivent être respectées dans le choix du slug <contents.html#des-objets-en-general>`_. **Obligatoire**.  ATENTION : si ce slug existe déjà dans notre base de données, il est possible qu'un nombre lui soit ajouté
5. ``introduction`` : le nom du fichier Mardown qui possède l'introduction. Il doit pointer vers le dossier courant. *Optionnel mais conseillé*
6. ``conclusion`` : le nom du fichier Mardown qui possède la conclusion. Il doit pointer vers le dossier courant. *Optionnel mais conseillé*
7. ``licence`` : nom complet de la license. *A priori* les licences "CC" et "Tous drois réservés" sont supportées. Le support de toute autre licence dépendra du site utilisant le code de ZdS (fork) que vous visez. **Obligatoire**
8. ``children`` : tableau contenant l'architecture du contenu.
    1. ``object`` : type d'enfant (*container* ou *extract*, selon qu'il s'agisse d'une section ou d'un texte). **Obligatoire**
    2. ``title`` : le titre de l'enfant. **Obligatoire**
    3. ``slug`` : le slug de l'enfant pour créer une url SEO-friendly, doit être unique dans le contenu, le slug est utilisé pour trouver le chemin vers l'enfant dans le système de fichier si c'est une section. Attention, `certaines contraintes doivent être respectées dans le choix du slug <contents.html#des-objets-en-general>`_. **Obligatoire**
    4. ``introduction`` : nom du fichier contenant l'introduction quand l'enfant est de type *container*. *Optionnel mais conseillé*
    5. ``conclusion`` : nom du fichier contenant la conclusion quand l'enfant est de type *container*. *Optionnel mais conseillé*
    6. ``children`` : tableau vers les enfants de niveau inférieur si l'enfant est de type *container*. **Obligatoire**
    7. ``text`` : nom du fichier contenant le texte quand l'enfant est de type *extract*. Nous conseillons de garder la convention ``nom de fichier = slug.md`` mais rien n'est obligatoire à ce sujet. **Obligatoire**




Version 1.0
-----------


.. note::

    La version 1.0 est dépréciée, et il est conseillé d'employer la version 2.0. Il est ceci dit toujours possible
    `d'importer des contenus <contents.html#import-de-contenus>`_ dont le manifeste est toujours en version 1.0, mais à vos risques et périls.


La version 1.0 définit trois types de manifeste selon que nous faisons face à un article,  un mini tutoriel ou un big tutoriel.


MINI TUTO
+++++++++

.. sourcecode:: js

    {
        "title": "Mon Tutoriel No10",
        "description": "Description du Tutoriel No10",
        "type": "MINI",
        "introduction": "introduction.md",
        "conclusion": "conclusion.md"
    }

BIG TUTO
++++++++

.. sourcecode:: js

    {
        "title": "3D temps réel avec Irrlicht",
        "description": "3D temps réel avec Irrlicht",
        "type": "BIG",
        "licence": "Tous droits réservés",
        "introduction": "introduction.md",
        "conclusion": "conclusion.md",
        "parts": [
            {
                "pk": 7,
                "title": "Chapitres de base",
                "introduction": "7_chapitres-de-base/introduction.md",
                "conclusion": "7_chapitres-de-base/conclusion.md",
                "chapters": [
                    {
                        "pk": 25,
                        "title": "Introduction",
                        "introduction": "7_chapitres-de-base/25_introduction/introduction.md",
                        "conclusion": "7_chapitres-de-base/25_introduction/conclusion.md",
                        "extracts": [
                            {
                                "pk": 87,
                                "title": "Ce qu'est un moteur 3D",
                                "text": "7_chapitres-de-base/25_introduction/87_ce-quest-un-moteur-3d.md"
                            },
                            {
                                "pk": 88,
                                "title": "Irrlicht",
                                "text": "7_chapitres-de-base/25_introduction/88_irrlicht.md"
                            }
                        ]
                    },(...)
                ]
            }, (...)
        ]
    }

Article
+++++++

.. sourcecode:: json

    {
        "title": "Mon Article No5",
        "description": "Description de l'article No5",
        "type": "article",
        "text": "text.md"
    }
