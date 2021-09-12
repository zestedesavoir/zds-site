=============================
Lancer les tests du *backend*
=============================

Lors du développement, il est souvent nécessaire de lancer les tests automatiques en local afin de vérifier que tout fonctionne comme prévu. Ce guide décrit l'essentiel à savoir pour utiliser les outils de gestion des tests fournis par Django.

Lancer tous les tests
=====================

La commande suivante permet de lancer tous les tests du *backend*. La découverte des tests est automatique : tous ce qui est identifié comme un test Django dans le projet sera lancé.

.. sourcecode:: bash

   ./manage.py test

Comme cette commande peut prendre beaucoup de temps, il est en général préférable d'utiliser une commande plus ciblée.

Lancer des tests de manière ciblée
==================================

Django permet de cibler plus précisément les tests à lancer en ajoutant des  arguments à la commande. C'est très pratique pendant le développement pour lancer et relancer des tests sur un morceau de code sans attendre pendant de longues minutes à chaque fois.

La commande ci-dessous lancera tous les tests trouvés dans le *package* passé en argument.

.. sourcecode:: bash

   ./manage.py test zds.tutorialv2.tests.tests_views

On peut cibler encore plus en indiquant un module, une classe ou une fonction de test.

.. sourcecode:: bash

   ./manage.py test zds.tutorialv2.tests.tests_views.tests_editcontentlicense
   ./manage.py test zds.tutorialv2.tests.tests_views.tests_editcontentlicense.EditContentLicensePermissionTests
   ./manage.py test zds.tutorialv2.tests.tests_views.tests_editcontentlicense.EditContentLicensePermissionTests.test_not_authenticated

On peut aussi indiquer plusieurs arguments à la suite pour lancer plusieurs groupes de tests. La commande ci-dessous lancera les tests pour les trois *packages* mentionnés.

.. sourcecode:: bash

   ./manage.py test zds.mp zds.pages zds.tutorialv2

Interpréter les résultats
=========================

Quand on lance des tests, Django renvoit beaucoup d'informations. Les plus importantes sont affichées en dernier.

Quand tous les tests passent vous verrez un message ressemblant à :

.. sourcecode:: console

   Ran 1 test in 0.515s

   OK

Quand certains tests échouent vous verrez un message ressemblant à :

.. sourcecode:: console

   Ran 4 tests in 2.609s

   FAILED (errors=2)

Il suffit alors de remonter la sortie console et chercher des lignes de la forme suivante, afin d'identifier quels tests échouent et pourquoi.

.. sourcecode:: console

   ======================================================================
   ERROR: test_authenticated_staff (zds.tutorialv2.tests.tests_views.tests_editcontentlicense.EditContentLicensePermissionTests)
   Test that on form submission, staffs are redirected to the content page.
   ----------------------------------------------------------------------

On rencontre en général deux types de soucis :

* ERROR : une erreur est survenue pendant le test (par exemple une exception qui conduit à un crash) ;
* FAIL : une assertion a échoué dans le test, mais il n'y a pas eu d'erreur.

Il ne vous reste alors plus qu'à corriger votre code ou mettre à jour les tests concernés. :-)

Pour en savoir plus sur les tests avec Django, consultez la `documentation officielle <https://docs.djangoproject.com/en/dev/topics/testing/overview/>`_.
