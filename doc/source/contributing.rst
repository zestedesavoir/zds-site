============================
Contribuer à Zeste de Savoir
============================

Cette page explique, brievement, la procédures pour contribuer à Zeste de Savoir.
En cas de problème, n'hésitez pas à demander de l'aide en ouvrant `un sujet sur le forum dédié <https://zestedesavoir.com/forums/sujet/nouveau/?forum=2>`__.

Avant de contribuer
-------------------

Pour contribuer, il est nécessaire de posséder `un compte GitHub <https://github.com/signup/free>`__.

Deux dépôts (*remotes*) sont en fait nécessaire :

+ Le premier sera le *remote* ``origin``, qui est la copie de Zeste de Savoir créée par le contributeur, et sur laquelle il a tout les droits ;
+ Le second est le *remote* ``upstream``, qui est la version officielle du dépôt, sur laquelle est basée le site.

Vous effectuez les modifications sur votre propore *remote* (``origin``). Une fois qu'elles sont prêtes, vous proposez une *Pull Request* (PR) sur le dépôt ``upstream``.

Pour créer le dépôt propre au contributeur, vous devez réaliser un *fork* du `dépot de Zeste de Savoir <https://github.com/zestedesavoir/zds-site>`__, en utilisant le bouton "Fork" en haut à droite de la page du dépôt.
Une copie du dépôt de Zeste de Savoir esr alors créée sur GitHub.

Il est possible d'effectuer certaines des actions présentées ci-dessous directement sur GitHub, mais souvent beaucoup plus simple de travailler en local, à l'aide de l'outil `git <https://git-scm.com/>`__.

Pour récupérer une version de votre dépôt, utilisez

.. sourcecode:: bash

    git clone https://github.com/<login>/zds-site

Une copie de votre dépôt est alors téléchargée. On rajoute ensuite le *remote* ``upstream`` grâce à:

.. sourcecode:: bash

    git remote add upstream https://github.com/zestedesavoir/zds-site

Cette seconde commande permet de télécharger en local une copie du dépôt officiel (sur laquelle toute modification sera basée).

Une fois ces opérations effectuées, vous pouvez passer `à l'installation des différents outils <./install.html>`__ nécessaires à l'exécution de Zeste de Savoir en local.

Pour contribuer
---------------

Une fois que vous avez trouvé une *issue* que vous aimeriez traiter dans `la liste des issues <https://github.com/zestedesavoir/zds-site/issues>`__, il est nécessaire de créer une nouvelle branche sur votre dépôt.

.. attention::

    **Attribuez-vous** votre *issue*. C'est important pour éviter de se marcher dessus. Si vous n'êtes pas dans l'organisation et donc que vous ne pouvez pas vous attribuer directement l'*issue*, il vous suffit d'ajouter un commentaire clair dans celle-ci (comme "Je prends"), et elle sera marquée comme "en cours".


On commence systématiquement par mettre à jour la copie locale de ``upstream``:

.. sourcecode:: bash

    git fetch upstream

On crée ensuite une branche qui contiendra les modifications:

.. sourcecode:: bash

    git checkout -b VOTRE_BRANCHE_LOCALE upstream/dev

Cette commande créer la branche ``VOTRE_BRANCHE_LOCALE``, qui est basée sur dernière version de Zeste de Savoir (la branche ``dev``).
C'est les modifications issues de cette branche qui seront ensuite proposées, donc vous pouvez créer autant de branches que nécéssaire.
Pensez à préfixer vos branches selon l'objet de votre PR : ``hotfix-XXX``, ``feature-XXX``, etc (ou XXX peut, par exemple, être le numéro de l'*issue*).

Chacune de vos modification doit s'accompagner d'un *commit*. Une des manières de faire est d'utiliser la commande ci-dessous:

.. sourcecode:: bash

    git commit -av

Cette commande ouvre un éditeur de texte, dans lequel vous indiquer le message de *commit*, c'est à dire un résumé de vos modifications. Faites des messages de *commit* **clairs** et si possible en français (voir les "bonnes pratiques" ci-dessous).

Une fois vos différentes modifications effectuées, envoyez le résultat de votre travail (vos différents *commits*) sur GitHub:

.. sourcecode:: bash

    git push origin VOTRE_BRANCHE_LOCALE


Quelques bonnes pratiques
-------------------------

+ Concernant les *commits*, nous suivons le même ordre d'idée des standards Git, à savoir :
    * La première ligne du commit ne doit pas faire plus de 50 caractères ;
    * Si besoin, complétez votre commit via des commentaires, en respectant une limite de 70 caractères par ligne ;
    * Bien que le code soit en anglais, le commit doit être de préférence en français ;
    * Vous pouvez également (c'est d'ailleurs conseillé) de référencer l'*issue* que vous fixez ;
    * Un commit doit être atomique ; il fixe / implémente **une** chose et le fait **bien**.
+ Le code et les commentaires doivent être rédigés en anglais.
+ N'hésitez pas à rajouter des `docstrings (PEP 257) <https://www.python.org/dev/peps/pep-0257/>`_.
+ Assurez-vous que le code suit la `PEP-8 <http://legacy.python.org/dev/peps/pep-0008/>`_ (conventions de formatage de python) grâce à ``tox -e flake8``. Veillez également à respecter `les conventions de code de Django <https://docs.djangoproject.com/en/1.7/internals/contributing/writing-code/coding-style/>`_.
+ Des *tests* assurent que les modifications que vous apportez n'induisent pas d'effet secondaires. Assurez-vous donc que l'intégralité des tests passent : ``python manage.py test``. Si nécéssaire, ajoutez un test pour votre modification. Seules les modifications de documentation et les réusinages n'ont pas besoin de nouveaux tests. **Votre test doit échouer sans votre modification, et réussir avec**. Il n'y a aucune chance que votre *pull request* soit acceptée sans son test associé.
+ Si vous avez fait des modifications du _front_, jouez les tests associés : ``npm test``.
+ Si vous modifiez le modèle (les fichiers ``models.py``), n'oubliez pas de créer les fichiers de migration correspondant : ``python manage.py makemigrations`` (et de les *commit*).
+ Si votre travail nécessite des actions spécifiques lors du déploiement (installations de nouveaux packages, migration de données, etc), précisez-les dans le fichier ``update.md``.


Réaliser une *pull request* (PR)
--------------------------------

Tous les détails sur le *workflow* se trouvent `sur la page dédiée <http://zds-site.readthedocs.org/fr/latest/workflow.html>`__. En résumé,

+ Les PR sont unitaires. Aucune PR qui corrige plusieurs problèmes ou apporte plusieurs fonctionnalité ne sera accepté (sauf ZEP).
+ Ces PR sont mergées dans la branche ``dev`` (ou dans la branche de *release* s'il s'agit de correction de bug suite à la bêta) après une QA légère.
+ La branche ``prod`` contient exclusivement le code en production, pas la peine d'essayer de faire le moindre *commit* dessus !

Comment préparer une bonne PR ?
...............................

Outre les règles ci-dessus, lors de l'ouverture d'une PR, respectez `le template suivant <https://github.com/zestedesavoir/zds-site/blob/dev/.github/pull_request_template.md>`__  (qui vous est proposé par défaut):

.. sourcecode:: text

    | Q                                   | R
    | ----------------------------------- | -------------------------------------------
    | Type de modification                | correction de bug / nouvelle fonctionnalité / évolution
    | Ticket(s) (_issue(s)_) concerné(s)  | (ex #1337)

    ### QA

    * Instruction 1
    * Instruction 2
    (...)


D'une part, il est important de préciser le type de modification et l'*issue* qui est concernée.
Cela permet au testeur de vérifier les différents commentaires qui avaient été posté concernant le problème ou la fonctionnalité, afin de voir si tout à été respecté.

Ajoutez ensuite des notes de QA (Quality Assurance).
Ces notes doivent permettent à un testeur de comprendre ce que vous avez modifié, ce qu'il faut tester en priorité et les pièges auxquels il doit s'attendre et donc sur lesquels porter une attention particulière.
Précisez tout particulièrement s'il est nécessaire d'effectuer une action de gestion préalable, comme

+ ``python manage.py migrate --fake-initial``
+ ``python manage.py loaddata fixture/*.yaml``
+ ``npm run gulp -- build``
+ ...

Et ensuite ?
............

1. Une fois la PR proposée, `Travis CI <https://travis-ci.org/>`__ (un outil d'intégration continue), se charge de lancer les tests (*back*, *front* et PEP-8) pour vérifier que rien n'est cassé, dans un environement qui se veut le plus proche possible de celui du site. Obtenir une confirmation de Travis est un prérequis. Une fois la PR proposée, tout nouveau *commit* publié sera testé par cet outil.
2. Un testeur ce charge d'effectuer `la QA <workflow.html#qu-est-ce-qu-une-qa-legere>`__ (revue de code et tests manuels).
3. Si tout est ok, la PR est *mergée* et intégrée au code de Zeste de Savoir. Elle sera présente sur le site après la prochaine `mise en production <workflow.html#workflow-de-mise-en-production>`__.


