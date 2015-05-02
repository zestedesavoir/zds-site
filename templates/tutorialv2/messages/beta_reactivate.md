{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}

Bonjour,

La bêta de **{{ title }}** est de nouveau active.

-> [Lien de la bêta : {{ title }}]({{ url }}) <-

Merci d'avance pour vos relectures.

{%  endblocktrans %}