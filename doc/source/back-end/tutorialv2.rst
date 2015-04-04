=======================================
Les tutoriels et articles v2.0 (ZEP 12)
=======================================

Vocabulaire et définitions
==========================

- **Contenu** (*content*): désigne, de manière générale, quelque chose qui peut être produit et édité sur ZdS, c'est à dire un article ou un tutoriel. Tout contenu sur ZdS possède un dossier qui lui est propre et dont le contenu est expliqué plus loin. Ce dossier contient des informations sur le contenu lui-même (*metadata*, par exemple une description, une licence, ...) et des textes, organisés dans une arborescence bien précise.
- **Article** : contenu, généralement cours, visant à faire découvrir un sujet plus qu'à l'expliquer (ex: découverte d'une nouvelle technique, "c'est toute une histoire", ...) ou a donner un état des lieux sur un sujet donné de manière concises (ex: statistiques sur le ZdS, nouvelle version d'un programme, actualité, ...)
- **Tutoriel** : contenu, en général plus long, qui a pour vocation d'apprendre quelque chose ou d'informer de manière plus complète sur des points précis.
- **GIT**: système de versionnage employé (entre autre) par ZdS. Il permet de faire cohexister différentes versions d'un contenu de manière simple et transparente pour l'auteur.
- **Version** : toute modification apportée sur un contenu (ou une de ces partie) génère une nouvelle version de celui-ci, qui est indentifiée par un *hash*, c'est à dire une chaine de caractère de 20 caractère de long (aussi appellée *sha* en référence à l'algorithme qui sert à les générer) et qui identifie de manière unique cette version parmi toutes celles que le contenu contient. ZdS peut également identifier certaines versions de manière spécifique : ainsi, on peut distinguer la version brouillon (*draft*), la version bêta (*beta*), la version en validation (*validation*) et la version publié (*public*). ZdS retient tout simplement les *hash* associés à ces différentes versions du tutoriel pour les identifier comme telles.
- Fichier **manifest.json** : fichier à la racine de tout contenu et qui décrit celui-ci de deux manières : par des informations factuelles sur le contenu en lui-même (*metadata*) et par son arborescence. Le contenu de ce fichier est détaillé plus loin. On retiendra qu'à chaque version correspond en général un fichier manifest.json donné dont le contenu peut fortement changer d'une version à l'autre.
- **Conteneur** (*container*) : sous-structure d'un contenu. Voir plus loin.
- **Extrait** (*extract*) : base atomique (plus petite unité) d'un contenu. Voir plus loin.

De la structure générale d'un contenu
=====================================

Un **contenu** est un conteneur avec des métadonnées (*metadata*, décrites ci-dessous). On peut également le désigner sous le nom de **conteneur principal** (il n'as pas de conteneur parent). Pour différencier articles et tutoriels, une de ces métadonnées est le type (*type*).

Un **conteneur** (de manière générale) peut posséder un conteneur parent et des enfants (*children*). Ces enfants peuvent être eux-même des conteneurs ou des extraits. Il a donc pour rôle de regrouper différents éléments. Outre des enfants, un conteneur possède un titre (*title*), une introduction (*introduction*), une conclusion (*conclusion*). On notera qu'un conteneur ne peut pas posséder pour enfant des conteneur ET des extraits.

Un **extrait** est une unité de texte. Il possède un titre (*title*) et un texte (*text*).

Tout les textes sont formatés en *markdown* (dans la version définie par le ZdS, avec les ajouts).

Conteneur et extraits sont des **objets** (*object*). Dès lors, ils possèdent tout deux un *slug* (litérallement, "limace") : il s'agit d'une chaine de caractère généré à partir du titre de l'objet et qui, tout en restant lisible par un être humain, le simplifie considérablement : un *slug* est uniquement composé de caractères alphanumériques minuscules et non-accentués (`[a-z0-9]*`) ainsi que des caractères `-` (tiret) et `_` (*underscore*)[^underscore]. Ce *slug* a deux utilités : il est employé dans l'URL permetant d'accéder à l'objet et dans le nom de fichier/dossier employer pour le stocker. Dès lors, cette spécification **impose** que ce *slug* soit unique au sein du conteneur parent, et que le *slug* du contenu soit unique au sein de tout les contenu de ZdS (ce qui ne signifie pas que tout les slugs doivent être uniques, tant que ces deux règles sont respectées).

[^underscore]: à noter que l'*underscore* est conservé par compatibilité avec l'ancien système, les nouveaux *slugs* générés par le système d'édition de ZdS n'en contiendront pas.

.. attention::

    Lors du déplacement d'un conteneur ou d'un extrait, les slugs sont modifiés de manière à ce qu'il n'y aie pas de colision.

    À noter que le slug doit être différent de celui donné au nom des introductions et des conclusions éventuelles. L'implémentation du ZdS considère que ceux-ci sont `introduction` et `conclusion`, mais ce n'est pas obligatoire.

En fonction de sa position dans l'arborescence du contenu, un conteneur peut aussi bien représenter le tutoriel/article lui-même (s'il est conteneur principal), une partie ou un chapitre. Ainsi, dans l'exemple suivant :

.. sourcecode:: text

    Contenu (tutoriel)
    |
    +-- Conteneur 1
         |
         +-- Extrait 1


le ``Conteneur 1`` sera rendu par ZdS comme étant un chapitre d'un (moyen-) tutoriel, et dans l'exemple suivant :

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


le `Conteneur 1` sera rendu par ZdS comme étant une partie d'un (big-) tutoriel, et `Conteneur 2` et `Conteneur 3` comme étant les chapitres de cette partie.

Les deux exemples donnés plus haut reprennent l'arboresence typique d'un contenu : Conteneur principal-[conteneur]~*n*~-extraits (ou *n* peut être nul). En fonction de la profondeur de l'arborescence (plus grande distance entre un conteneur enfant et le conteneur principal), le contenu sera nommé de manière différente. S'il s'agit d'un contenu de type tutoriel, on distinguera :

+ **Mini-tutoriel** : le contenu n'as que des extraits pour enfant (au minimum 1) ;
+ **Moyen-tutoriel** : le contenu a au moins un conteneur pour enfant. Ces conteneurs sont pour ZdS des chapitres ;
+ **Big-tutoriel** : le contenu a un ou plusieurs conteneur-enfants (considéré par ZdS comme des parties), dont au moins 1 possède un conteneur enfant (considérés par Zds comme des chapitres).

Il n'est pas possible de créer une arborescence à plus de 2 niveaux (parce que ça n'as pas de sens).

On considère qu'un article est l'équivalent d'un mini-tutoriel, mais dont le but est différent (voir ci-dessus).

Aspects techniques et fonctionnels
==================================

Métadonnées d'un contenu
------------------------

On distingue actuelement deux types de métadonnées (*metadata*) : celles qui sont versionnées (et donc reprises dans le manifest.json) et celle qui ne le sont pas. La liste exhaustive de ces dernière (à l'heure actuelle) est la suivante :

+ Les *hash* des différentes version du tutoriels (`sha_draft`, `sha_beta`, `sha_public` et `sha_validation`) ;
+ Les auteurs du contenu ;
+ Les catégories auquel appartient le contenu ;
+ La miniature ;
+ La source du contenu si elle n'as pas été rédigée sur ZdS mais importée avec une licence compatible ;
+ La présence ou pas de JSFiddle dans le contenu ;
+ Différentes informations temporelles : date de création (`creation_date`), de publication (`pubdate`) et de dernière modification (`update_date`).

Ces différentes informations sont stockées dans la base de donnée, au travers du modèle `PublishableContent`. Pour des raisons de facilité, certaines des métadonnées versionnées sont également stockée en base de donnée : le titre, le type de contenu, la licence et la description. En ce qui concerne la version de celle-ci, c'est TOUJOURS celle correspondant **à la version brouillon** qui sont stockées, il ne faut donc **en aucun cas** les employer pour résoudre une URL ou à travers une template correspondant à la version publiée.

Les métadonnées versionnées sont stockées dans le fichier manifest.json


Le stockage en pratique
-----------------------

Comme énoncé plus haut, chaque contenu possède un dossier qui lui est propre (dont le nom est le slug du contenu), stocké dans l'endroit défini par la variable `ZDS_APP['content']['repo_path']`. Dans ce dossier ce trouve le fichier manifest.json.

Pour chaque conteneur, un dossier est créé, qui contient les éventuels fichiers correspondants aux introduction, conclusion et différents extraits, ainsi que des dossiers pour les éventuels conteneurs enfants. Il s'agit de la forme d'un contenu tel que généré par ZdS en utilisant l'éditeur intégré.

Il est demandé de se conformer un maximum à cette structure pour éviter les mauvaises surprises en cas d'édition externe (voir ci-dessous).

Éventuelle édition externe
--------------------------

Actuellement, l'importation est possible sous forme principalement d'un POC à l'aide d'un fichier ZIP. Ce mécanisme doit être conservé mais peut être étendu : ne plus être lié à la base de donnée pour autre chose que les métadonnées du contenu externe permet une simplification considérable de l'édition hors-ligne (entre autre, la possibilité d'ajouter ou de supprimer comme bon semble à l'auteur).

Au maximum, ce système tentera d'être compréhensif envers une arborescence qui serait différente de celle énoncée ci-dessous. Par contre **l'importation réorganisera les fichiers importés de la manière décrite ci-dessus**, afin de parer aux mauvaises surprises.

Tout contenu qui ne correspond pas aux règles précisées ci-dessus ne sera pas ré-importable. Ne sera pas ré-importable non plus un contenu dont les fichiers indiqués dans le manifest.json n'existent pas ou sont incorrects. Seront supprimés les fichiers qui seraient inutiles (images, qui actuelement doivent être importées séparément dans une gallerie, autres fichiers supplémentaires, pour des raisons élémentaire de sécurité).

Publication d'un contenu ("mise en production")
===============================================

Processus de publication
------------------------

Apès avoir passé les étapes de validations (`détaillées ailleurs`_), le contenu est près à être publié. Cette action
est effectuée par un membre du staff. Le but de la publication est
double : permettre aux visiteurs de lire le contenu, mais aussi
d’effectuer certains traitements (détaillés par après) afin que celui-ci
soit sous une forme qui soit plus rapidement affichable par ZdS. C’est
pourquoi ces contenus ne sont pas stockés au même endroit (voir
``ZDS_AP['content']['repo_public_path']``

.. _détaillées ailleurs: http://zds-site.readthedocs.org/fr/latest/tutorial/tutorial.html#cycle-de-vie-des-tutoriels

).

La mise en production se passe comme suis :

1. S'il s'agit d'un nouveau contenu (jamais publié), un dossier dont le nom est le slug du contenu est créé. Dans le cas contraire, le contenu de ce dossier est entièrement effacé.
2. Le manifest.json correspondant à la version de validation (`sha_publication`) est copié dans ce dossier. Il servira principalement à valider les URLs, créer le sommaire et gérer le comportement des boutons "précédents" et "suivants" dans les conteneur dont les enfants sont des extraits (voir ci-dessous).
3. L'arborescence des dossiers est conservée pour les conteneur dont les enfants sont des conteneur, et leur éventuelles introduction et conclusion sont parsé en HTML. À l'inverse, pour les conteneurs dont les enfants sont des extraits, un fichier HTML unique est créé, reprenant de manière continue la forme parsée de l'éventuelle introduction, des différents extraits dans l'ordre et de l'éventuelle conclusion.
4. Le `sha_public` est mis à jour dans la base de donnée et l'objet `Validation` est changé de même.

Consultation d'un contenu publié
--------------------------------

On ne doit pas avoir à ce servir de GIT pour afficher la version publiée d'un contenu.

Dès lors, deux cas se présentent :

+ L'utilisateur consulte un conteneur dont les enfants sont eux-mêmes des conteneur (c'est à dire le conteneur principal ou une partie d'un big-tutoriel) : le manifest.json est employé pour générer le sommaire, comme c'est le cas actuelement, l'introduction et la conclusion sont également affichés.
+ L'utilisateur consulte un conteneur dont les enfants sont des extraits: le fichier HTML généré durant la mise en production est employé tel quel par la *template* correspondante, additionné de l'éventuelle possibilité de faire suivant/précédent (qui nécéssite la lecture du manifest.json)

