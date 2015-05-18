{% load i18n %}
{% load date %}

{% blocktrans with time=content.creation_date|format_date title=content.title|safe type=type|safe %}

Debout là-dedans !

J'ai commencé ({{ time }}) la rédaction d'un {{ type }} au doux nom 
de « {{ title }} » et j'ai dans l'objectif de proposer en validation 
un texte aux petits oignons. Je fais donc appel à votre bonté sans 
limite pour obtenir un maximum de retours, que ce soit à propos 
du fond ou de la forme. Il est donc tout naturel que la bêta se 
place à votre disposition :

-> [Bêta, pour vous servir.]({{ url }}) <-

Je vous remercie pour votre aide.

{%  endblocktrans %}
