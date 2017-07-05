Les contributions externes sont les bienvenues !

# Avant de réaliser...

1. Vérifiez que vous avez [un compte Github](https://github.com/signup/free).
2. Créez votre _issue_ si elle n'existe pas.
    * Vérifiez que vous avez la dernière version du code.
    * Décrivez clairement votre problème, avec toutes les étapes pour le reproduire.
3. **Attribuez-vous** votre _issue_. C'est important pour éviter de se marcher dessus. Si vous n'êtes pas dans l'organisation et donc que vous ne pouvez pas vous attribuer directement l'_issue_, il vous suffit d'ajouter un commentaire clair dans celle-ci (comme _"Je prends"_), et elle sera marquée comme "en cours").
4. _Forkez_ le dépôt.
5. Installez l'environnement. Tout est dans le fichier [README.md](README.md).

# Contribuer à Zeste De Savoir

1. Créez une branche pour contenir votre travail.
2. Faites vos modifications.
3. Ajoutez un test pour votre modification. Seules les modifications de documentation et les réusinages n'ont pas besoin de nouveaux tests.
4. Assurez-vous que l'intégralité des tests passent : `python manage.py test`.
5. Assurez-vous que le code suit la [PEP-8](http://legacy.python.org/dev/peps/pep-0008/) : `tox -e flake8`.
6. Si vous avez fait des modifications du _front_, jouez les tests associés : `npm test`.
7. Si vous modifiez le modèle (les fichiers models.py), n'oubliez pas de créer les fichiers de migration : `python manage.py makemigrations`.
8. Si votre travail nécessite des actions spécifiques lors du déploiement, précisez-les dans le fichier [update.md](update.md).
9. Poussez votre travail et faites une _pull request_.

# Quelques bonnes pratiques

* Respectez [les conventions de code de Django](https://docs.djangoproject.com/en/1.10/internals/contributing/writing-code/coding-style/), ce qui inclut la [PEP 8 de Python](http://legacy.python.org/dev/peps/pep-0008/).
* Le code et les commentaires sont en anglais.
* Le _workflow_ Git utilisé est le [Git flow](http://nvie.com/posts/a-successful-git-branching-model/). En détail :
    * Les arrivées fonctionnalités et corrections de gros bugs hors release se font via des PR.
    * Ces PR sont unitaires. Aucune PR qui corrige plusieurs problèmes ou apporte plusieurs fonctionnalité ne sera accepté ; la règle est : une fonctionnalité ou une correction = une PR.
    * Ces PR sont mergées dans la branche `dev` (appelée `develop` dans le git flow standard), après une QA légère.
    * Pensez à préfixer vos branches selon l'objet de votre PR : `hotfix-XXX`, `feature-XXX`, etc.
    * La branche `prod` (appelée `master` dans le git flow standard) contient exclusivement le code en production, pas la peine d'essayer de faire le moindre _commit_ dessus !

Tous les détails sur le workflow se trouvent [sur la page dédiée](http://zds-site.readthedocs.org/fr/latest/workflow.html).

* Votre test doit échouer sans votre modification, et réussir avec.
* Faites des messages de _commit_ clairs et en français.
* Il n'y a aucune chance que votre _pull request_ soit acceptée sans son test associé.

# Les bonnes pratiques pour les PR et les commits
## Les Pull-Requests

* Lors de l'ouverture d'une PR, respectez le template suivant :

    ```markdown
    | Q                             | R
    | ----------------------------- | -------------------------------------------
    | Correction de bugs ?          | [oui|non]
    | Nouvelle Fonctionnalité ?     | [oui|non]
    | Tickets (_issues_) concernés  | [Liste de tickets séparés par des virgules]
    ```
* Ajoutez des notes de QA (Quality Assurance). Ces notes doivent permettent à un testeur de comprendre ce que vous avez modifié, ce qu'il faut tester en priorité et les pièges auxquels il doit s'attendre et donc sur lesquels porter une attention particulière. Précisez tout particulièrement s'il est nécessaire d'effectuer une action de gestion préalable, comme `python manage.py migrate --fake-initial`, `python manage.py loaddata fixture/*.yaml` ou `npm run gulp -- build`.

## Les commits

* Pour les commits, nous suivons le même ordre d'idée des standards Git, à savoir :
    * La première ligne du commit ne doit pas faire plus de 50 caractères.
    * Si besoin, complétez votre commit via des commentaires, en respectant une limite de 70 caractères par ligne.
    * Bien que le code soit en anglais, le commit doit être de préférence en français.
    * Vous pouvez également (c'est d'ailleurs conseillé) de référencer l'_issue_ que vous fixez.
    * Un commit doit être atomique ; il fixe / implémente **une** chose et le fait **bien**.

* Essayez d'éviter les commits dits inutiles (`fix previous commit`, ...). Si vous en avez dans votre pull-request,
  on vous demandera probablement de faire un `squash` de vos commits.

N'hésitez pas à demander de l'aide, et bon courage !
