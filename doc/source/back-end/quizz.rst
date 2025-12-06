===============================
Ajout de Quizz à Zest de savoir
===============================

Zeste de savoir est capable de présenter des quizz à l'utilisateur. La philosophie qui a été retenue est :

- L'auteur écrit la **correction** du quizz dans un extrait qui est marqué comme étant un quizz.
- Lorsque le tutoriel est publié, côté client, un script parcourt cette correction et la transforme en formulaire.
- Une fois que le lecteur a rempli son quizz, la correction est automatiquement calculée et rendue au lecteur.
- Des statistiques sont alors envoyées à l'auteur pour qu'il voit où sont les erreurs de chacun.

L'ajout de quizz n'est pas une mince affaire dans notre code d'autant qu'il est important de les rendre **faciles** à rédiger.
En effet, rédiger sur ZDS demande pas mal d'effort et l'ajout de quizz avec les méthodes habituelles à base
de formulaires spécifiques, qui permettent de "configurer le rendu" de la question est peu pertinent.

La première version du module de quizz permet d'ajouter des QCM mais a été conçue pour permettre l'ajout d'autres types de réponse.

Liens avec ZMarkdown
====================

Le module des quizz nécessite ZMarkdown 9 pour être fonctionnel sur la version web et ZMarkdown 10 pour être proprement exporté en PDF.
Les epub affichent uniquement la correction pour l'instant.

Utiliser Zmarkdown > 10
-----------------------

Avec l'utilisation de zmarkdown > 10 vous pouvez utiliser le bloc ``[[quizz | Intitulé de la question]]``.
Ce bloc a le même comportement que le bloc neutre. Cependant il permet d'ajouter des informations de contexte nécessaires à l'export Latex.
De même on devrait pouvoir tirer partie du fait que ce bloc a une classe précise dans les implémentations des futurs types de questions.

Ajouter des types de questions
------------------------------

Globalement, l'ajout de type de questions, disons "texte libre" pour l'exemple se décompose en trois parties :

- Décider de quelle syntaxe Markdown on tirera partie pour définir la correction. Imaginons ici qu'on utilise la syntaxe des codes inlines (deux `````)
- Implémenter dans zMarkdown un préprocesseur de ``quizzCustomBlock`` qui permettra de remplacer les ``inlineCode`` par un texte composé de ``______`` dans le quizz et les laissera intacts dans la correction
- Adapter ``content_quizz.js`` et ``statistics.py`` pour que la correction se fasse et que les statistiques remontent

Comportement attendu des quiz
=============================

- Les quiz peuvent être créés dans les tutoriels.
- Dans une session, un utilisateur non connecté ne peut répondre qu’une seule fois à un quiz
- Un utilisateur connecté peut répondre plusieurs fois à un quiz
- Le propriétaire du quiz et le staff ont accès à une page contenant les statistiques (nombre de réponses à chaque question)
- Le propriétaire et le staff ont la possibilité de réinitialiser les statistiques de chaque quiz et de chaque question d’un quiz indépendamment à l’aide d’un bouton 
- Une question de quiz contient au moins une bonne réponse (pas de test) 
- Une question quiz doit avoir une explication qui s’affiche lorsqu'il répond au quiz
- Lors de la modification du tutoriel, les statistiques doivent rester cohérentes avec les quiz qui sont encore présents dans le tutoriel
- Lors d’une bonne réponse, la couleur de fond passe en vert, en orange pour une bonne réponse partielle (ex : une des deux bonnes réponses a été choisie mais pas l’autre). Enfin rouge pour une mauvaise réponse.

Comment créer un quiz
=====================

la Création d’un quiz se fait directement en zmarkdown de la façon suivante : 

[[quizz | la question1]]
| - [ ] réponse 1
| - [x] bonne réponse
| - [ ] réponse 2
| - réponse 2 est correcte, car Elle est correcte

[[quizz | la question2]]
| - [x] réponse 1
| - [x] bonne réponse
| - [ ] réponse 2
| - réponse 1 et 2 sont correcte car Elle sont bonnes

Contenu du fichier
==================

Variables globales
------------------

- answers: un objet vide qui contiendra les réponses des utilisateurs aux questions du quizz.
- idCounter: un compteur pour générer des identifiants uniques pour chaque question du quizz.
- idBias: une valeur qui sert à décaler la numérotation des questions du quizz en cas de suppression d'une question.

Fonctions
---------

- initializePipeline(answers): une fonction qui initialise une série de fonctions pour traiter les réponses des utilisateurs.
- injectForms(div, answers): une fonction qui ajoute les éléments de formulaire pour les questions du quizz à un élément de la page HTML.
- sendQuizzStatistics(form, statistics): une fonction qui envoie les statistiques de la réponse du quizz à un serveur à l'aide d'une requête XMLHttpRequest.
- displayResultAfterSubmitButton(form): une fonction qui affiche la réponse correcte pour chaque question du quizz après que l'utilisateur a soumis ses réponses.
- QuizzAnswered(form): une fonction qui teste si toutes les questions du quizz ont une réponse.
- iconMaker(isGood): une fonction qui crée un élément d'icône avec l'icône "check" ou "exclamation-triangle" de Font Awesome en fonction de si la réponse de l'utilisateur est correcte ou non.
- getQuestionText(question): une fonction qui retourne le texte de la question.
- getAnswerText(liWrapper): une fonction qui retourne le texte de la réponse.
- computeForm(formData, answers): une fonction qui compare les réponses de l'utilisateur avec les réponses attendues et retourne une liste des réponses incorrectes et une liste de toutes les réponses.
- markBadAnswers(form, badAnswerNames, answers): une fonction qui marque les réponses incorrectes pour chaque question du quizz.

Événements
----------

- 'submit' pour chaque formulaire de quizz: lorsque l'utilisateur soumet ses réponses, le code traite les réponses et envoie les statistiques à un serveur.

Sélectionneurs DOM (Document Object Model) 
------------------------------------------

- document.querySelectorAll('div.quizz'): sélectionne tous les éléments HTML avec la classe quizz qui contiennent des questions de quizz.
- document.querySelectorAll('form.quizz'): sélectionne tous les éléments HTML avec la classe quizz qui sont des formulaires de quizz.


Base de données 
===============

Représentation en base de donnée des quiz
-----------------------------------------

- Le modèle QuizzQuestion contient les champs pour stocker une URL, la question et le type de question. Le type de question est un champ de texte avec une taille maximale de 15 caractères et une valeur par défaut de "qcm".
- Le modèle QuizzAvailableAnswer contient les champs pour stocker le libellé de la réponse, un indicateur pour savoir si c'est la bonne réponse, et une clé étrangère pour lier la réponse à la question correspondante dans le modèle QuizzQuestion.
- Le modèle QuizzUserAnswer contient les champs pour stocker une réponse donnée par l'utilisateur, la date de la réponse, et des clés étrangères pour lier la réponse à la question correspondante dans le modèle QuizzQuestion et au contenu publié associé.

Commentaires sur les factories
------------------------------

- La classe QuizzQuestionFactory utilise la bibliothèque Python faker pour générer une URL, une question et un type de questions aléatoires. Le type de question est choisi parmi une liste de valeurs possibles ('qcm', 'open', 'bool').
- La classe QuizzAvailableAnswerFactory génère des réponses possibles à une question de quiz. Elle utilise également faker pour générer une étiquette de réponse et un booléen pour indiquer si la réponse est correcte ou non. La clé étrangère related_question est une sous-factory qui crée une instance de QuizzQuestion.
- La classe QuizzUserAnswerFactory génère des réponses d'utilisateurs à des questions de quiz. Elle utilise une sous-factory pour créer une instance de PublishableContentFactory, un champ de réponse aléatoire et une clé étrangère related_question qui est une sous-factory pour créer une instance de QuizzQuestion. Le champ full_answer_id est généré à l'aide de faker pour simuler un identifiant unique.


Commentaires sur les tests
--------------------------

- test_question_count() : vérifie que deux questions ont été créées dans la base de données.
- test_answer_count() : vérifie que quatre réponses ont été créées dans la base de données.
- test_user_answer_count() : vérifie que deux réponses d'utilisateur ont été créées dans la base de données.
- test_related_user_answers() : vérifie que les réponses d'utilisateur sont bien liées aux bonnes questions.
- test_related_answers() : vérifie que les réponses disponibles sont bien liées aux bonnes questions.
- test_answer_is_good() : vérifie qu'au moins une réponse disponible pour chaque question est marquée comme bonne.
- test_user_answer_unique_id() : vérifie que chaque réponse d'utilisateur a un ID unique.
- test_nb_good_answers() : vérifie qu'il y a bien 2 bonnes et 2 mauvaises réponses pour une question qui a plusieurs réponses possibles.