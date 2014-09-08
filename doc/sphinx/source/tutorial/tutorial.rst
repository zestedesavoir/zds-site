=============
Les tutoriels
=============

Les composantes d'un tutoriel
=============================

Un tutoriel n'est qu'un ensemble d'introduction de corps et de conclusion.
Cependant, selon la taille souhaitée du tutoriel, il peut nécessiter une organisation
particulière. C'est pourquoi les tutoriel de ZdS sont structurés en **quatre** niveaux.

Niveau 1 : Le tutoriel
----------------------

Ce niveau définit l'ensemble des métadonées assocciées à un tutoriel, c'est le plus haut
niveau de touts les tutoriels. on y retrouve les informations suivantes :

- titre
- description
- logo
- licence
- sous-catégories
- introducton
- conclusion

Niveau 2 : La partie
--------------------

Ce niveau adapté à des documents un peu plus longs, permet de subdiviser notre contenu
en plusieurs parties. C'est typiquement le niveau qui sera utile si vous souhaiter rédiger
un mémoire, ou une thèse. Par contre, pour un simple article, ce n'est pas la peine d'en faire
des parties. Un tutoriel peut contenir plusieurs parties et une partie comprend essentiellement
les informations suivantes :
- titre
- introduction
- conclusion
- position (dans le tutoriel)

Niveau 3 : La chapitre
----------------------

On retrouve la encore les mêmes notions qu'on peut rencontrer dans la rédaction d'un document
pédagogique. Si une partie peut contenir plusieurs chapitres (on le verra plus loin dans le cas
des bigtutos), un chapitre peut être rattaché a un tutoriel directement (minituto) .
Le chapitre comprend les informations suivantes :
- titre
- introduction
- conclusion

Niveau 4 : L'extrait
--------------------

L'extrait est la niveau le plus fin de subdivision d'un tutoriel. Il constitue le contenu, ou encore
le corps de notre texte. Un extrait est constitué uniquement d'un bloc de texte.


Les types de tutoriels
======================

Il existe actuellement deux types de tutoriels, les minituto et les bigtutos,
Même s'il y'a une réflexion sur la création de moyen-tuto, laissez moi déjà
vous présenter ce qui existe aujourdhui.

Les minitutos
-------------

Un minituto est un format de tutoriel pour du contenu léger. Fonctionnellement il s'agit d'un tutoriel
qui ne contient qu'un seul chapitre (niveau 3) mais peut contenir un ou plusieurs exrait.
On pourrait le représenter ainsi :

.. sourcecode:: none

 Tutoriels  -> chapitre  -
                         |-> introduction
                         |-> 
                         |-> extrait 1
                         |-> extrait 2
                         |-> extrait ...
                         |-> extrait n
                         |-> 
                         |-> conclusion


Dans ce cas, le nombre de chapitre est bien limité à 1 et la présentation d'un minituto consiste à
présenter un seul chapitre de la structure globale.

Les bigtutos
------------

Un bigtuto, si on repense à nos niveaux de structure, une un tutoriel dans lequel on peut avoir plusieurs
parties, chaque partie pouvant contenir plusieurs chapitres et chaque chapitre pouvant à leur tour
contenir plusieurs extraits.
Les big tutos reprenent donc ici tous les éléments de la structure. Ce format est adapté aux tutoriels
donc le contenu est assez conséquent, et demande beaucoup de structuration. On pourrait le représenter ainsi:


.. sourcecode:: none

  Tutoriels -
            -> partie 1 -
                          |-> chapitre 1 -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
                          |-> chapitre 2 -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
                          |-> chapitre n -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
            -> partie 2 -
                          |-> chapitre 1 -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
                          |-> chapitre 2 -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
                          |-> chapitre n -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
            -> partie n -
                          |-> chapitre 1 -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
                          |-> chapitre 2 -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion
                          |-> chapitre n -
                                         |-> introduction
                                         |-> extrait 1
                                         |-> extrait 2
                                         |-> extrait ...
                                         |-> extrait n
                                         |-> conclusion


Cycle de vie des tutoriels
==========================

Quelque soit le type de tutoriel, le cycle de vie de celui-ci reste toujours le même.
Un tutoriel peut-être rédigé par un ou plusieurs auteurs. Chaque modification sur le tutoriel
est conservée afin de pouvoir retrouver l'historique des modifications et éventuellement
recupérer le contenu perdu. Lorsqu'un tutoriel est crée il rentre dans sa première étape.

Le brouillon
------------

Le brouillon est la première étape du cycle de vie d'un tutoriel. Il donne toujours l'état
le plus récent du contenu d'un tutoriel vu par les auteurs. Chaque fois que le contenu du
tutoriel est modifié, c'est la version brouillon qui est mise à jour.
La version brouillon est accessible uniquement pour les auteurs et validateurs d'un tutoriel,
Si on souhaite donner un accès en lecture seule à nos écrit, il faut passer par la méthode
adéquate.

La beta
-------

Lorsque les auteurs estiment que leur tutoriel est arrivé à un certain niveau de maturité, et qu'ils souhaitent 
recuillir les premiers retours de lecteurs, ils se doivent de mettre à disposition de la communauté le tutoriel en
lecture seule. C'est le mode beta.

La procédure voudrait que lors de l'ouverture d'une beta, l'auteur crée un sujet dans le forum des tutoriels
en beta, en postant le lien version la version beta du tutoriel.

.. attention::

    Le lien de la beta, peut être trouvé via votre profil utilisateur, vous devez recopier tout le lien avec la partie `?version=blablabla`. Et pensez bien à modifier ce lien lorsque vous mettez à jour votre version beta.

En fait lorsqu'un tutoriel est en mode beta, il s'agit d'une version précise qui est mise 
dans ce mode. On peut continuer à mettre à jour la version brouillon pour rajouter de nouveaux chapitres
à notre tutriel, pendant ce temps, la communauté lit une version figée de notre tutoriel. L'avantage étant que
si le tutoriel prend beaucoup de temps à lire, le lecteur n'a pas de mauvaise surprise de mise à jour
pendant sa lecture. Les auteurs quant à eux doivent mettre à jour manuellement leur version beta et ainsi
ils controllent pleinement ce qu'ils mettent à disposition des lecteurs.

La validation
-------------

Une fois que l'auteur a eu assez de retour sur son tutoriel, et qu'il estime qu'il est prêt à être publié,
il décide d'envoyer son tutoriel en validation.

L'envoi en validation n'est pas définitif, dans le sens ou, vous pouvez à tout moment mettre à jour la version
qui se trouve du coté des validateurs. Evitez d'en abuser tout de même, car, si un validateur commence à lire
votre tutoriel, il devra recommencer son travail si vous faites une mise à jour dessus. Ce qui pourrait non seulement
ralentir le processus de validation de votre tutoriel, mais décourager aussi le validateur. Donc un conseil a donner serait
de n'envoyer que du contenu sûr en validation.

Comme pour la beta, la version brouillon du tutoriel peut continuer à être améliorée pendant que la version 
de validation reste figée. Auteurs et validateurs peuvent donc continuer à travailler chacun de son coté.

La publication
--------------

Une fois le contenu, lu et relu par l'équipe staff, le tutoriel est publié. Il faut bien préciser que le processus
de validation peut être assez long en fonction de la taille du tutoriel traité. Un tutoriel n'est pas obligé
d'être publié à la suite d'une demande de validation, il peut aussi être rejeté. Dans tout les cas, un historique
de validation est disponible pour les membres du staff.

La publication d'un tutoriel entraine la création d'export en plusieurs formats. On a les formats

- Markdown : disponible uniquement pour les membres du staff et les auteurs des tutoriels
- HTML
- PDF
- EPUB : format de lecture adapté aux liseuses
- Archive : un export de l'archive contenant le dépot git du projet.

Pour différentes raisons, il se peut que l'export dans divers formats échoue. Dans ce cas, le lien de téléchargement n'est pas présenté. Un fichier de log sur le serveur enregistre les problèmes lié à l'export d'un format.

Aujourd'hui il existe des bugs dans la conversion en PDF (blocs custom), qui devront être réglés plus tard avec la `ZEP 05 <http://zestedesavoir.com/forums/sujet/676/zep-05-refonte-du-traitement-markdown-pour-lexport>`_)

L'aspect technique
==================

Le stockage dans la base de donnée
----------------------------------

Aujourd'hui la base de données est utilisée comme zone tampon, surtout parce que Django propose déjà des methodes
d'enregistrement des objets en base de données de manière concurrentes et *thread safe*. L'idée étant de s'en
détacher à terme.
La version stockée dans la base de données est le dernier état, c'est à dire l'état de la version en
brouillon. Il ne faut donc pas aller chercher en base de données les informations pour les afficher.

Chaque tutoriel possède trois attributs principaux :

- sha_draft : le hash du commit de la version brouillon
- sha_beta : le hash du commit de la version brouillon
- sha_validation : le hash du commit de la version validation
- sha_public : le hash du commit de la version publique

On peut les voir comme des pointeurs sur chaque version, et le fait qu'ils soient stockés en base les rends
plus accessibles. A terme aussi, on devrait pouvoir en faire des branches.

Il faut aussi noter qu'on ne stocke pas le contenu (introduction, conclusion, extrait) directement en base de données, on stocke uniquement les chemin relatif vers le fichiers markdown qui contiennent le contenu.

Les données versionnés
----------------------

Le module des tutoriels se base sur **git** pour versionner son contenu. Physiquement, nous avons un répertoire pour chaque tutoriel (point d'initialisation du dépot). A l'intérieur nous avons un répertoire par partie, et dans chaque partie, un répertoire par chapitre, et pour chaque chapitre, un fichier par extrait.

Pour éviter les conflits dans les noms de fichier, le chemin vers un extrait aura souvent le modèle suivant :

`[id_partie]_[slug_partie]/[id_chap]_[slug_chap]/[id_extrait]_[slug_extrait].md`

Pour pouvoir versionner tout ceci, nous avons un fichier nommé `masnifest.json` chargé de stocker l'ensemble des métadonnées versionnées du tutoriel. Ce fichier manifest est lui aussi versionné. Pour chaque version, il suffit donc de lire ce fichier pour reconstituer un tutoriel. C'est un fichier json qui reprend la structure du document, et les différents chemins relatifs vers le contenu. Les métadonnées stockées sont :

- Le titre du tutoriel, des parties, des chapitres et des extraits
- Le sous-titre du tutoriel
- La licence du tutoriel
- Les divers chemin relatifs vers les fichiers markdown

L'objectif étant d'arriver à tout versionner (catégories, ...) et de ne plus avoir à lire dans la base de donnée pour afficher quelque chose.

Qu'en est-il des images ?
+++++++++++++++++++++++++

Le versionning des images d'un tutoriel (celles qui font partie de la gallerie du tuto) continue a faire débat, et il a été décidé pour le moment de ne pas les versionner dans un premier temps, pour des raisons simples :

- versionner les images peut rendre très rapidement une archive lourde si l'auteur change beaucoup d'images, il va se trouver avec des images plus jamais utilisées qui traine dans son archive.
- avoir besoin d'interroger le dépot à chaque fois pour lire les images peut rapidement devenir lourd pour la lecture.

Le parti a été pris de ne pas versionner les images qui sont stockées sur le serveur, ce n'est pas critique et on peut très bien travailler ainsi. Par contre, il faudra mieux y réfléchir pour une version 2 afin de proposer la rédaction totalement en mode hors ligne.

Quid des tutoriels publiés ?
++++++++++++++++++++++++++++

Les tutoriels en *offline* sont tous versionnés, et sont dans le répertoire `tutoriels_private`. Lorsqu'ils sont validés le traitement suivant est appliqué.

- On copie le dépôt du tutoriel dans le répertoire `tutoriels_public`
- On va chercher dans l'historique du dépot les fichiers correspondant à la version publique
- On converti ces fichiers en html (en utilisant zMarkdown)
- On stocke les fichiers html sur le serveur.

Ainsi, pour lire un tutoriel public, on a juste besoin de lire les fichiers html déjà convertis.
