==================
Mixins SCSS
==================

Des *mixins* SCSS sont disponibles pour faciliter le développement.

CSS adaptatif (responsive)
==========================

Une série de *mixins* existe pour faciliter l'insertion de *media-queries*
afin d'adapter l'interface du site aux différents appareils du marché.

Variables
---------

Tout d'abord, des variables SCSS définissent différents points d'arrêt entre
plusieurs types d'écran :

- ``$tiny`` : largeur maximale des très très petits écrans (penser iPhone SE) (419 px) ;
- ``$tablet`` : largeur minimale des tablettes (769 pixels) ;
- ``$desktop`` : largeur minimale d'un écran d'ordinateur classique (1024 pixels) ;
- ``$wide`` : largeur minimale d'un écran large (1216 pixels) ;
- ``$extra-wide`` : largeur minimale d'un écran full-HD (1408 pixels).

*Mixins*
--------

Mais concrètement, vous utiliserez surtout les *mixins* permettant d'inclure
automatiquement les *media-queries* correspondantes à différentes catégories
ou ensembles de catégories d'écran. Par exemple, pour écrire du SCSS qui ne sera
que pris en compte pour les mobiles, écrivez :

.. sourcecode:: scss

  @include mobile {
    // Votre code SCSS…
  }

ou encore, en SASS :

.. sourcecode:: sass

  +mobile
    // Votre code SASS…

Il est tout aussi possible d'utiliser ceci pour définir tous les CSS spécifiques
à une catégorie d'écran d'un coup, ou au fur et à mesure en spécifiant propriété
par propriété. Ainsi, ces deux façons de faire sont valides :

.. sourcecode:: scss

  .something {
    font-weight: bold;

    @include mobile {
      font-weight: normal;
    }
  }

  // -- ou --

  .something {
    font-weight: bold;
  }

  @include mobile {
    .something {
      font-weight: normal;
    }
  }

Voici les différentes *mixins* disponibles, avec la largeur de l'écran
correspondante. Les noms des *mixins* reprennent ceux des points d'arrêt plus
haut.

.. note::

	Pour des raisons de cohérence, et sauf si vous avez une bonne raison de faire autrement (par exemple, en cas de besoin d'un point d'arrêt très spécifique), utilisez toujours ces *mixins* pour insérer un code CSS spécifique à une largeur d'écran.

- | ``tiny`` : les très petits appareils mobiles.
  | *0 → 418 pixels*
- | ``mobile`` : les appareils mobiles.
  | *0 → 768 pixels*
- | ``tablet`` : les tablettes, et toutes les tailles au dessus.
  | *769 pixels → ∞*
- | ``tablet-only`` : les tablettes, uniquement.
  | *769 → 1023 pixels*
- | ``until-desktop`` : les mobiles et les tablettes.
  | *0 → 1023 pixels*
- | ``desktop`` : les ordinateurs, toutes tailles d'écran.
  | *1024 pixels → ∞*
- | ``desktop-only`` : les ordinateurs, mais pas ceux de grande taille.
  | *1024 → 1215 pixels*
- | ``until-wide`` : les mobiles, tablettes, et ordinateurs pas trop grands.
  | *0 → 1215 pixels*
- | ``wide`` : les ordinateurs, à partir de ceux ayant un grand écran.
  | *1216 pixels → ∞*
- | ``wide-only`` : les ordinateurs ayant un grand écran, mais pas *très* grand.
  | *1216 → 1407 pixels*
- | ``until-extra-wide`` : tous les appareils n'ayant pas un très grand écran.
  | *0 → 1407 pixels*
- | ``extra-wide`` : les ordinateurs ayant un écran très grand. Les téléviseurs, aussi.
  | *1408 pixels → ∞*

Si vous étiez habitué⋅e à l'ancien système…
-------------------------------------------

Auparavant, des variables existaient contenant la partie des ``@media``
changeante en fonction des largeurs d'écran, et on écrivait les *media-queries*
en entier à chaque fois. Les noms des variables n'étaient pas exactement les
mêmes non plus.

.. list-table:: Voici donc une correspondance.
  :header-rows: 1

  * - Ancienne variable
    - *Mixin* équivalente
  * - ``$media-mobile``
    - ``mobile``
  * - ``$media-mobile-tablet``
    - ``until-desktop``
  * - ``$media-tablet``
    - ``tablet``
  * - ``$media-wide``
    - ``desktop``
  * - ``$media-under-extra-wide``
    - ``until-wide``
  * - ``$media-extra-wide``
    - ``wide``
  * - ``$media-mega-wide``
    - ``extra-wide``


Listes au format horizontal (``horizontal-list``)
=================================================

Cette mixin CSS sert à transformer n'importe quelle liste (numérotée ou non, de toute façon les puces seront masquées)
en liste horizontale.

Conceptuellement, une liste de ce genre :

.. sourcecode:: html

   <ul class="my-horizontal-list">
       <li>Premier</li>
       <li>Second</li>
       <li>Troisième</li>
   </ul>

avec le CSS suivant :

.. sourcecode:: scss

   .my-horizontal-list {
       @include horizontal-list;
   }

sera affichée ainsi si cette mixin est appliquée.

.. sourcecode::

   Premier • Second • Troisième

Vous pouvez personnaliser le séparateur ainsi que la distance entre les éléments. Par défaut, une puce (``•``) et une
distance de 16 sont utilisées.

.. sourcecode:: scss

   .my-horizontal-list {
       @include horizontal-list($gap: $length-32, $separator: " — ");
   }
