===============================
Paramètrer le moteur de Captcha
===============================

ZdS utilise un moteur de captcha à l'inscription pour éviter la profusion de bot. Ce dernier s'appuie sur le système "Recaptcha Nocaptcha" de Google afin d'offrir à l'utilisateur une utilisation la moins contraignante possible.

Cependant, il est possible d'activer ou désactiver de manière très simple cette sécurite. Pour cela, il suffit de changer le paramètre booléen ``USE_CAPTCHA`` dans le fichier ``settings_prod.py``.

Pour que le moteur de captcha fonctionne, il faut lui spécifier des paramètres pour communiquer avec le serveur de vérification. Ce paramètrage se fait là encore dans le fichier ``settings_prod.py`` avec les options ``RECAPTCHA_PUBLIC_KEY`` et ``RECAPTCHA_PRIVATE_KEY``. Ces paramètres sont à récupérer sur `la page de google <https://www.google.com/recaptcha/admin>`_.   .
