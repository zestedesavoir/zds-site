{% load i18n %}


{% trans "Bonjour membres du CA" %},

{% blocktrans %}
Le membre **{{ username }}** souhaiterait adhérer à l'association.
{% endblocktrans %}

- {% trans "Identité" %} : {{ full_name }}
- {% trans "Adresse courriel" %} : {{ email }}
- {% trans "Date de naissance" %} : {{ birthdate }}
- {% trans "Adresse" %} :

{{ address }}

**{% trans "Motivations" %} :**

{{ justification }}

[{% trans "Voir son profil sur le site" %}]({{ profile_url }}).
