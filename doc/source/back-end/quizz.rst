===============================
Ajout de Quizz à Zest de savoir
===============================

Zeste de savoir est capablede présenter des quizz à l'utilisateur. La philosophie qui a été retenue est :

- L'auteur écrit la **correction** du quizz dans un extrait qui est marqué comme étant un quizz.
- Lorsque le tutoriel est publié, côté client, un script parcourt cette correction et la transforme en formulaire.
- Une fois que le lecteur a rempli son quizz, la correction est automatiquement calculée et rendue au lecteur.
- Des statistiques sont alors envoyées à l'auteur pour qu'il voit où sont les erreurs de chacun.

L'ajout de quizz n'est pas une mince affaire dans notre code d'autant qu'il est important de les rendre **faciles** à rédiger.
En effet, rédiger sur ZDS demande pas mal d'effort et l'ajout de quizz avec les méthodes habituelles à base
de formulaires spéciiques, qui permettent de "configurer le rendu" de la question est peu pertinent.

La première version du module de quizz permet d'ajouter des QCM mais a été conçue pour permettre l'ajout d'autres types de réponse.

Liens avec ZMarkdown
====================

Le module des quizz nécessite ZMarkdown 9 pour être fonctionnel sur la version web et ZMarkdown 10 pour être proprement exporté en PDF.
Les epub affichent uniquement la correction pour l'instant.

Utiliser Zmarkdown > 10
-----------------------

Avec l'utilisation de zmarkdown > 10 vous pouvez utiliser le bloc ``[[quizz | Intitulé de la question]]``.
Ce bloc a le même comportement que le bloc neutre. Cependant il permet d'ajouter des informations de contexte nécessaire à l'export Latex.
De même on devrait pouvoir tirer partie du fait que ce bloc a une classe précise dans les implémentations des futurs types de questions.

Ajouter des types de questions
------------------------------

Globalement, l'ajout de type de questions, disons "texte libre" pour l'exemple se décompose en trois parties :

- Décider de quelle syntaxe Markdown on tirera partie pour déinir la correction. Imaginons ici qu'on utilise la syntaxe
des codes inlines (deux `)
- Implémenter dans zMarkdown un preprocessor de ``quizzCustomBlock`` qui permettra de remplacer les ``inlineCode`` par un texte
composé de ``______`` dans le quizz et les laissera intact dans la correction
- Adapter ``content_quizz.js`` et ``statistics.py`` pour que la correction se fasse et que les statistiques remontent

