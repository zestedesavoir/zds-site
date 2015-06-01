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

.. sourcecode:: html

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

.. sourcecode:: html

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

.. sourcecode:: html

    {% load date %}
    {{ date | format_date}}

tooltip_date
------------

Ce filtre effectue la même chose que ``format_date`` mais à destination des ``tooltip``.

humane_time
-----------

Formate une date au format *Nombre de seconde depuis Epoch* en un élément lisible. Ainsi :

.. sourcecode:: html

    {% load date %}
    {{ date_epoch | humane_time}}

sera rendu :

.. sourcecode:: html

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
================

Ces templatetags sont principalement fondés sur https://github.com/morninj/django-email-obfuscator.


obfuscate
---------

L'email va être encodé avec des caractères ASCII pour le protéger des bots :


.. sourcecode:: html

    {% load email_obfuscator %}
    {{ 'your@email.com'|obfuscate }}


obfuscate_mailto
----------------

Ce templatetag ajoute en plus un ``mailto``. Il prend un paramètre optionnel qui permet d'avoir un text personnalisé dans
la balise <a> :

.. sourcecode:: html

    {% load email_obfuscator %}
    {{ 'your@email.com'|obfuscate_mailto:"my custom text" }}

Ce qui donnera :

.. sourcecode:: html

    <a href="&#109;&#97;&#105;&#108;&#116;&#111;&#58;&#121;&#111;&#117;&#114;&#64;&#101;&#109;&#97;&#105;&#108;&#46;&#99;&#111;&#109;">my custom text</a>


obfuscate_mailto_top_subject
----------------------------

Identique sur le fonctionnement à ``obfuscate_mailto``, ce templatetag ajoute en plus un sujet (qui remplace le champ
pouvant être inséré entre les balises ``<a>`` et ``</a>``) ainsi que ``target="_top"``.

Il est utilisé sur la page « Contact ».

Exemple :

.. sourcecode:: html

    {% load email_obfuscator %}
    {{ 'association@zestedesavoir.com'|obfuscate_mailto_top_subject:"Contact communication" }}

feminize
--------

Permet de générer les déterminants et pronom adéquats en fonction du mot suivant dynamiquement généré. Typiquement
ce templatetag est utile dans le cas de la hiérarchie des tutoriels où vous pouvez avoir *"une partie"* ou *"un chapitre"*.

Ce templatetag est basé sur deux dictionnaires de mots : le premier qui associe le déterminant masculin à son homologue
féminin est le second qui associe un mot à un booléen qui indique s'il est féminin ``True`` ou masculin ``False``.

Exemple :

.. sourcecode:: html

    {% load feminize %}
    {{ "le"|feminize:"partie" }} partie <!-- affiche "la partie" si vous êtes en langue française -->

.. attention::
    le templatetag ``feminize`` est internationalisé.

times
-----

Permet de générer une liste de nombre pour itérer dessus, utile dans les boucles.

Exemple :

.. sourcecode:: html
    {% load times %}
    {% for i in 25|times %}
        je suis dans l'itération {{ i }}
    {% endfor %}

target_tree
-----------

Ce templatetag est utilisé dans le module de tutoriel (v2) dans le but de générer la hiérarchie des tutos et l'arbre
des déplacements possibles d'un élément. Il s'agint d'un wrapper autour de ``zds.tutorialv2.utils.get_target_tagged_tree``.

Exemple :

.. sourcecode:: html
    {% load target_tree %}
    {% for element in child|target_tree %}
            <option value="before:{{element.0}}"
            {% if not element.3 %} disabled {% endif %}>
                 &mdash;&mdash;{% for _ in element.2|times %}&mdash;{% endfor %}{{ element.1 }}
            </option>
    {% endfor %}

repo_blob et diff_text
----------------------

Ces deux templatetags sont utilisés de concert dans le module de diff des contenus (v1 et v2).

``repo_blob`` s'assure que les données brutes (texte) extraites du dépot sont bien encodée (py2).
``diff_text`` transforme la sortie de gitdiff en html.

Exemple :

.. sourcecode:: html
    {% load repo_reader %}
    <h2>{% trans "Nouveaux Fichiers" %}</h2>
    {% for add in path_add %}
        {% with add_next=add.b_blob|repo_blob %}
            <h3>{{ add.b_blob.path }}</h3>
            <div class="diff_delta">
                {{ ''|diff_text:add_next|safe }}
            </div>
        {% endwith %}
    {% endfor %}

    <h2>{% trans "Fichiers Modifiés" %}</h2>
    {% for maj in path_maj %}
        {% with maj_next=maj.b_blob|repo_blob %}
            {% with maj_prev=maj.a_blob|repo_blob %}
                <h3>{{ maj.a_blob.path }}</h3>
                <div class="diff_delta">
                    {{ maj_prev|diff_text:maj_next|safe }}
                </div>
            {% endwith %}
        {% endwith %}
    {% endfor %}