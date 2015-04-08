=======================================
Les tutoriels et articles v2.0 (ZEP 12)
=======================================

Vocabulaire et définitions
==========================

- **Contenu** (*content*): désigne, de manière générale, quelque chose qui peut être produit et édité sur ZdS, c'est-à-dire un article ou un tutoriel. Tout contenu sur ZdS possède un dossier qui lui est propre et dont le contenu est expliqué plus loin. Ce dossier contient des informations sur le contenu lui-même (*metadata*, par exemple une description, une licence, ...) et des textes, organisés dans une arborescence bien précise.
- **Article** : contenu, généralement court, visant à faire découvrir un sujet plus qu'à l'expliquer (ex: découverte d'une nouvelle technique, "c'est toute une histoire", ...) ou à donner un état des lieux sur un sujet donné de manière concise (ex: statistiques sur ZdS, nouvelle version d'un programme, actualité...).
- **Tutoriel** : contenu, en général plus long, qui a pour vocation d'apprendre quelque chose ou d'informer de manière plus complète sur des points précis.
- **GIT**: système de gestion de versions employé (entre autres) par ZdS. Il permet de faire coexister différentes versions d'un contenu de manière simple et transparente pour l'auteur.
- **Version** : toute modification apportée sur un contenu (ou une de ses parties) génère une nouvelle version de celui-ci, qui est indentifiée par un *hash*, c'est-à-dire une chaîne de caractères de 20 caractères de long (aussi appellée *sha* en référence à l'algorithme qui sert à les générer) et qui identifie de manière unique cette version parmi toutes celles que le contenu contient. ZdS peut également identifier certaines versions de manière spécifique : ainsi, on peut distinguer la version brouillon (*draft*), la version bêta (*beta*), la version en validation (*validation*) et la version publié (*public*). ZdS retient tout simplement les *hash* associés à ces différentes versions du tutoriel pour les identifier comme telles.
- Fichier **manifest.json** : fichier à la racine de tout contenu et qui décrit celui-ci de deux manières : par des informations factuelles sur le contenu en lui-même (*metadata*) et par son arborescence. Le contenu de ce fichier est détaillé plus loin. On retiendra qu'à chaque version correspond en général un fichier manifest.json, dont le contenu peut fortement changer d'une version à l'autre.
- **Conteneur** (*container*) : sous-structure d'un contenu. Voir plus loin.
- **Extrait** (*extract*) : base atomique (plus petite unité) d'un contenu. Voir plus loin.

De la structure générale d'un contenu
=====================================

Un **contenu** est un conteneur avec des métadonnées (*metadata*, décrites 
ci-dessous). On peut également le désigner sous le nom de 
**conteneur principal** (il n'a pas de conteneur parent). Pour différencier 
articles et tutoriels, une de ces métadonnées est le type (*type*).

Un **conteneur** (de manière générale) peut posséder un conteneur parent et des 
enfants (*children*). Ces enfants peuvent être eux-même des conteneurs ou des 
extraits. Il a donc pour rôle de regrouper différents éléments. Outre des 
enfants, un conteneur possède un titre (*title*), une introduction 
(*introduction*) et une conclusion (*conclusion*). On notera qu'un conteneur ne 
peut pas posséder pour enfants à la fois des conteneurs ET des extraits.

Un **extrait** est une unité de texte. Il possède un titre (*title*) et un 
texte (*text*).

Tous les textes sont formatés en *markdown* (dans la version définie par ZdS, 
avec les ajouts).

Conteneurs et extraits sont des **objets** (*object*). Dès lors, ils possèdent 
tous deux un *slug* (litéralement, "limace") : il s'agit d'une chaîne de 
caractères générée à partir du titre de l'objet et qui, tout en restant lisible 
par un être humain, le simplifie considérablement : un *slug* est uniquement 
composé de caractères alphanumériques minuscules et non-accentués 
(``[a-z0-9]*``) ainsi que des caractères ``-`` (tiret) et ``_`` (*underscore*). 
Ce *slug* a deux utilités : il est employé dans l'URL permetant d'accéder à 
l'objet et dans le nom de fichier/dossier employé pour le stocker. Dès lors, 
cette spécification **impose** que ce *slug* soit unique au sein du conteneur 
parent, et que le *slug* du contenu soit unique au sein de tous les contenus de 
ZdS (ce qui ne signifie pas que tout les slugs doivent être uniques, tant que 
ces deux règles sont respectées).

.. note::

    À noter que l'*underscore* est conservé par compatibilité avec l'ancien 
    système, les nouveaux *slugs* générés par le système d'édition de ZdS 
    n'en contiendront pas.

.. attention::

    Lors du déplacement d'un conteneur ou d'un extrait, les slugs sont modifiés 
    de manière à ce qu'il n'y ait pas de collision.

    À noter que le slug doit être différent de celui donné aux noms des 
    introductions et conclusions éventuelles. L'implémentation de ZdS considère 
    que ceux-ci sont ``introduction`` et ``conclusion``, mais ce n'est pas 
    obligatoire.

En fonction de sa position dans l'arborescence du contenu, un conteneur peut 
aussi bien représenter le tutoriel/article lui-même (s'il est conteneur 
principal), une partie ou un chapitre. Ainsi, dans l'exemple suivant :

.. sourcecode:: text

    Contenu (tutoriel)
    |
    +-- Conteneur 1
         |
         +-- Extrait 1


le ``Conteneur 1`` sera rendu par ZdS comme étant un chapitre d'un (moyen-) 
tutoriel, alors que dans l'exemple suivant :

.. sourcecode:: text

    Contenu (tutoriel)
    |
    +-- Conteneur 1
         |
         +-- Conteneur 2
         |     |
         |     +-- Extrait 1
         |
         +-- Conteneur 3
               |
               +-- Extrait 1


le ``Conteneur 1`` sera rendu par ZdS comme étant une partie d'un (big-) 
tutoriel, et ``Conteneur 2`` et ``Conteneur 3`` comme étant les chapitres de 
cette partie.

Les deux exemples donnés plus haut reprennent l'arboresence typique d'un 
contenu : Conteneur principal-[conteneur]~*n*~-extraits (où *n* peut être nul). 
En fonction de la profondeur de l'arborescence (plus grande distance entre un 
conteneur enfant et le conteneur principal), le contenu sera nommé de manière 
différente. S'il s'agit d'un contenu de type *tutoriel*, on distinguera :

+ **Mini-tutoriel** : le contenu n'a que des extraits pour enfants (au minimum un) ;
+ **Moyen-tutoriel** : le contenu a au moins un conteneur pour enfant. Ces conteneurs sont pour ZdS des chapitres ;
+ **Big-tutoriel** : le contenu a un ou plusieurs conteneur-enfants (considérés par ZdS comme des parties), dont au moins un possède un conteneur enfant (considérés par ZdS comme des chapitres).

Il n'est pas possible de créer une arborescence à plus de 2 niveaux (parce que 
ça n'a pas de sens).

On considère qu'un article est l'équivalent d'un mini-tutoriel, mais dont le 
but est différent (voir ci-dessus).

Aspects techniques et fonctionnels
==================================

Métadonnées d'un contenu
------------------------

On distingue actuellement deux types de métadonnées (*metadata*) : celles qui 
sont versionnées (et donc reprises dans le manifest.json) et celles qui ne le 
sont pas. La liste exhaustive de ces dernières (à l'heure actuelle) est la 
suivante :

+ Les *hash* des différentes versions du tutoriel (``sha_draft``, ``sha_beta``, ``sha_public`` et ``sha_validation``) ;
+ Les auteurs du contenu ;
+ Les catégories auquelles appartient le contenu ;
+ La miniature ;
+ L'origine du contenu, s'il n'a pas été rédigé sur ZdS mais importé avec une licence compatible ;
+ La présence ou pas de JSFiddle dans le contenu ;
+ Différentes informations temporelles : date de création (``creation_date``), de publication (``pubdate``) et de dernière modification (``update_date``).

Ces différentes informations sont stockées dans la base de données, au travers 
du modèle ``PublishableContent``. Pour des raisons de facilité, certaines des 
métadonnées versionnées sont également stockées en base de données : le titre, 
le type de contenu, la licence et la description. En ce qui concerne la version 
de cette dernière, c'est TOUJOURS celle correspondant 
**à la version brouillon** qui est stockée. Il ne faut donc **en aucun cas** 
les employer pour résoudre une URL ou à travers une template correspondant à la 
version publiée.

Les métadonnées versionnées sont stockées dans le fichier manifest.json


Le stockage en pratique
-----------------------

Comme énoncé plus haut, chaque contenu possède un dossier qui lui est propre 
(dont le nom est le slug du contenu), stocké dans l'endroit défini par la 
variable ``ZDS_APP['content']['repo_path']``. Dans ce dossier se trouve le 
fichier manifest.json.

Pour chaque conteneur, un dossier est créé, contenant les éventuels fichiers 
correspondant aux introduction, conclusion et différents extraits, ainsi que 
des dossiers pour les éventuels conteneurs enfants. Il s'agit de la forme d'un 
contenu tel que généré par ZdS en utilisant l'éditeur en ligne.

Il est demandé de se conformer au maximum à cette structure pour éviter les 
mauvaises surprises en cas d'édition externe (voir ci-dessous).

Éventuelle édition externe
--------------------------

Actuellement, l'importation est possible principalement sous forme d'un POC à 
l'aide d'un fichier ZIP. Ce mécanisme doit être conservé mais peut être étendu 
: ne plus être lié à la base de données pour autre chose que les métadonnées du 
contenu externe permet une simplification considérable de l'édition hors-ligne 
(entre autres, la possibilité d'ajouter ou de supprimer comme bon le semble à 
l'auteur).

Au maximum, ce système tentera d'être compréhensif envers une arborescence qui 
serait différente de celle énoncée ci-dessus. Par contre 
**l'importation réorganisera les fichiers importés de la manière décrite ci-dessus**, 
afin de parer aux mauvaises surprises.

Tout contenu qui ne correspond pas aux règles précisées ci-dessus ne sera pas 
ré-importable. Ne sera pas ré-importable non plus tout contenu dont les 
fichiers indiqués dans le manifest.json n'existent pas ou sont incorrects. 
Seront supprimés les fichiers qui seraient inutiles (images, qui actuellement 
doivent être importées séparément dans une galerie, autres fichiers 
supplémentaires) pour des raisons élémentaires de sécurité.

Publication d'un contenu ("mise en production")
===============================================

Processus de publication
------------------------

Apès avoir passé les étapes de validation 
(`détaillées ailleurs <./tutorial.html#cycle-de-vie-des-tutoriels>`__), le 
contenu est près à être publié. Cette action
est effectuée par un membre du staff. Le but de la publication est
double : permettre aux visiteurs de lire le contenu, mais aussi
d’effectuer certains traitements (détaillés ci-après) afin que celui-ci
soit sous une forme qui soit plus rapidement affichable par ZdS. C’est
pourquoi ces contenus ne sont pas stockés au même endroit 
(voir ``ZDS_AP['content']['repo_public_path']``).

La mise en production se passe comme suit :

1. S'il s'agit d'un nouveau contenu (jamais publié), un dossier dont le nom est le slug du contenu est créé. Dans le cas contraire, le contenu de ce dossier est entièrement effacé ;
2. Le manifest.json correspondant à la version de validation (``sha_publication``) est copié dans ce dossier. Il servira principalement à valider les URLs, créer le sommaire et gérer le comportement des boutons "précédent" et "suivant" dans les conteneurs dont les enfants sont des extraits (voir ci-dessous) ;
3. L'arborescence des dossiers est conservée pour les conteneurs dont les enfants sont des conteneurs, et leur éventuelles introduction et conclusion sont parsées en HTML. À l'inverse, pour les conteneurs dont les enfants sont des extraits, un fichier HTML unique est créé, reprenant de manière continue la forme parsée de l'éventuelle introduction, des différents extraits dans l'ordre et de l'éventuelle conclusion ;
4. Le ``sha_public`` est mis à jour dans la base de données et l'objet ``Validation`` est changé de même.

Consultation d'un contenu publié
--------------------------------

On ne doit pas avoir à se servir de GIT pour afficher la version publiée d'un 
contenu.

Dès lors, deux cas se présentent :

+ L'utilisateur consulte un conteneur dont les enfants sont eux-mêmes des conteneurs (c'est-à-dire le conteneur principal ou une partie d'un big-tutoriel) : le manifest.json est employé pour générer le sommaire, comme c'est le cas actuellement. L'introduction et la conclusion sont également affichées.
+ L'utilisateur consulte un conteneur dont les enfants sont des extraits : le fichier HTML généré durant la mise en production est employé tel quel par le *template* correspondant, additionné de l'éventuelle possibilité de faire suivant/précédent (qui nécéssite la lecture du manifest.json).

Passage des tutos v1 aux tutos v2
=================================

Le parseur v2 ne permettant qu'un support minimal des tutoriels à l'ancien format, il est nécessaire de mettre en place des procédures de migration.

Migrer une archive v1 vers une archive v2
-----------------------------------------

Le premier cas qu'il est possible de rencontrer est la présence d'une archive *hors ligne* d'un tutoriel à la version 1.

La migration de cette archive consistera alors à ne migrer que le fichier de manifeste la nouvelle architecture étant bien plus souple du point de vue des nomenclatures, il ne sera pas nécessaire de l'adapter.

Un outil intégré au code de zds a été mis en place, il vous faudra alors :

- décompresser l'archive
- exécuter ``python manage.py upgrade_manifest_to_v2 /chemin/vers/archive/decompressee/manifest.json``
- recompresser l'archive

Si vous désirez implémenter votre propre convertisseur, voici l'algorithme utilisé en python :

.. sourcecode:: python

    with open(_file, "r") as json_file:
        data = json_reader.load(json_file)
    _type = "TUTORIAL"
    if "type" not in data:
        _type = "ARTICLE"
    versioned = VersionedContent("", _type, data["title"], slugify(data["title"]))
    versioned.description = data["description"]
    versioned.introduction = data["introduction"]
    versioned.conclusion = data["conclusion"]
    versioned.licence = Licence.objects.filter(code=data["licence"]).first()
    versioned.version = "2.0"
    versioned.slug = slugify(data["title"])
    if "parts" in data:
        # if it is a big tutorial
        for part in data["parts"]:
            current_part = Container(part["title"],
                str(part["pk"]) + "_" + slugify(part["title"]))
            current_part.introduction = part["introduction"]
            current_part.conclusion = part["conclusion"]
            versioned.add_container(current_part)
            for chapter in part["chapters"]:
                current_chapter = Container(chapter["title"],
                    str(chapter["pk"]) + "_" + slugify(chapter["title"]))
                current_chapter.introduction = chapter["introduction"]
                current_chapter.conclusion = chapter["conclusion"]
                current_part.add_container(current_chapter)
                for extract in chapter["extracts"]:
                    current_extract = Extract(extract["title"],
                        str(extract["pk"]) + "_" + slugify(extract["title"]))
                    current_chapter.add_extract(current_extract)
                    current_extract.text = current_extract.get_path(True)
                    
    elif "chapter" in data:
        # if it is a mini tutorial
        for extract in data["chapter"]["extracts"]:
            current_extract = Extract(extract["title"],
                str(extract["pk"]) + "_" + slugify(extract["title"]))
            current_extract.text = current_extract.get_path(True)
            versioned.add_extract(current_extract)
    elif versioned.type == "ARTICLE":
        extract = Extract(data["title"], "text")
        versioned.add_extract(extract)

Migrer la base de données
-------------------------

Si vous faites tourner une instance du code de zeste de savoir sous la version 1.X et que vous passez à la v2.X, vous allez
devoir migrer les différents tutoriels. Pour cela, il faudra simplement exécuter la commande ``python manage.py migrate_to_zep12.py ``
