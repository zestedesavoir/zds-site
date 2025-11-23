Dans une application MVC, le contrôleur a pour rôle principal de contenir toute la **logique** de votre application.

La logique, c'est l'ensemble des étapes que vous voulez réaliser pour que votre site fonctionne.

Principalement, le contrôleur va converser avec votre **modèle**. Le modèle, c'est un ensemble de classes qui représentent les données manipulées par votre application.
Très souvent, le modèle est accompagné par une *couche* appelée DAL. C'est cette couche qui accèdera à votre base de données par exemple. Elle fera l'objet de la partie IV.

Ce qu'il faut comprendre, c'est qu'a priori, le contrôleur ne suppose pas l'utilisation d'une base de données. Vous pouvez faire pleins de calculs uniquement à partir de données contenues dans les sessions, les formulaires, ou les url.



*[DAL]: Data Access Layer
