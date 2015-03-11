==========
*Workflow*
==========

Cette page détaille le *workflow* utilisé sur Zeste de Savoir. Elle est là surtout pour satisfaire votre curiosité, à moins d'avoir les droits de faire une Mise En Production (MEP). La `page de contribution <https://github.com/zestedesavoir/zds-site/blob/dev/CONTRIBUTING.md>`__ devrait répondre à vos questions quant au processus de développement.

Ce *workflow* est très fortement fondé sur le `Git flow <http://nvie.com/posts/a-successful-git-branching-model/>`__.

*Workflow* général
==================

L'idée générale est très simple :

-  Le développement se fait sur la branche ``dev`` ;
-  La branche ``prod`` contient la version en production ;
-  Lorsqu'on juge qu'on a assez de matière pour un nouveau déploiement, on crée une branche dédiée (par exemple ``release-v1.7``) que l'on teste en pré-production (les bugs trouvés seront corrigés sur cette branche) ;
-  En cas de bug ultra-urgent à corriger en production, on crée une branche spéciale.

La pré-production (ou béta) est disponible via `ce lien <https://beta.zestedesavoir.com>`_. Vous pouvez y accéder avec le nom d'utilisateur "clementine" et le mot de passe "souris".

*Workflow* de développement
===========================

Description
-----------

1. Les fonctionnalités et corrections de bugs se font via des *Pull Requests* (PR) depuis des *forks* via `GitHub <https://github.com/zestedesavoir.com/zds-site>`_.
2. Ces PR sont unitaires. Aucune PR qui corrige plusieurs problèmes ou apporte plusieurs fonctionnalité ne sera acceptée ; la règle est : une fonctionnalité ou une correction = une PR.
3. Ces PR sont mergées dans la branche ``dev`` (appelée ``develop`` dans le git flow standard), après une *Quality Assurance* (QA) légère.
4. La branche ``prod`` (appelée ``master`` dans le git flow standard) contient exclusivement le code en production, pas la peine d'essayer de faire le moindre *commit* dessus !
5. Les branches du dépôt principal (``dev``, ``prod`` et la branche de release) ne devraient contenir que des merge de PR, aucun commit direct.

Quelques précisions
-------------------

**Où peut-on trouver les détails pratiques ?**

Tous ces détails sont `dans la page de contribution <https://github.com/zestedesavoir/zds-site/blob/dev/CONTRIBUTING.md>`__. On y trouve entre autres les recommendations en terme de PR ou de messages de commits.

**Qu'est-ce qu'une "QA légère"** ?

C'est s'assurer que le code fait ce qu'il devrait sans passer des heures à re-tester l'intégralité du site. Concrètement, cela implique :

-  une revue de code ;
-  la vérification que des tests correspondants à la fonctionnalité ou à la correction sont présents, cohérents et passent ;
-  des tests manuels dans le cas de fonctionnalités ou corrections complexes et/ou critiques (au cas par cas).

*Workflow* de mise en production
================================

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

Le temps maximum entre la création d'une branche de *release* et sa mise en production est de **deux semaines**. Au-delà on considère qu'il y a trop de problèmes et qu'ils risquent de bloquer le développement :

1. Merge des corrections de la branche de *release* dans ``dev``
2. Pas de mise en production
3. Suppression de la branche de *release*, devenue inutile

En cas de problèmes sur la release
----------------------------------

Vous l'avez lu : les corrections de ``master`` **ne sont pas remontées sur ``dev``** au fur et à mesure. La raison est que ça prends du temps, de l'énergie et que ça fait beaucoup de merges croisés. Donc toutes les corrections sont remontées en même temps lors de la mise en production. Conséquences :

-  Si vous bossez sur ``dev`` pendant qu'une *release* est en cours, pas la peine de corriger un bug déjà corrigé sur la *release* : la PR serait refusée (pour cause de doublon).
-  Si un *gros* problème est détecté sur la *release* et qu'il est correctible en un temps raisonnable :

   1. Il est corrigé sur la branche de *release*.
   2. Les merges de PR sur ``dev`` qui impliquent un risque même vague de conflit sont bloqués.
   3. S'il y a quand même un conflit (à cause d'une PR mergée sur ``dev`` avant la détection du problème), la personne qui règle le problème fournit 2 correctifs : un pour la branche de *release* et un pour la branche de de ``dev``.

Ceci fonctionne bien si les développements sont de bonne qualité, donc avec peu de correctifs sur la branche de *release* (idéalement aucun !)... les codes approximatifs et non testés seront donc refusés sans la moindre pitié !

Glossaire
=========

-  **MEP** : Mise En Production
-  **PR** : *Pull Request* (proposition d'une modification de code à un projet)
-  **QA** : *Quality Assurance* (`Assurance Qualité <https://fr.wikipedia.org/wiki/Assurance_qualit%C3%A9>`_) 
