{% load i18n %}
{% load date %}
{% blocktrans with time=content.creation_date|format_date title=content.title|safe type=type|safe %}

Tout le monde se secoue ! :D

J'ai commencé ({{ time }}) la rédaction d’un {{ type }} au doux nom
de « {{ title }} » et j’ai pour objectif de proposer en validation
un texte aux petits oignons. Je fais donc appel à votre bonté sans
limites pour dénicher le moindre pépin, que ce soit à propos
du fond ou de la forme. Vous pourrez consulter la bêta à votre guise à
l’adresse suivante :

-> [À présent, c’est à vous !]({{ url }}) <-

Merci !
{%  endblocktrans %}
