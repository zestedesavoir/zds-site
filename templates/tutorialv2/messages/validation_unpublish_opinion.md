{% load i18n %}

{% blocktrans with title=content.title|safe moderator_name=moderator.username|safe moderator_url=moderator.get_absolute_url %}

Votre billet « [{{ title }}]({{ url }}) » a été définitivement dépublié par 
[{{ moderator_name }}]({{ moderator_url }}), probablement car il enfreignait les CGU du site.

N'hésitez pas à contacter cette personne afin d'obtenir plus d'informations sur sa décision.
{% endblocktrans %}