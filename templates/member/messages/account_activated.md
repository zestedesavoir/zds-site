{% load i18n %}

{% blocktrans with username=username|safe %}

Bonjour **{{ username }}**,

Je suis Clem', la mascotte de {{ site_name }}. Je suis aussi en charge des messages automatiques tels que celui-ci.

J'ai l'honneur de t'annoncer que maintenant que ton compte a été activé, tu es officiellement membre de la communauté !

Tu peux désormais profiter pleinement des fonctionnalités du site :

- la [bibliothèque]({{ library_url }}) pour apprendre de nouvelles choses ;
- la [tribune]({{ opinions_url }}), pour partager des opinions ou faire des retours d'expérience ;
- le [forum]({{ forums_url }}), pour discuter avec la communauté et demander de l'aide.

Sur le forum, reste courtois, explique ton problème clairement et utilise la [mise en forme](https://zestedesavoir.com/tutoriels/249/rediger-sur-zds/). En suivant ces conseils, les autres membres pourront t’aider au mieux.

Si tu veux transmettre ton savoir, tu trouveras tout ce qu'il y a à savoir dans le [guide du contributeur](https://zestedesavoir.com/tutoriels/705/le-guide-du-contributeur/).

En espérant que tu te plairas ici, je te laisse maintenant faire un petit tour.

Clem'

{% endblocktrans %}
