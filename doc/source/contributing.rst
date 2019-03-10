============================
Contribuer à Zeste de Savoir
============================

Avant de commencer...
---------------------

1. Vérifiez que vous avez `un compte Github <https://github.com/signup/free>`_.
2. Créez le *ticket* correspondant à votre travail s'il n'existe pas. (Cette étape peut être omise pour des corrections mineures.)
    * Vérifiez que vous avez la dernière version du code.
    * Décrivez clairement votre problème, avec toutes les étapes pour le reproduire.
3. **Attribuez-vous** votre *ticket*. C'est important pour éviter de se marcher dessus. Si vous n'êtes pas dans l'organisation et donc que vous ne pouvez pas vous attribuer directement le *ticket*, ajoutez simplement un commentaire clair dans celui-ci (tel que *"Je prends"*).
4. *Forkez* le dépôt et installez l'environnement, `comme décrit ici <./install.html>`_.

Contribuer à Zeste De Savoir
----------------------------

1. Créez une branche pour contenir votre travail.
2. Faites vos modifications.
3. Ajoutez un test pour votre modification. Seules les modifications de documentation et les réusinages n'ont pas besoin de nouveaux tests.
4. Assurez-vous que vos tests passent en utilisant la commande ``python manage.py test`` (`voir la documentation <https://docs.djangoproject.com/fr/1.10/topics/testing/overview/#running-tests>`_). Lancer la commande sur tous les tests du site risque de prendre un certain temps et n'est pas nécessaire : les tests seront de toute manière lancés de manière automatisée sur votre *pull request*.
5. Assurez-vous que le code suit la `PEP-8 <http://legacy.python.org/dev/peps/pep-0008/>`_ : ``flake8``.
6. Si vous avez fait des modifications du _frontend_, jouez les tests associés : ``yarn test``.
7. Si vous modifiez les modèles (les fichiers ``models.py``), n'oubliez pas de créer les fichiers de migration : ``python manage.py makemigrations``.
8. Poussez votre travail et faites une *pull request*.
9. Si votre travail nécessite des actions spécifiques lors du déploiement, précisez-les dans le corps de votre *pull request*. Elles seront ajoutées au *changelog* par le mainteneur qui effectuera le *merge*.

Quelques bonnes pratiques
-------------------------

* Respectez `les conventions de code de Django <https://docs.djangoproject.com/en/2.1/internals/contributing/writing-code/coding-style/>`_, ce qui inclut la `PEP 8 de Python <http://legacy.python.org/dev/peps/pep-0008/>`_.
* Le code et les commentaires sont en anglais.
* Le *workflow* Git utilisé est le `Git flow <http://nvie.com/posts/a-successful-git-branching-model/>`_, qui est `détaillé ici <./workflow.html>`_. En résumé :
    * Les arrivées fonctionnalités et corrections de gros bugs hors release se font via des PR.
    * Ces PR sont unitaires. Aucune PR qui corrige plusieurs problèmes ou apporte plusieurs fonctionnalité ne sera accepté ; la règle est : une fonctionnalité ou une correction = une PR.
    * Ces PR sont mergées dans la branche ``dev`` (appelée ``develop`` dans le git flow standard), après une QA légère.
    * Pensez à préfixer vos branches selon l'objet de votre PR : ``hotfix-XXX``, ``feature-XXX``, etc.
    * La branche ``prod`` (appelée ``master`` dans le git flow standard) contient exclusivement le code en production, pas la peine d'essayer de faire le moindre *commit* dessus !
* Faites des messages de *commit* clairs et en français.
* Il n'y a aucune chance que votre *pull request* soit acceptée sans son test associé.
* Votre test doit échouer sans votre modification, et réussir avec.

Les bonnes pratiques pour les PR et les commits
-----------------------------------------------

Les pull requests
=================

* Lors de l'ouverture d'une PR, la zone de texte sera pré-complété avec les informations essentielles à apporter à votre PR. Utilisez ce gabarit pour rédiger votre message.
* Ajoutez des notes de QA (Quality Assurance). Ces notes doivent permettent à un testeur de comprendre ce que vous avez modifié, ce qu'il faut tester en priorité et les pièges auxquels il doit s'attendre et donc sur lesquels porter une attention particulière. Précisez tout particulièrement s'il est nécessaire d'effectuer une action de gestion préalable, comme `python manage.py migrate --fake-initial`, `python manage.py loaddata fixture/*.yaml` ou `yarn run build`.

Les commits
===========

* Pour les commits, nous suivons le même ordre d'idée des standards Git, à savoir :
    * La première ligne du commit ne doit pas faire plus de 50 caractères.
    * Si besoin, complétez votre commit via des commentaires, en respectant une limite de 70 caractères par ligne.
    * Bien que le code soit en anglais, le commit doit être de préférence en français.
    * Vous pouvez également (c'est d'ailleurs conseillé) de référencer l'_issue_ que vous fixez.
    * Un commit doit être atomique ; il fixe / implémente **une** chose et le fait **bien**.

* Essayez d'éviter les commits dits inutiles (``fix previous commit``, ...). Si vous en avez dans votre pull-request,
  un *squash* sera effectué lors du *merge*.

N'hésitez pas à demander de l'aide, et bon courage !
