===================================
Elements de templates personnalisés
===================================

Le package ``zds/utils/templatetags`` contient un ensemble de tags et filtres personnalisés pouvant être utilisés
dans les templates rendues par Django.

La majorité de ces modules proposent aussi des fonctions proposant les même fonctionnalités depuis le reste du code
Python.

append_to_get
=============

L'élément ``append_to_get`` permet de rajouter des paramètres à la requête ``GET`` courante. Par exemple, sur une page
``module/toto``, le code de template suivant :

    {% load append_to_get %}
    <a href="{% append_to_get key1=var1,key2=var2 %}">Mon lien</a>

produira le code suivant :

.. sourcecode:: html

    <a href="module/toto?key1=1&key2=2">Mon lien</a>

si le contenu de ``var1`` est ``1`` et le contenu de ``var2`` est ``2``

captureas
=========

L'élément ``captureas`` permet de demander d'effectuer le rendu d'un bloc de template et de stocker son contenu dans
une variable. Ainsi le code suivant :

    {% load captureas %}
    {% captureas var2 %}
    {% for i in 'xxxxxxxxxx' %}
    {{forloop.counter0}}
    {% endfor %}
    {% endcaptureas %}

ne produit rien en sortie mais affecte le résultat du bloc entre les éléments ``{% captureas var2 %}`` et
``{% endcaptureas %}``, soit ``0123456789``, dans la variable de template ``var2``

date
====

Plusieurs filtres sont disponible dans ce module.

format_date
-----------

Ce filtre formate une date au format ``DateTime`` destiné à être affiché sur le site :

    {% load date %}
    {{ date | format_date}}

tooltip_date
------------

Ce filtre effectue la même chose que ``format_date`` mais à destination des ``tooltip``.

humane_time
-----------

Formate une date au format *Nombre de seconde depuis Epoch* en un élément lisible. Ainsi :

    {% load date %}
    {{ date_epoch | humane_time}}

sera rendu :

    01 Jan 1970, 01:00:42

Si le contenu de ``date_epoch`` etait de ``42``.

emarkdown
=========

Markdown vers HTML
------------------

Permet de rendre un texte markdown en HTML :

- ``emarkdown`` : Transforamtion classique
- ``emarkdown_inline`` : Transforamtion uniquement des éléments *inline* et donc pas de blocs. Utilisés pour les
  signatures des membres.


Markdown vers Markdown
----------------------

Ces élements sont utilisés dans le cadre de la transformation du markdown avant d'être traité par ``Pandoc`` lors de la
génération des fichiers PDF et EPUB des tutos :

- ``decale_header_1`` : Décale les titres de 1 niveau (un titre de niveau 1 devient un titre de niveau 2, etc.)
- ``decale_header_2`` : Décale les titres de 2 niveaux (un titre de niveau 1 devient un titre de niveau 3, etc.)
- ``decale_header_3`` : Décale les titres de 3 niveaux (un titre de niveau 1 devient un titre de niveau 4, etc.)


email_obfuscator
----------------

Ces templatetags sont principalement fondés sur https://github.com/morninj/django-email-obfuscator.


obfuscate
+++++++++

L'email va être encodé avec des caractères ASCII pour le protéger des bots :

    {% load email_obfuscator %}
    {{ 'your@email.com'|obfuscate }}


obfuscate_mailto
++++++++++++++++

Ce templatetag ajoute en plus un ``mailto``. Il prend un paramètre optionnel qui permet d'avoir un text personnalisé dans
la balise <a> :

    {% load email_obfuscator %}
    {{ 'your@email.com'|obfuscate_mailto:"my custom text" }}
    #returns '<a href="mailto:your@email.com">my custom text</a>' as an encoded string like
    #<a href="&#109;&#97;&#105;&#108;&#116;&#111;&#58;&#121;&#111;&#117;&#114;&#64;&#101;&#109;&#97;&#105;&#108;&#46;&#99;&#111;&#109;">my custom text</a>


obfuscate_mailto_top_subject
++++++++++++++++++++++++++++

Identique sur le fonctionnement à ``obfuscate_mailto``, ce templatetag ajoute en plus un sujet (qui remplace le champ
pouvant être inséré entre les balises ``<a>`` et ``</a>``) ainsi que ``target="_top"``.

Il est utilisé sur la page « Contact ».

Exemple :

    {% load email_obfuscator %}
    {{ 'association@zestedesavoir.com'|obfuscate_mailto_top_subject:"Contact communication" }}


autres
======

**TODO**
