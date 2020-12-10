==================================================
Intégration du reformatage du code Python avec Git
==================================================

Pour la mise en forme du code Python, le projet Zeste de Savoir
utilise l'outil `black`. Cet outil permet de :

- formater le code Python selon certaines règles ;
- vérifier qu'un code Python est bien formaté selon ces mêmes règles.

Pour éviter aux développeurs d'oublier de formater le code, un
*pre-commit hook* qui exécute `black` avant chaque *commit* est
installé avec le *backend*. Vous n'avez normalement
rien à configurer pour en bénéficier.

Si vous tentez de commiter du code mal formaté, le code sera
reformaté automatiquement et le *commit* interrompu. Il vous suffira
alors de recommencer en incluant ces modifications pour que tout se passe
sans problème.

Ce *hook* permet d'éviter de corriger *a posteriori* les erreurs
de formatage relevées par les outils d'intégration continue, qui
refusent tout code ne respectant pas ces règles.
