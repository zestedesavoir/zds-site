{% load i18n %}

{% blocktrans with title=content.title|safe type=type|safe %}
Bonjour **{{ user }}**,

Tu as été ajouté comme auteur {{ type }} [{{ title }}]({{ url }}).
Tu peux le retrouver en [cliquant ici]({{ index }}), ou *via* le lien "En 
rédaction" du menu "Tutoriels" sur la page de ton profil.


Tu peux maintenant commencer à rédiger !
{%  endblocktrans %}
