Les contributions externes sont les bienvenues !

# Avant de réaliser...

1. Vérifiez que vous avez [un compte Github](https://github.com/signup/free)
2. Créez votre _issue_ si elle n'existe pas
    * Vérifiez que vous avez la dernière version du code
    * Décrivez clairement votre problème, avec toutes les étapes pour le reproduire
3. **Attribuez-vous** votre _issue_. C'est important pour éviter de se marcher dessus. Si vous n'êtes pas dans l'organisation et donc que vous ne pouvez pas vous attribuer directement l'_issue_, il vous suffit d'ajouter un commentaire clair dans celle-ci (comme _"Je prends"_), et elle sera marquée comme "en cours").
4. _Forkez_ le dépôt
5. Installez l'environnement. Tout est dans le fichier README.md

# Contribuer à Zeste De Savoir

1. Créez une branche pour contenir votre travail
2. Faites vos modifications
3. Ajoutez un test pour votre modification. Seules les modifications de documentation et les réusinages n'ont pas besoin de nouveaux tests
4. Assurez-vous que l'intégralité des tests passent : `python manage.py test`
5. Poussez votre travail et faites une _pull request_

# Quelques bonnes pratiques

* Respectez [les conventions de code de Django](https://docs.djangoproject.com/en/1.6/internals/contributing/writing-code/coding-style/), ce qui inclut la [PEP 8 de Python](http://legacy.python.org/dev/peps/pep-0008/)
* Le code et les commentaires sont en anglais
* Le _workflow_ Git utilisé est le [git flow](http://nvie.com/posts/a-successful-git-branching-model/) :
    * Les contributions se font uniquement sur la branche `dev`
    * Pensez à préfixer vos branches selon l'objet de votre PR : `hotfix-XXX`, `feature-XXX`, etc.
    * La branche `master` contient exclusivement le code en production, pas la peine d'essayer de faire le moindre _commit_ dessus ! 
* Votre test doit échouer sans votre modification, et réussir avec
* Faites des messages de _commit_ clairs et en anglais
* Il n'y a aucune chance que votre _pull request_ soit acceptée sans son test associé

N'hésitez pas à demander de l'aide, et bon courage !
