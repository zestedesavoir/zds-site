================
Les statistiques
================

Le module de statistique permet, à partir des logs générés par le serveur web, de stocker les nombres de visites des les contenus.
Le module va donc exposer le contenu de ces données stockées à travers une API afin d'être utilisées par le site web pour l'afficher à coté d'un contenu, et utilisées par toute personne qui souhaiterait exploiter les statistiques d'affichage des contenus.


.. note::
    Les visites des contenus publiés avant la date de MEP pouront être comptabilisés.

Le schéma ci-dessous décrit l'architecture du module de statistique dans l'application zds.

    .. figure:: ../images/stats/architecture.png
      :align: center

Le back-end du module est donc constitué de deux parties :

- le batch, qui permet d'indexer dans la base de donnée le contenu du fichier de log quotidien
- l'api, qui permet d'exposer les différents services de consultation de statistiques

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

Si aucune rotation de log n'a été mise en place sur les access log nginx, il faudra créer le fichier ``/etc/logrotate.d/nginx.conf``, sinon il suffira de modifier la configuration nginx existante.

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
    Cette configuration permet d'effectuer une rotation tous les jours des access log de nginx, avec 90 jours de rétention. Les logs >= 2 jours seront compressés, ce qui permet au batch zds-stats de s'exécuter sur les logs non compressés d'il y'a un jour.

Redémarrez ensuite le service logrotate

.. code:: bash

    service logrotate restart

Mise en place de l'ordonnancement de batchs via crontab
-------------------------------------------------------

Le batch de parsing des logs doit tourner sur un fichier de log qui n'est pas en cours d'écriture par un autre processus.
On préférera donc faire tourner le service sur les logs du jour J-1 après que logrotate soit passé.

Cela revient à inscrire cette ligne dans notre système d'ordonnancement (en prennant la peine de remplacer par les bon chemins).

.. code:: bash

    /opt/zds/zdsenv/bin/python /opt/zds/zds-site/manage.py parse_logs /var/log/zds/nginx-access.log.1 >> /var/log/zds/zds-stats.log 2>> /var/log/zds/zds-stats-error.log
