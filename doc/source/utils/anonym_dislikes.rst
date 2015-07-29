======================
Anonymisation des +/-1
======================

Sur les forums et les commentaires de contenu, les membres peuvent ajouter des +1 ou des -1 pour signifier leur émotion en un clic à propos d'un message. Pendant longtemps ces votes étaient anonymes mais suite à une décision des membres, il a été décidé de les rendre publiques. Ainsi, l'affichage de ces derniers est possible gràce à un bouton en forme d'oeil à côté des icones de vote. Lors d'un clic sur ce bouton, les pseudos/avatars des votants sont récupérés en base de données pour être affiché (appel AJAX). Pour des raisons d'ergonomie, ce bouton n'est pas affiché dans la version mobile du site.

Cette décision de désanonymisation ayant eu lieu après le début de la vie du site, tous les votes antérieurs à cette décision restent anonymes. Pour cela, les votes sont filtrés selon leur clé primarire renseignés dans le fichier ``settings_prod.py`` : ``LIKES_ID_LIMIT`` et ``DISLIKES_ID_LIMIT``.
