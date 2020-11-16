======================
Anonymisation des +/-1
======================

Sur les forums et les commentaires de contenu, les membres peuvent ajouter des +1 ou des -1 pour signifier leur émotion en un clic à propos d'un message. Pendant longtemps ces votes étaient anonymes mais suite à une décision des membres, il a été décidé de les rendre publiques. Ainsi, un extrait de la liste des votants non-anonymes est visible sous forme de tooltip au survol des boutons de votes. La liste complète est ensuite accessible sous forme de boite modale, ouvrable au clic sur la tooltip.

Cette décision de désanonymisation ayant eu lieu après le début de la vie du site, tous les votes antérieurs à cette décision restent anonymes. Pour cela, les votes sont filtrés selon leur clé primaire renseignés dans le fichier ``settings_prod.py`` : ``VOTES_ID_LIMIT``
