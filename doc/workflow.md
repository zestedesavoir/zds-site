Cette page d�taille le _workflow_ utilis� sur Zeste de Savoir. Elle est l� surtout pour satisfaire votre curiosit�, � moins d'avoir les droits de faire une Mise En Production (MEP). La [page de contribution](CONTRIBUTING.md) devrait r�pondre � vos questions quant au processus de d�veloppement.

Ce _workflow_ est tr�s fortement bas� sur le [Git flow](http://nvie.com/posts/a-successful-git-branching-model/).

# _Workflow_ g�n�ral

L'id�e g�n�rale est tr�s simple :

- Le d�veloppement se fait sur la branche `dev`
- La branche `prod` contient la version en production
- Lorsqu'on juge qu'on a assez de mati�re pour un nouveau d�ploiement, on cr�e une branche d�di�e (par exemple `release-v1.7`), qui est test�e en pr�-production et corrig�e sur cette branche
- En cas de bug ultra-urgent � corriger en production, on cr�e une branche sp�ciale

# _Workflow_ de d�veloppement

## Description

1. Les arriv�es fonctionnalit�s et corrections de gros bugs se font via des _Pull Requests_ (PR) depuis des _forks_.
1. Ces PR sont unitaires. Aucune PR qui corrige plusieurs probl�mes ou apporte plusieurs fonctionnalit� ne sera accept� ; la r�gle est : une fonctionnalit� ou une correction = une PR.
1. Ces PR sont merg�es dans la branche `dev` (appel�e `develop` dans le git flow standard), apr�s une _Quality Assurance_ (QA) l�g�re. `dev` ne devrait contenir que des merge de PR, aucun commit direct.
1. La branche `prod` (appel�e `master` dans le git flow standard) contient exclusivement le code en production, pas la peine d'essayer de faire le moindre _commit_ dessus !

## Quelques pr�cisions

**O� peut-on trouver les d�tails pratiques ?**

Tous ces d�tails sont [dans la page de contribution](CONTRIBUTING.md). On y trouve entre autres les recommendations en terme de PR ou de messages de commits.

**Qu'est-ce qu'une "QA l�g�re"** ?

C'est s'assurer que le code fait ce qu'il devrait sans passer des heures � re-tester l'int�gralit� du site. Concr�tement, cela implique :

- Une revue de code
- La v�rification que des tests correspondants � la fonctionnalit� ou � la correction sont pr�sents, coh�rents et passent
- Des tests manuels dans le cas de fonctionnalit�s ou corrections complexes et/ou critiques (au cas par cas)

# _Workflow_ de mise en production

## Description

1. Quand on a assez de nouveaut�s dans `dev` (mais pas trop), on d�cide de faire une _release_. L'id�e est de pouvoir v�rifier et corriger les probl�mes de cette _release_ rapidement, en moins de 2 semaines entre le lancement de la release et sa MEP.
    1. Cr�ation d'une **nouvelle branche de release** du nom de la version (par exemple `release-v1.7`)
	1. D�ploiement de cette branche sur l'environnement de pr�-production, avec un _dump_ de donn�es de production
	1. Tests les plus complets possibles sur ce nouvel environnement
	1. Corrections �ventuelles sur cette branche de _release_. Les corrections **ne sont pas remont�es sur `dev`** au fur et � mesure. Cf ci-dessous pour les d�tails.
1. Lorsqu'on a bien test� cette branche, on la met en production :
	1. Merge de la branche de _release_ dans `dev`
	1. Merge de la branche de _release_ dans `prod`
	1. Tag avec la nouvelle version
	1. Mise en production sur le serveur
	1. Suppression de la branche de _release_, devenue inutile
	
Le temps maximum entre la cr�ation d'une branche de _release_ et sa mise en production est de **deux semaines**. Au-del� on consid�re qu'il y a trop de probl�mes et qu'ils risquent de bloquer le d�veloppement :

1. Merge des corrections de la branche de _release_ dans `dev`
1. Pas de mise en production
1. Suppression de la branche de _release_, devenue inutile

## En cas de probl�mes sur la release

Vous l'avez lu : les corrections de `master` **ne sont pas remont�es sur `dev`** au fur et � mesure. La raison est que �a prends du temps, de l'�nergie et que �a fait beaucoup de merges crois�s. Donc toutes les corrections sont remont�es en m�me temps lors de la mise en production. Cons�quences :

- Si vous bossez sur `dev` pendant qu'une _release_ est en cours, pas la peine de corriger un bug d�j� corrig� sur la _release_ : la PR serait refus�e (pour cause de doublon).
- Si un _gros_ probl�me est d�tect� sur la _release_ et qu'il est correctible en un temps raisonnable :
	1. Il est corrig� sur la branche de _release_.
	1. Les merges de PR sur `dev` qui impliquent un risque m�me vague de conflit sont bloqu�s.
	1. S'il y a quand m�me un conflit (� cause d'une PR merg�e sur `dev` avant la d�tection du probl�me), la personne qui r�gle le probl�me fournit 2 correctifs : un pour la branche de _release_ et un pour la branche de de `dev`.
	
Ceci fonctionne bien si les d�veloppements sont de bonne qualit�, donc avec peu de correctifs sur la branche de _release_ (id�alement aucun !)... les codes approximatifs et non test�s seront donc refus�s sans la moindre piti� !

# Glossaire

- **MEP** : Mise En Production
- **PR** : _Pull Request_
- **QA** : _Quality Assurance_