==================
Helpers CSS
==================

Des *mixins* SCSS sont disponibles pour faciliter le développement.

CSS adaptatif (responsive)
=============

Une série de *mixins* existe pour faciliter l'insertion de *media-queries*
afin d'adapter l'interface du site aux différents appareils du marché.

Variables
-------------------

Tout d'abord, des variables SCSS définissent différents points d'arrêt entre
plusieurs types d'écran :

- ``$tablet`` : largeur minimale des tablettes (769 pixels) ;
- ``$desktop`` : largeur minimale d'un écran d'ordinateur classique (1024 pixels) ;
- ``$wide`` : largeur minimale d'un écran large (1216 pixels) ;
- ``$fullhd`` : largeur minimale d'un écran full-HD (1408 pixels).

*Mixins*
-------------------

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

Voici les différentes *mixins* disponibles. Les noms des *mixins* reprennent
ceux des points d'arrêt plus haut.

- ``mobile`` : les appareils mobiles.
- ``tablet`` : les tablettes, et toutes les tailles au dessus.
- ``tablet-only`` : les tablettes, uniquement.
- ``touch`` : les mobiles et les tablettes.
- ``desktop`` : les ordinateurs, toutes tailles d'écran.
- ``desktop-only`` : les ordinateurs, mais pas ceux de grande taille.
- ``until-wide`` : les mobiles, tablettes, et ordinateurs pas trop grands.
- ``wide`` : les ordinateurs, à partir de ceux ayant un grand écran.
- ``wide-only`` : les ordinateurs ayant un grand écran, mais pas un écran full-HD.
- ``until-fullhd`` : tous les appareils, sauf ceux ayant un écran full-HD.
- ``fullhd`` : les ordinateurs ayant un écran full-HD. Les téléviseurs, aussi.

Si vous étiez habitué⋅e à l'ancien système…
-------------------

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
    - ``touch``
  * - ``$media-tablet``
    - ``tablet``
  * - ``$media-wide``
    - ``desktop``
  * - ``$media-under-extra-wide``
    - ``until-wide``
  * - ``$media-extra-wide``
    - ``wide``
  * - ``$media-mega-wide``
    - ``fullhd``
