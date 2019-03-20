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
   wget https://github.com/mozilla/geckodriver/releases/download/v0.19.0/geckodriver-v0.19.0-linux64.tar.gz
   mkdir geckodriver
   tar -xzf geckodriver-v0.19.0-linux64.tar.gz -C geckodriver
   # Ajout du webdriver dans le PATH
   export PATH=$PATH:$PWD/geckodriver

Pour Mac OS ou Windows, il suffit de lire les instructions à l'adresse suivante : https://github.com/mozilla/geckodriver/

.. attention::

   La version de geckodriver à installer dépend des versions de Selenium et de Firefox ! Par exemple, la version 19.0 de geckodriver fonctionne correctement avec Selenium 3.6.0 et Firefox 55.0 ou 56.0 mais peut ne pas fonctionner avec d'autres versions. En cas de problème lors de l'Installation, ne pas hésiter à demander de l'aide !

Écriture des tests
~~~~~~~~~~~~~~~~~~

Il est donc possible d'écrire des tests pour Django directement en utilisant la document de Selenium ici : <http://selenium-python.readthedocs.io/> et le `StaticLiveServerTestCase` de Django (<https://docs.djangoproject.com/fr/2.1/ref/contrib/staticfiles/#django.contrib.staticfiles.testing.StaticLiveServerTestCase>).

Il est aussi possible d'utiliser l'extension Firefox (<https://addons.mozilla.org/en-US/firefox/addon/selenium-ide/>) et d'exporter le test généré, cependant, il est nécessaire de le réécrire pour prendre en compte Django et Python 3. De plus, il est nécessaire d'ajouter un tag à la classe afin de pouvoir lancer les tests Selenium séparément.

Voici le contenu d'un test :

.. sourcecode:: python

  from django.contrib.staticfiles.testing import StaticLiveServerTestCase
  from selenium.webdriver.firefox.webdriver import WebDriver
  from django.test import tag


  @tag('front')
  class MySeleniumTests(StaticLiveServerTestCase):
      @classmethod
      def setUpClass(cls):
          super(MySeleniumTests, cls).setUpClass()
          cls.selenium = WebDriver()
          cls.selenium.implicitly_wait(10)

      @classmethod
      def tearDownClass(cls):
          cls.selenium.quit()
          super(MySeleniumTests, cls).tearDownClass()

      def test_zestedesavoir_is_present(self):
          self.selenium.get(self.live_server_url + '/')


Lancement des tests
~~~~~~~~~~~~~~~~~~~

Il suffit d'utiliser le Makefile et de lancer ``make test-front``.

Il est aussi possible d'éxecuter un test précis avec ``python manage.py test zds.xxx.yyy`` où ``xxx`` est le nom du module à tester et ``yyy`` est le nom du fichier de tests à lancer.
