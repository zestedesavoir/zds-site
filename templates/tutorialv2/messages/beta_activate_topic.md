{% load i18n %}
{% load date %}

{% blocktrans with time=content.creation_date|format_date title=content.title|safe type=type|safe %}

Bonjour à tous,

J'ai commencé ({{ time }}) la rédaction d'un {{ type }} dont l'intitulé est **{{ title }}**.

J'aimerais obtenir un maximum de retour sur celui-ci, sur le fond ainsi que sur la forme, afin de proposer en validation un texte de qualité.
Si vous êtes intéressé, cliquez ci-dessous.

-> [Lien de la bêta: {{ title }}]({{ url }}) <-

Merci d'avance pour votre aide.

{%  endblocktrans %}