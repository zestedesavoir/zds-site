========
Selenium
========

Selenium est utilisé pour réaliser les tests front-end. Il s'agit d'un outil très utilisé qui propose des interfaces dans différents languages dont Python. Il est donc possible de l'utiliser avec Django.

Pour l'utiliser, il suffit au développeur d'installer Selenium et un webdriver.

Les tests front-end
-------------------

Installation du webdriver
~~~~~~~~~~~~~~~~~~~~~~~~~

Il est nécessaire d'installer deux choses pour utiliser Selenium avec Django : Selenium (présent dans ``requirements-dev.txt``) et un webdriver. Pour ceci, il suffit d'exécuter :

.. sourcecode:: bash

   # Installation du webdriver
   wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz
   mkdir geckodriver
   tar -xzf geckodriver-v0.30.0-linux64.tar.gz -C geckodriver
   # Ajout du webdriver dans le PATH
   export PATH=$PATH:$PWD/geckodriver

Pour macOS, il suffit de lire les instructions à l'adresse suivante : https://github.com/mozilla/geckodriver/

.. attention::

   La version de geckodriver à installer dépend des versions de Selenium et de Firefox ! Par exemple, la version 30.0 de geckodriver fonctionne correctement avec Selenium >= 3.14 et Firefox >= 78 ESR mais peut ne pas fonctionner avec d'autres versions. Mozilla met à disposition `une table de compatibilité <https://firefox-source-docs.mozilla.org/testing/geckodriver/Support.html>`_. En cas de problème lors de l'installation, ne pas hésiter à demander de l'aide !

Écriture des tests
~~~~~~~~~~~~~~~~~~

Il est donc possible d'écrire des tests pour Django directement en utilisant la document de Selenium ici : <http://selenium-python.readthedocs.io/> et le `StaticLiveServerTestCase` de Django (<https://docs.djangoproject.com/fr/2.1/ref/contrib/staticfiles/#django.contrib.staticfiles.testing.StaticLiveServerTestCase>).

Il est aussi possible d'utiliser l'extension Firefox (<https://addons.mozilla.org/en-US/firefox/addon/selenium-ide/>) et d'exporter le test généré, cependant, il est nécessaire de le réécrire pour prendre en compte Django et Python 3. De plus, il est nécessaire d'ajouter un tag à la classe afin de pouvoir lancer les tests Selenium séparément.

Voici le contenu d'un test :

.. sourcecode:: python

  from django.contrib.staticfiles.testing import StaticLiveServerTestCase
  from django.test import tag
  from selenium.webdriver import Firefox
  from selenium.webdriver.firefox.options import Options


  @tag("front")
  class MySeleniumTests(StaticLiveServerTestCase):
      @classmethod
      def setUpClass(cls):
          super().setUpClass()
          options = Options()
          options.add_argument("--headless")
          cls.selenium = Firefox(options=options)
          cls.selenium.implicitly_wait(30)

      @classmethod
      def tearDownClass(cls):
          cls.selenium.quit()
          super().tearDownClass()

      def test_zestedesavoir_is_present(self):
          self.selenium.get(self.live_server_url + "/")


Lancement des tests
~~~~~~~~~~~~~~~~~~~

Il suffit d'utiliser le Makefile et de lancer ``make test-back-selenium``.
