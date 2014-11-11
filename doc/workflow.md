Cette page détaille le _workflow_ utilisé sur Zeste de Savoir. Elle est là surtout pour satisfaire votre curiosité, à moins d'avoir les droits de faire une Mise En Production (MEP). La [page de contribution](../CONTRIBUTING.md) devrait répondre à vos questions quant au processus de développement.

Ce _workflow_ est très fortement basé sur le [Git flow](http://nvie.com/posts/a-successful-git-branching-model/).

# _Workflow_ général

L'idée générale est très simple :

- Le développement se fait sur la branche `dev`
- La branche `prod` contient la version en production
- Lorsqu'on juge qu'on a assez de matière pour un nouveau déploiement, on crée une branche dédiée (par exemple `release-v1.7`), qui est testée en pré-production et corrigée sur cette branche
- En cas de bug ultra-urgent à corriger en production, on crée une branche spéciale

# _Workflow_ de développement

## Description

1. Les arrivées fonctionnalités et corrections de gros bugs se font via des _Pull Requests_ (PR) depuis des _forks_.
2. Ces PR sont unitaires. Aucune PR qui corrige plusieurs problèmes ou apporte plusieurs fonctionnalité ne sera accepté ; la règle est : une fonctionnalité ou une correction = une PR.
3. Ces PR sont mergées dans la branche `dev` (appelée `develop` dans le git flow standard), après une _Quality Assurance_ (QA) légère.
4. La branche `prod` (appelée `master` dans le git flow standard) contient exclusivement le code en production, pas la peine d'essayer de faire le moindre _commit_ dessus !
5. Les branches du dépôt principal (`dev`, `prod` et la branche de release) ne devraient contenir que des merge de PR, aucun commit direct.

## Quelques précisions

**Où peut-on trouver les détails pratiques ?**

Tous ces détails sont [dans la page de contribution](../CONTRIBUTING.md). On y trouve entre autres les recommendations en terme de PR ou de messages de commits.

**Qu'est-ce qu'une "QA légère"** ?

C'est s'assurer que le code fait ce qu'il devrait sans passer des heures à re-tester l'intégralité du site. Concrètement, cela implique :

- Une revue de code
- La vérification que des tests correspondants à la fonctionnalité ou à la correction sont présents, cohérents et passent
- Des tests manuels dans le cas de fonctionnalités ou corrections complexes et/ou critiques (au cas par cas)

# _Workflow_ de mise en production

## Description

1. Quand on a assez de nouveautés dans `dev` (mais pas trop), on décide de faire une _release_. L'idée est de pouvoir vérifier et corriger les problèmes de cette _release_ rapidement, en moins de 2 semaines entre le lancement de la release et sa MEP.
    1. Création d'une **nouvelle branche de release** du nom de la version (par exemple `release-v1.7`)
	2. Déploiement de cette branche sur l'environnement de pré-production, avec un _dump_ de données de production
	3. Tests les plus complets possibles sur ce nouvel environnement
	4. Corrections éventuelles sur cette branche de _release_. Les corrections **ne sont pas remontées sur `dev`** au fur et à mesure. Cf ci-dessous pour les détails.
2. Lorsqu'on a bien testé cette branche, on la met en production :
	1. Merge de la branche de _release_ dans `dev`
	2. Merge de la branche de _release_ dans `prod`
	3. Tag avec la nouvelle version
	4. Mise en production sur le serveur
	5. Suppression de la branche de _release_, devenue inutile
	
Le temps maximum entre la création d'une branche de _release_ et sa mise en production est de **deux semaines**. Au-delà on considère qu'il y a trop de problèmes et qu'ils risquent de bloquer le développement :

1. Merge des corrections de la branche de _release_ dans `dev`
2. Pas de mise en production
3. Suppression de la branche de _release_, devenue inutile

## En cas de problèmes sur la release

Vous l'avez lu : les corrections de `master` **ne sont pas remontées sur `dev`** au fur et à mesure. La raison est que ça prends du temps, de l'énergie et que ça fait beaucoup de merges croisés. Donc toutes les corrections sont remontées en même temps lors de la mise en production. Conséquences :

- Si vous bossez sur `dev` pendant qu'une _release_ est en cours, pas la peine de corriger un bug déjà corrigé sur la _release_ : la PR serait refusée (pour cause de doublon).
- Si un _gros_ problème est détecté sur la _release_ et qu'il est correctible en un temps raisonnable :
	1. Il est corrigé sur la branche de _release_.
	2. Les merges de PR sur `dev` qui impliquent un risque même vague de conflit sont bloqués.
	3. S'il y a quand même un conflit (à cause d'une PR mergée sur `dev` avant la détection du problème), la personne qui règle le problème fournit 2 correctifs : un pour la branche de _release_ et un pour la branche de de `dev`.
	
Ceci fonctionne bien si les développements sont de bonne qualité, donc avec peu de correctifs sur la branche de _release_ (idéalement aucun !)... les codes approximatifs et non testés seront donc refusés sans la moindre pitié !

# Glossaire

- **MEP** : Mise En Production
- **PR** : _Pull Request_
- **QA** : _Quality Assurance_
