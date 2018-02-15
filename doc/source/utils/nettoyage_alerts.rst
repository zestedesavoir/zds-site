==================================================
Commande de nettoyage des alertes et notifications
==================================================

Il peut arriver que le système d'alerte et de notification génère des alertes et/ou notifications persistentes.

Nous faisons en sorte de corriger les bugs pour les nouvelles alertes et notifications mais ces corrections sont rarement
rétroactives. C'est pourquoi une commande de nettoyage a été mise à disposition.

Elle s'utilise ainsi : ``python manage.py clean_alerts_and_notifications``.

Un paramètre optionnel existe si vous désirez utiliser un autre administrateur que l'utilisateur anonyme/Clem' :
``--moderator <username>``.
