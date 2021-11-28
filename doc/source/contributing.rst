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
4. Assurez-vous que vos tests passent en utilisant la commande ``make test-back`` (voyez la `page dédiée <./guides/backend-tests.html>`_ pour plus de détails). Lancer la commande sur tous les tests du site risque de prendre un certain temps et n'est pas nécessaire : les tests seront de toute manière lancés de manière automatisée sur votre *pull request*.
5. Si vous avez modifié les modèles (les fichiers ``models.py``), n'oubliez pas de créer les fichiers de migration : ``python manage.py makemigrations``.
6. Poussez votre travail et faites une *pull request*.
7. Si votre travail nécessite des actions spécifiques lors du déploiement, précisez-les dans le corps de votre *pull request*. Elles seront ajoutées au *changelog* par le mainteneur qui effectuera le *merge*.

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

Les Pull Requests
=================

Lors de l'ouverture d'une PR, la zone de texte sera pré-complété avec les informations essentielles à apporter à votre PR. Utilisez ce gabarit pour rédiger votre message.

| Ajoutez des notes de QA (Quality Assurance). Ces notes doivent permettent à un testeur de comprendre ce que vous avez modifié, ce qu'il faut tester en priorité et les pièges auxquels il doit s'attendre et donc sur lesquels porter une attention particulière.
| Précisez tout particulièrement s'il est nécessaire d'effectuer une action de gestion préalable, comme ``python manage.py migrate --fake-initial``, ``python manage.py loaddata fixture/*.yaml`` ou ``yarn run build``.

Mise à jour d'une Pull Request : *rebase*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Au fil de l'avancement de votre PR, ou juste avant de la fusionner, il peut vous être demandé de *rebaser* (ou *rebase*). Cela permet de mettre à jour la branche de votre PR avec la toute dernière version de la branche principale du dépôt.

C'est une opération assez simple, et très utile pour s'assurer que votre modification s'intègre toujours bien avec la toute dernière version du site (si d'autres contributeurs ont changé quelque chose, typiquement). Elle a l'avantage, par rapport à une classique fusion (``git merge``), d'intégrer les commits naturellement dans l'historique, sans en ajouter de supplémentaire inutile.

Pour *rebase* en ligne de commande, utilisez la commande ``git pull --rebase upstream dev`` (c'est tout). Si vous utilisez une interface graphique pour git, la marche à suivre dépendra de cette interface.

.. warning::

  Si git vous informe qu'il y a **des conflits** lors du *rebase*, cela signifie que des parties du code ont été modifiées à la fois par les autres contributeurs et par vous-même. Pas de panique ! Corriger un conflit est assez simple. Git va, pour chaque conflit, vous montrer votre version et la version des autres contributeurs côte à côte dans le fichier concerné, et ce sera à vous de décider ce que vous gardez (votre version, celle des autres, ou un savant mélange des deux). Concrètement, pour chacun des fichiers que git indique comme en conflit, vous devez :

  1. ouvrir le fichier, chercher les marques qu'a laissé git à l'intérieur, et résoudre le conflit en choisissant quel bout garder (tout en retirant les marques de conflit de git — à la fin, le fichier doit être “normal”, comme si git n'était jamais passé par là) ;
  2. marquer les conflits du fichier comme corrigés (``git add <path>`` en ligne de commande, et probablement quelque chose comme “Marquer comme résolu” en GUI) ;
  3. continuer le *rebase* (``git rebase --continue`` en ligne de commande, “Continuer le rebase” ou similaire en GUI).

Vous devez ensuite publier sur GitHub avec un **force-push** (``git push --force``), car *rebase* réécrit l'historique (si vous oubliez, vous obtiendrez une erreur et git refusera l'opération). Ça ne pose aucun problème ici — c'est l'un des cas d'usage légitime du *force-push*, et vous ne le faites que sur votre propre branche.

.. note::

  Pour pouvoir *rebaser*, il vous faut avoir défini une *remote* ``upstream`` pointant vers le dépôt principal de ZdS (la *remote* ``origin`` devant pointer vers votre fork), de la façon suivante : ``git remote add upstream https://github.com/zestedesavoir/zds-site.git``.

  Cette opération n'est nécessaire qu'une seule fois au début, pour tous les *rebases* que vous ferez sur votre fork.

Il est également possible de mettre la branche à jour sur GitHub en bas de la page de la PR, mais GitHub créé un commit de fusion sans faire de *rebase*.

Les commits
===========

Pour les commits, nous suivons le même ordre d'idée que les standards Git.

* La première ligne du commit ne doit pas faire plus de 50 caractères.
* Si besoin, complétez votre commit via des commentaires, en respectant une limite de 70 caractères par ligne.
* Bien que le code soit en anglais, le commit doit être de préférence en français.
* Vous pouvez également (c'est d'ailleurs conseillé) référencer l'*issue* que vous corrigez.
* Un commit doit être atomique ; il fixe / implémente **une** chose et le fait **bien**.

N'hésitez pas à demander de l'aide, et bon courage !
