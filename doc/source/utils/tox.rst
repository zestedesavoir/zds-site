===
Tox
===

Tox est un outil qui permet d'encapsuler une logique de test spécifique, ainsi que d'executer cette logique dans un ou plusieurs environnements. Grace à cette encapsulation, on pourra donc demander à un serveur d'integration (travis dans notre cas) de lancer ladite logique, et/ou plusieurs en parallèle.

Pour le developpeur, lancer les tests à partir de tox permet de s'asssurer que les tests sont lancés avec les tests sont lancés avec les bonnes dépendances. Lorsque vous construisez votre ``virtualenv`` vous meme, rien de vous assure que vos dépendances sont le reflet de vos requirements au moment du lancement des tests.

Les commandes de test sont donc centralisées et plus simple à écrire dans la console, il en existe actuellement plusieurs disponibles.

.. attention::

    Pour lancer les commandes tox, vous devez sortir de votre environnement virtualenv si vous en avez un (ce qui vous permet de lancer certaines commandes via ``sudo`` ). Ce qui signifie que tox doit etre installé en dehors de n'importe quel environnement de developpement.

Les tests back-end
------------------

Tests avec une base SQLite
~~~~~~~~~~~~~~~~~~~~~~~~~~

Les tests back-end en mode développement sont des tests lancés sur le back-end en se basant sur le fichier ``settings.py``. Ce qui signifie donc qu'il se base sur la base de donnée que vous avez définit dans le fichier ``settings.py``. Si vous avez un fichier ``settings_prod.py`` se dernier sera aussi utilisé pour surcharger les variables du ``settings.py``.

La commande de lancement est la suivante :

.. sourcecode:: bash

    tox -e back

Si vous souhaitez uniquement lancer les tests d'un module du projet, le module article par exemple :

.. sourcecode:: bash

    tox -e back zds.article

ça fonctionne donc exactement comme avec ``python manage.py zds.article``.
