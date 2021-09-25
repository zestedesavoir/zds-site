==================================
Écrire des tests pour le *backend*
==================================

Zeste de Savoir aspire à avoir une base de code aussi qualitative et maintenable que possible, notamment grâce à une suite de tests automatisés pour le *backend* Python. Lorsqu'on développe pour Zeste de Savoir, on est ainsi amené à modifier cette suite de tests et ainsi contribuer à la qualité du code.

Ce guide est destiné aux contributeurs qui recherchent des conseils pour la mise en œuvre des tests *backend* sur Zeste de Savoir. Si vous souhaitez simplement lancer les tests existants, référez-vous au `guide correspondant <./backend-tests.html>`_.

Comprendre la politique de tests
================================

La politique actuelle pour les tests du *backend* est que tout ce qui est écrit en Python doit être testé. Ce n'est pas entièrement le cas actuellement, mais c'est l'objectif vers lequel on tend.

En conséquence, toute mise à jour du code doit s'accompagner de la création (ou adaptation) de tests pour au minimum couvrir le comportement ajouté ou modifié. L'ajout de tests manquants mais hors du périmètre de la modification n'est pas requis.

La présence de tests adéquats est vérifiée lors de l'assurance qualité des PR. Toute fusion de PR sans tests associés est exceptionnelle et cantonnée à des situations où la balance bénéfices-risques est acceptable. Accepter une PR sans tests associés est laissé à l'appréciation de l'équipe qui fusionne les PR.

Les contributions destinées purement à l'amélioration des tests sont les bienvenues. En effet, l'historique du projet fait que certaines parties du projet sont peu, mal, ou pas testées automatiquement.

Quoi qu'il en soit, l'équipe est disponible sur le canal ``#dev-de-zds`` de `notre serveur Discord <https://discord.gg/ue5MTKq>`_ ou `le forum Dev Zone <https://zestedesavoir.com/forums/communaute/dev-zone/>`_ pour vous aider si vous avez des doutes, questions ou difficultés.


Identifier ce qu'il faut tester
===============================

Avant d'écrire des tests, il est important d'identifier précisément ce que l'on teste. Cette question peut paraître triviale, mais est pourtant primordiale, car cela change la manière dont les tests seront écrits, les efforts pour ce faire et leur valeur ajoutée.

Quelles sont les limites de la chose testée ?
---------------------------------------------

Il faut être en mesure de délimiter précisément la chose testée, en précisant son interface (au sens large) : quelles sont les entrées, les sorties, et être capable de relier les unes aux autres.

Par exemple pour une fonction, les entrées incluent naturellement les arguments de la fonction et les sorties les valeurs de retour. Cependant, si la fonction lit ou modifie un état (attributs d'objet, base de données, fichiers), alors les entrées incluent aussi les états initiaux et les sorties les états finaux.

Les entrées et sorties peuvent être des choses complexes. Par contre, si vous n'êtes pas capable de les identifier clairement, c'est peut-être dû à une mauvaise conception de ce que vous souhaitez tester. Essayez de restructurer vos changements !

Est-ce que les limites identifiées sont les bonnes ?
----------------------------------------------------

Maintenant que vous avez identifié des limites pour la chose à tester, questionnez-vous sur leur pertinence. Les exemples ci-dessous listent quelques écueils qui peuvent survenir en pratique.

**Tester le code du framework au lieu du sien.** Avec Django, on réutilise des classes de base fournies par le *framework*. Il est assez facile de retester des comportements déjà vérifiés par la classe en question. Par exemple, si vous utilisez des *templates views*, il n'est pas nécessaire en général de tester automatiquement que le template que vous avez indiqué est bien celui utilisé : c'est à Django de vérifier que la classe fonctionne correctement. C'est d'ailleurs un risque de faire des tests redondants avec le code et donc plus difficile à maintenir dans la durée.

**Étendre excessivement le périmètre du test.** Quand on définit l'interface du code à tester, on peut parfois voir grand. Par exemple, on peut être tenté pour une vue de faire un test en regardant dans le rendu HTML si les informations attendues sont présentées comme prévu. Ce faisant, on teste le rendu du template en plus de la vue. Ce n'est pas forcément pertinent, donc réfléchissez bien à restreindre vos interfaces si vous pensez avoir vu trop large.


Organiser les tests
===================

Cette section donne quelques conseils généraux pour vous aider à organiser vos tests.

Séparer les niveaux d'abstraction
---------------------------------

On peut se retrouver à tout vouloir tester en même temps : les droits d'accès, les redirections,
le comportement dans différentes situations, etc. Pour faciliter les tests, considérez de séparer suivant différents aspects :

* les droits d'accès peuvent souvent être vérifiés sans aucunement tester le fonctionnel (erreur ou pas d'erreur) ;
* les redirections peuvent se vérifier souvent indépendamment du fonctionnel (redirigé ou non) ;
* le fonctionnel n'a par exemple pas besoin de s'entremêler avec la gestion des droits dans de nombreux cas.

On peut observer un découpage dans cet esprit dans ``./zds/tutorialv2/tests/tests_views/tests_editcontentlicense.py``.

Éviter les duplications
-----------------------

Quand on teste différents résultats attendus pour différentes entrées, on peut être amené à écrire du code qui a tendance à se répéter. Si tel est le cas, une bonne stratégie consiste à décrire les cas de tests sous forme de données (par exemple à l'aide d'un dictionnaire) et ensuite écrire une unique fonction de tests qui jouera tous les différents cas en appliquant la même logique à chaque fois.

Cette technique est par exemple employée dans ``./zds/tutorialv2/tests/tests_views/tests_editcontentlicense.py``.

Découper en fichiers
--------------------

Les fichiers de tests sur Zeste de Savoir sont historiquement assez longs, et peuvent atteindre plusieurs centaines voire plusieurs milliers de lignes. Mais ce n'est pas vraiment une bonne idée !

Si vous êtes amenés à rajouter plusieurs centaines de lignes de tests dans un fichier (ce qui est vite arrivé dans certains cas), considérez le choix de faire un fichier séparé.


Connaître les outils pratiques
==============================

Quelques lectures en lien avec Django :

* `l'aperçu global des tests avec Django <https://docs.djangoproject.com/en/2.2/topics/testing/overview/>`_ ;
* `la documentation sur les outils de test fournis par Django <https://docs.djangoproject.com/en/2.2/topics/testing/tools/>`_.

Une tâche qui revient très souvent lors des tests est la création d'utilisateurs, sujets de forum, messages, tutoriels, articles, etc.
Il existe des outils de développement pour faciliter leur création appelés *Factory* et qu'on retrouve dans les fichiers `factories.py` de chaque module. L'usage est simple, il suffit d'appeler le constructeur pour recevoir un objet du type souhaité :

.. sourcecode:: python

   self.author = ProfileFactory()  # self.author est un objet Profile !

.. include:: /includes/contact-us.rst
