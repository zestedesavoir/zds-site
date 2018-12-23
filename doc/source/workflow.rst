===============================
*Workflow* et détails pratiques
===============================

Cette page détaille le *workflow* utilisé lors du développement de Zeste de Savoir. La `page de contribution <./contributing.html>`_ devrait répondre à vos questions quant au processus de développement. Ici seront aussi décrit quelques détails sur la gestion des tickets sur Github (*tagging* et priorité).

Ce *workflow* est très fortement basé sur le `Git flow <http://nvie.com/posts/a-successful-git-branching-model/>`__.

*Workflow* général
==================

L'idée générale est très simple :

-  Le développement se fait sur la branche ``dev``;
-  La branche ``prod`` contient la version en production;
-  Lorsqu'on juge qu'on a assez de matière pour un nouveau déploiement, on crée une branche dédiée (par exemple ``release-v1.7``) que l'on teste en pré-production (les bugs trouvés seront corrigés sur cette branche);
-  En cas de bug ultra-urgent à corriger en production, on crée une branche spéciale (`hotfix <http://nvie.com/posts/a-successful-git-branching-model/#hotfix-branches>`__).

La pré-production (ou bêta) est disponible sur `beta.zestedesavoir.com <https://beta.zestedesavoir.com>`_.

*Workflow* de développement
===========================

Description
-----------

1. Les fonctionnalités et corrections de bugs se font via des *Pull Requests* (PR) depuis des *forks* via `GitHub <https://github.com/zestedesavoir.com/zds-site>`_.
2. Ces PR sont unitaires. Aucune PR qui corrige plusieurs problèmes ou apporte plusieurs fonctionnalité ne sera acceptée; la règle est : une PR = une fonctionnalité ou une correction.
3. Ces PR sont mergées dans la branche ``dev`` (appelée ``develop`` dans le git flow standard), après une *Quality Assurance* (QA) légère.
4. La branche ``prod`` (appelée ``master`` dans le git flow standard) contient exclusivement le code en production, pas la peine d'essayer de faire le moindre *commit* dessus !
5. Les branches du dépôt principal (``dev``, ``prod`` et la branche de release) ne devraient contenir que des merge de PR, aucun commit direct.

Quelques précisions
-------------------

**Où peut-on trouver les détails pratiques ?**

Tous ces détails sont `dans la page de contribution <./contributing.html>`_. On y trouve entre autres les recommendations en terme de PR ou de messages de commits.

**Qu'est-ce qu'une "QA légère"** ?

C'est s'assurer que le code fait ce qu'il devrait sans passer des heures à re-tester l'intégralité du site. Concrètement, cela implique :

-  une revue de code (*Code Review* (CR));
-  la vérification que des tests correspondants à la fonctionnalité ou à la correction sont présents, cohérents et passent;
-  des tests manuels dans le cas de fonctionnalités ou corrections complexes et/ou critiques (au cas par cas).

Milestones
==========

Pour avoir une vue d'ensemble des modifications inclues ou à inclure dans chaque release, nous utilisons des *milestones*. Il existe une *milestone* par release majeure (e.g. une pour v19, aucune pour v19.1), les PRs mergées dans une version mineure appartenant à la *milestone* de la version majeure correspondante.

Les *milestones* sont également utilisées par le script de génération de rapport de release, rapport contenant quelques détails sur la release en question.

Toute PR se voit attribuer une *milestone*. Elle est attribuée au plus tôt par le *Maintainer* ou le *Release Manager* à l'ouverture de la PR si cette PR doit impérativement passer dans la prochaine release, au plus tard par la personne qui merge la PR lors de son merge. Bien qu'une PR doit généralement être atomique, il arrive - notamment dans le cas des ZEP - qu'elle ait pour effet secondaire de régler plusieurs bugs, d'introduire plusieurs fonctionnalités. Dans ces rares cas, chaque ticket fermé par effet secondaire d'une PR peut également recevoir une *milestone*.

* Toute PR mergée dans dev doit porter la *milestone* « Version de développement »
* Toute PR mergée ailleurs (la branche de release si c'est une correction de bêta, prod en cas de hotfix) doit porter la *milestone* « Version N »

La *milestone* « Version de développement » s'appelle comme ça parce qu'elle contient les modifications apportées depuis la dernière release. Cette *milestone* étant largement la plus utilisée, son nom a l'avantage qu'on voit immédiatement si on attribue ou non la bonne *milestone*, sans avoir à réfléchir au numéro de version.

Lors de la clôture de chaque release, la *milestone* « Version de développement » est renommée « Version N » et une nouvelle *milestone* « Version de développement » est créée.


Stratégie de *tagging* des tickets
==================================

Les étiquettes (ou *labels* ou *tags*) utilisées pour classifier les tickets sont réparties dans des catégories :

-  Quelles sont les **Compétences** requises ?

   -  **C-Back**, pour le *backend*
   -  **C-Front**, pour le *frontend*
   -  **C-API**, pour les *API* du *backend*
   -  **C-Docs**, pour la documentation
   -  **C-Infra**, pour l'infrastucture des serveurs
   -  **C-Search**, pour le moteur de recherche du *backend*

-  Quel est le **Statut** de ce ticket, cette PR ?

   -  **S-BUG**, pour les bugs (par exemple, une fonctionnalité qui vient d'être introduite et qui fonctionne anormalement)
   -  **S-Régression**, pour les retours en arrière en terme de qualité (par exemple, une fonctionnalité qui fonctionnait bien juqu'à maintenant mais qui ne fonctionne plus)
   -  **S-Refactorisation**, pour les réorganisations et nettoyages du code
   -  **S-Zombie**, pour les tickets à faible priorité qui ne donnent plus signe de vie mais ne sont pas résolus pour autant

-  Quelle est la **Priorité** de ce ticket, cette PR ?

   -  **Bloquant**, pour tout ce qui empêche une utilisation correcte du site (impossible de rédiger un contenu, forte atteinte aux performances...)
   -  *D'une manière générale, chacun·e est invité·e à choisir ce sur quoi concentrer ses efforts en fonction de ses intérêts.*

-  Autres

   -  **Facile**, pour les tickets avec une proposition de solution accessible aux débutant·e·s
   -  **Feedback**, pour les tickets sur lesquels l'auteur·e souhaite recevoir un retour, discuter une approche, proposer quelque chose ou ouvrir le débat
   -  *Pour signaler que le contenu d'une PR est succeptible de changer, il est conseillé d'éditer le titre de celle-ci pour y ajouter "[WIP]" au début (cela signifie *Work In Progress*, soit Travail En Cours en français.*


*Workflow* de mise en production
================================

Cette partie est là surtout pour satisfaire votre curiosité, à moins d'avoir les droits de faire une Mise En Production (MEP).

Description
-----------

1. Quand on a assez de nouveautés dans ``dev`` (mais pas trop), on décide de faire une *release*. L'idée est de pouvoir vérifier et corriger les problèmes de cette *release* rapidement, en moins de 2 semaines entre le lancement de la release et sa MEP.

   1. Création d'une **nouvelle branche de release** du nom de la version (par exemple ``release-v1.7``)
   2. Déploiement de cette branche sur l'environnement de pré-production, avec un *dump* de données de production
   3. Tests les plus complets possibles sur ce nouvel environnement
   4. Corrections éventuelles sur cette branche de *release*. Les corrections **ne sont pas remontées sur ``dev``** au fur et à mesure. Cf ci-dessous pour les détails.

2. Lorsqu'on a bien testé cette branche, on la met en production :

   1. Merge de la branche de *release* dans ``dev``
   2. Merge de la branche de *release* dans ``prod``
   3. Tag avec la nouvelle version
   4. Mise en production sur le serveur
   5. Suppression de la branche de *release*, devenue inutile

Pour éviter d'installer les outils front en production pour des questions de fiabilité, le front est automatiquement généré par Travis CI et poussé sur le dépot dès qu'un tag (qui correspond à une release) est poussé sur GitHub. `scripts/push_front.sh <https://github.com/zestedesavoir/zds-site/tree/dev/scripts/push_front.sh>`__ est donc lancé avec l'utilisateur `ZDS-Bot <https://github.com/zds-bot>`__ dès qu'un tag est poussé sur le dépot. Ce script crée un nouveau tag avec *-build* en suffixe, contenant un commit avec le front généré, qui sera déployé en (pré-)production.

Le temps maximum entre la création d'une branche de *release* et sa mise en production est de **deux semaines**. Au-delà on considère qu'il y a trop de problèmes et qu'ils risquent de bloquer le développement :

1. Merge des corrections de la branche de *release* dans ``dev``
2. Pas de mise en production
3. Suppression de la branche de *release*, devenue inutile

En cas de problèmes sur la release
----------------------------------

Vous l'avez lu : les corrections de ``master`` **ne sont pas remontées sur** ``dev`` au fur et à mesure. La raison est que ça prends du temps, de l'énergie et que ça fait beaucoup de merges croisés. Donc toutes les corrections sont remontées en même temps lors de la mise en production. Conséquences :

-  Si vous bossez sur ``dev`` pendant qu'une *release* est en cours, pas la peine de corriger un bug déjà corrigé sur la *release* : la PR serait refusée (pour cause de doublon).
-  Si un *gros* problème est détecté sur la *release* et qu'il est correctible en un temps raisonnable :

   1. Il est corrigé sur la branche de *release*.
   2. Les merges de PR sur ``dev`` qui impliquent un risque même vague de conflit sont bloqués.
   3. S'il y a quand même un conflit (à cause d'une PR mergée sur ``dev`` avant la détection du problème), la personne qui règle le problème fournit 2 correctifs : un pour la branche de *release* et un pour la branche de de ``dev``.

Ceci fonctionne bien si les développements sont de bonne qualité, donc avec peu de correctifs sur la branche de *release* (idéalement aucun !)… les codes approximatifs et non testés seront donc refusés.

Rôles et Responsabilités
========================

Le projet Zeste de Savoir est dirigé par sa communauté. Ensuite les développeurs prennent en main l'aspect technique.
On distingue cependant deux rôles particuliers au sein de l'équipe de développement.
Voici leurs noms ainsi que leurs tâches :

Le Maintainer (M)
-----------------

  - Suivi des éventuels bugs et suggestions remontés sur le forum
  - Écriture d'un *changelog* incluant les instructions de déploiement et les tests à effectuer en bêta
  - Confirmer les choix techniques
  - Trancher les choix techniques qui ne sont pas évidents
  - S'assurer que les tickets vivent leur vie (tags par exemple)
  - Marquer les tickets comme bloquants et donner des coups de fouet pour qu'ils soient fermés
  - S'assurer que les PR s'écoulent et se débloquent
  - Gérer les tensions entre devs/membres si nécessaire
  - Gérer la "vie de l'équipe" et sa logistique (droits github…)

Le Release Manager (RM)
-----------------------

  - Roles

    - Gestion de la branche de production du dépôt
    - Mise en bêta puis mise en production
    - Gérer et monitorer l'infra (configuration des logiciels, logs, sécurité) [pré]prod'
    - Donner un avis sur les contraintes de changement de serveur (ou prévenir sur les limites de l'actuel quand nécessaire, cf. premier point)
    - Suivre les tickets "infra" sur GH et faire les actions nécessaires
    - Gérer les personnes ayant accès au serveur [pré]prod'
    - Maintenir de la doc. sur les actions pour faire un suivi et assurer la relève/remplacement quand c'est nécessaire (maladie, vacances…)

  - Responsabilités

    - **Confidentialité** vis-a-vis des données privées présente sur les serveurs (email, contenu de MP…)
    - Si possible, toujours tester en preprod' avant de reproduire en prod'
    - **Professionnalisme**, "si on sait pas on fait pas" pour ne pas mettre la production en péril (sauf en preprod entre les releases)
  

Chacun de ces postes est occupé par une personne différente (idéalement) qui aura été choisi parmi les développeurs et pour qui l'association Zeste de Savoir a donné son approbation (en raison du caractère confidentiel de certaines données).

Glossaire
=========

-  **MEP** : Mise En Production
-  **PR** : *Pull Request* (proposition d'une modification de code à un projet)
-  **QA** : *Quality Assurance* (`Assurance Qualité <https://fr.wikipedia.org/wiki/Assurance_qualit%C3%A9>`_)
-  **CR** : *Code Review* (`Revue de code <https://fr.wikipedia.org/wiki/Revue_de_code>`_)
