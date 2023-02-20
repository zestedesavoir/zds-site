========================
Installation de GeoLite2
========================

`GeoLite2 <https://dev.maxmind.com/geoip/geolite2-free-geolocation-data>`_ est une base de donnée gratuite donnant des informations de localisation sur les adresses IP, par exemple le pays d'origine probable. Zeste de Savoir l’utilise afin de localiser les adresses IP des membres à des fins de modération.

L’installation de la base de donnée est optionnelle pour le bon fonctionnement du site. En particulier, l’environnement de développement peut fonctionner sans.


Installation
------------

La base de donnée doit être téléchargée depuis le site de l’éditeur.

1. Créer un `compte utilisateur <https://www.maxmind.com/en/geolite2/signup?lang=en>`_ gratuit.
2. Se connecter et accéder à la `page de téléchargement <https://www.maxmind.com/en/accounts/current/geoip/downloads>`_.
3. Choisir la ligne « GeoLite2 City » ; vérifier que le format est bien *GeoIP2 Binary* et télécharger l’archive GZIP.
4. Décompresser l’archive et renommer le dossier ``GeoLite2-City_YYYYMMDD`` en ``geodata``.
5. Placer ce dossier à la racine du projet.

La localisation des adresses IP sera désormais indiquée sur les pages de profil si vous êtes connectés en tant que staff ou admin.

Consultez la `documentation officielle <https://dev.maxmind.com/geoip/geolite2-free-geolocation-data>`_ pour plus d’information.


Mise à jour
-----------

La mise à jour de la base de donnée peut se faire en téléchargeant une nouvelle version et en l’installant à la place de l’ancienne, en suivant la procédure décrite dans la section `Installation <#installation>`_.

Si vous souhaitez automatiser la mise à jour, d’autres options existent :

* le programme de mise à jour `GeoIP Update <https://dev.maxmind.com/geoip/updating-databases?lang=en#using-geoip-update>`_ ;
* l’utilisation des permaliens de la page de téléchargement, par exemple avec ``wget`` ou autre outil similaire.

Dans tous les cas, vous aurez besoin de générer une clé de licence.

Consultez la `documentation officielle <https://dev.maxmind.com/geoip/geolite2-free-geolocation-data>`_ pour une information complète à ce sujet.


Résolution de problème
----------------------

J’ai des avertissements concernant GeoIP2 dans les logs
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

Si le message d’erreur est le suivant :

    .. sourcecode:: none

        GeoIP path must be a valid file or directory.

alors la base de donnée n’est pas installée ou n’est pas installée au bon endroit.

* Vérifiez que vous avez placé le dossier au bon endroit.
* Vérifiez que le dossier a le bon nom.
* Vérifiez que le fichier ``.mmdb`` a le bon nom.

À cette fin, consulter la configuration de votre environnement de développement peut être utile. Le module de localisation utilise les paramètres ``GEOIP_PATH`` pour le nom dudossier et ``GEOIP_CITY`` pour le nom du fichier. Ils sont définis dans ``zds/settings/abstract_base/zds.py``.

Si vous avez une autre erreur, contactez les développeurs. Il s’agit sûrement d’un bug et non d’un souci d’installation.


La localisation de l’IP n’est pas affichée malgré tout
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Vérifiez d’abord votre installation encore une fois, et notamment l’absence d'avertissement concernant GeoIP2 dans les logs. Si vous avez des avertissements, consultez la `section ci-dessus <#jai-des-avertissements-concernant-geoip2-dans-les-logs>`_ pour les résoudre.

Vérifiez que vous êtes bien connecté en tant que staff ou admin. Les adresses IP et leur localisation ne sont pas affichées pour les simples membres.

Vérifiez que le profil ne s’est pas connecté depuis une IP locale telle que 127.0.0.1. Aucune localisation ne sera affichée pour ce type d’IP.

Autrement, il est possible que la base de donnée ne connaisse pas la localisation de l’IP. Dans ce cas, Zeste de Savoir ne donnera aucune information de localisation. Notez également que la localisation peut être partielle (par exemple seulement le pays, mais pas la ville).
