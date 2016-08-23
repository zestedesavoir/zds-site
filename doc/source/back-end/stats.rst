================
Les statistiques
================

Le module de statistique permet, à partir des logs générés par le serveur web, de stocker les nombres de visite sur les contenus.
Le module va donc exposer le contenu de ces données stockées à travers une API afin d'être utilisée par le site web pour l'afficher à coté d'un contenu, et utilisée par toute personne qui souhaiterait exploiter les statistiques sur le contenu.


.. DANGER::
    La comptabilisation des visites commencera à la date de la première mise en production du module de statistiques. Ainsi visites sur les contenus publiés avant cette date ne pouront pas être comptabilisés.

Le schema ci-dessous décrit l'architecture du module de statistique dans l'application zds.

    .. figure:: ../images/stats/architecture.png
      :align: center

Le back-end du module est donc constitué de deux parties :

- le batch : qui permet d'indexer dans la base de donnée le contenu du fichier de log quotidien
- l'api : qui permet d'exposer les différents services de consultation de statistiques

Le déploiement du module en production
======================================

Modification du format de log nginx
-----------------------------------


    http {
        log_format combined '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for" $request_time $upstream_response_time $pipe';

        ...
    }

Mise en place de rotation des logs
----------------------------------

Il faut installer logrotate

.. code:: bash

    sudo apt-get install logrotate

Si aucune rotation de log n'a été mise en place sur les access log nginx, il faudra créer le fichier ``/etc/logrotate.d/nginx.conf`` sinon, il suffira de modifier la configuration nginx existante.

Le contenu doit être le suivant :

.. code:: bash

    /path/to/log/nginx-access.log {
        daily
        rotate 90
        compress
        delaycompress
        missingok
        notifempty
        create 644 zds zds
    }

.. note::
    Cette configuration permet d'effectuer une rotation tous les jours des access log de nginx, avec 90 jours de rétention. Les logs >= 2 jours seront compressés, ce qui permet au batch zds-stats de s'executer sur la log d'il y'a un jour et non compressée.

Redemarrez ensuite le service logrotate

.. code:: bash

    service logrotate restart

Mise en place de l'ordonnancement de batchs via crontab
-------------------------------------------------------

Le batch de parsing des logs doit tourner sur un fichier de log qui n'est pas en cours d'écriture par un autre processus.
Donc on preferera faire tourner le service sur la log du jour J-1 après que logrotate soit passé.

Ce qui revient à inscrire cette ligne dans notre système d'ordonnancement (en prennant la peine de remplacer par les bon chemins).

.. code:: bash

    /path/to/python2.7 /path/to/zds-site/manage.py parse_logs /path/to/log/nginx-access.log.1 >> /path/to/log/zds-stats.log 2>> /path/to/log/zds-stats-error.log
