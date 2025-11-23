Dans une application MVC web, le coeur de notre application, c'est le contrôleur. Il a pour rôle d'appliquer la logique de notre application et d'afficher les résultats.

La logique, c'est l'ensemble des étapes que vous voulez réaliser pour que votre site fonctionne.

Principalement, le contrôleur va converser avec votre modèle.
Le modèle, c'est un ensemble de classes qui représentent les données manipulées par votre application.
Très souvent, le modèle est accompagné par une couche appelée DAL ou "couche d'accès aux données". C'est cette couche qui accèdera à votre base de données par exemple. Elle fera l'objet de la partie IV.

Ce qu'il faut comprendre, c'est qu'a priori, le contrôleur ne suppose pas l'utilisation d'une base de données.
Vous pouvez faire pleins de calculs uniquement à partir de données contenues dans les sessions, les formulaires, ou les url.
