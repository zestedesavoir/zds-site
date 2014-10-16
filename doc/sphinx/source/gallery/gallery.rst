============
Les galeries
============

La liste des galleries de l'utilisateur est accessible via l'url suivante : ``/galerie/``.

Généralités
===========

Une galerie rassemble physiquement un certain nombre d'image. Elle peut prendre un titre ainsi qu'un sous-titre.

Création et remplissage
-----------------------

On peut créer une nouvelle galerie via l'url ``/galerie/nouveau/``, ou il est nécéssaire de renseigner ces deux champs.

.. attention::
   Des galeries sont créée **automatiquement** à la création d'un nouveau `tutoriel <../tutorial/tutorial.html>`_ par un utilisateur et possède alors le même nom que celui-ci.

Il est ensuite possible d'uploader des images via le menu de gauche :

   .. figure:: images/menu-gauche.png
      :align: center

      Liens permetant d'uploader des images

Via celui-ci, on peut importer des archives contenant des images (au format ZIP) ou des images seules. Dans ce dernier cas, le formulaire d'*upload* est le suivant :

   .. figure:: images/nouvelle-image.png
      :align: center

      Formulaire d'upload de nouvelles images

Comme on peut le voir, chaque image doit posséder au minimum un titre et peut posséder une légende, qui sera employée par la suite. Il est donc conseillé de remplir également ce second champ, bien que ce ne soit pas obligatoire. Quand à l'image elle-même, sa taille ne peut pas excéder 1024 Kio.

Une fois l'image uploadée, il est possible d'effectuer différentes actions sur celle-ci sur la page spécifique à celle-ci :

   .. figure:: images/gestion-image.png
      :align: center

      Gestion d'une image

Autrement dit,

+ En modifier le titre, la légende ou encore l'image en elle-même. À noter que le titre et la légende peuvent être modifiés **sans qu'il ne soit nécéssaire** d'uploader une nouvelle image.
+ Obtenir le code à insérer dans un champ de texte acceptant le markdown pour l'image en elle-même, sa miniature ou encore la miniature accompagnée du lien vers l'image en taille réelle.

.. attention::
    Le titre de l'image n'entre pas en compte dans le nommage de l'image une fois cette dernière téléchargée. Afin de s'assurer l'unicité des noms, nous utilisons un algorithme de hashage pour cela.

Les utilisateurs et leurs droits
--------------------------------

Le créateur de la gallerie possède un droit d'écriture, mais peut rajouter à tout moment des utilisateurs dans celle-ci :

   .. figure:: images/gestion-auteurs.png
      :align: center

      Ajout d'un nouvel utilisateur

Lors d'un clic sur "Ajouter un utilisateur", une fenêtre modale s'ouvre :

   .. figure:: images/gestion-auteurs2.png
      :align: center

      Choix de l'utilisateur et sélection de ces droits

Il est alors possible de rajouter un nouvel utilisateur dans la gallerie. Les droits de celui-ci peuvent-être les suivants :

+ **Lecture** : (``zds.gallery.models.GALLERY_READ``) l'utilisateur a seulement le droit de consulter les images existantes dans la gallerie sans pouvoir apporter de modifications;
+ **Écriture** : (``zds.gallery.models.GALLERY_WRITE``), inclut **Lecture**, l'utilisateur peut modifier ou supprimer des images existantes, en rajouter des nouvelles et changer les atributs de la gallerie (y compris ajouter de nouveaux utilisateurs);


Il n'est actuelement pas possible de modifier les droits d'un utilisateur après son ajout à la galerie.


La suppression
--------------

Une image peut être supprimée à tout moment en la sélectionnant sur la page de la gallerie et en cliquant sur le bouton suivant :

   .. figure:: images/sup-image.png
      :align: center

      Suppression d'une ou plusieurs image(s)

Attention qu'aucune confirmation n'est demandée pour la suppression d'une image.

Une galerie peut être quand a elle supprimée via la page de gestion des galeries (``/galerie/``) en cochant la case de celle-ci et en cliquant sur "supprimer les galleries sélectionnées" dans le menu de gauche :

   .. figure:: images/sup-galerie.png
      :align: center

      Suppression d'une galerie

Une modale s'ouvre ensuite, demandant de confirmer le choix :

   .. figure:: images/sup-galerie2.png
      :align: center

      Confirmation

Une fois cliqué sur "confirmer", la gallerie et les images qu'elle contient sont supprimées.

.. attention::
   Si une galerie est liée à un tutoriel existant, elle ne peut pas être supprimée.

Lien gallerie <-> Tutoriel
==========================

Chaque tutoriel possède une galerie en propre. Par défaut cette galerie possède le même nom qui a été donné au tutoriel lors de sa création.

Chaque auteur possède un droit d'accès en écriture (``GALLERY_WRITE``) sur la gallerie liée au toturiel.

Si un membre possède un droit de lecture seule (``GALLERY_READ``) sur la gallerie d'un tutoriel, aucun droit n'est accordé à ce membre quant au tutoriel.

A l'heure actuelle, les articles ne possèdent pas de gallerie.

Aspects techniques
==================

Chaque galerie (classe ``Gallery``) est stockée en base de donnée avec son titre, son sous-titre et son *slug* (ainsi que la date de création et de dernière modification). Une galerie est ratachée à l'utilisateur via la classe ``UserGallery``, qui reprend un lien vers l'utilisateur, la gallerie, mais également les droits qu'il possède sur cette dernière, sous la forme d'une constante : ``GALLERY_READ`` pour le droit de lecture ou ``GALLERY_WRITE`` pour le droit d'écriture.

Une image (classe ``Image``) est renseignée en base de donnée avec son titre, sa légende, un lien vers la galerie qui la contient, son *slug* et un lien *physique* vers le fichier image  (ainsi que la date de création et de dernière modification).

Les images sont stockée dans le dossier renseigné par la variable ``MEDIA_URL`` (dans le fichier ``settings.py``), dans un sous-dossier dont le nom correspond au ``pk`` de la galerie. C'est la libraire `easy_thumbnails <https://github.com/SmileyChris/easy-thumbnails>`_ qui gère la génération des miniatures correspondantes aux images uploadées, à la demande du *back*.

Outils logiciels utilisés
=========================

Afin d'assurer une compatibilité maximale de toutes les images des galleries, leur redimensionnement au besoin... Le logiciel pyllow est utilisé.