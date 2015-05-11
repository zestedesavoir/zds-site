==================================
Présentation de l'environnement de travail
==================================

L'environnement de travail est constitué par… :

-Les sources de Zeste de Savoir,

-Un serveur Python,

-Un environnement virtuel* qui contient le serveur précédemment cité.

*: notion expliquée ci-dessous.

Les sources sont bien évidemment les fichiers que vous ouvrirez, créerez, modifierez ou supprimerez pour apporter des
corrections de bugs, pour développer des fonctionnalités ou encore pour les tester.

Le serveur Python est utilisé pour tester le résultat de ces différentes opérations (donc pour utiliser le site Web
Zeste de Savoir en local sur votre machine).

L'environnement virtuel contient les paquets logiciels (exclusivement Python) à installer pour que le serveur
Python puisse fonctionner correctement (on parle de « dépendances » car le bon fonctionnement du serveur
Python dépend (!) de l'installation de ces paquets). Au lieu d'installer ces paquets directement dans votre
distribution, vous les installerez dans cet environnement virtuel (qui fait partie de la distribution). Ainsi,
la distribution n'accueillera pas ces paquets, ce qui évite de la polluer. Autre point important pour bien comprendre
la notion d'environnement virtuel : il y a un environnement virtuel par projet (un projet, c'est par exemple Zeste de
Savoir). Cela permet d'utiliser telle version de chaque paquet pour tel projet, et telle autre version de chaque paquet
pour tel autre projet. Chaque projet peut donc utiliser telle ou telle version de chaque paquet. Enfin, notons que
l'environnement virtuel contient le serveur Python : c'est un paquet logiciel comme un autre.


Pour installer l'environnement de travail, consultez les parties "Installation back-end" et "Installation front-end".
