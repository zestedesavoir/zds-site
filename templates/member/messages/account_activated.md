{% load i18n %}

{% blocktrans with username=username|safe %}

Bonjour **{{ username }}**,

Ton compte a été activé, et tu es donc officiellement membre de la communauté de {{ site_name }}.

{{ site_name }} est une communauté dont le but est de diffuser des connaissances au plus grand nombre.

Voici les fonctionnalités les plus importantes pour profiter du site :

- les [tutoriels]({{ tutorials_url }}) pour apprendre de nouveaux savoirs ;
- les [articles]({{ articles_url }}), pour découvrir de nouveaux sujets ;
- les [tribunes]({{ opinions_url }}), pour partager des opinions ou faire des retours d'expérience ;
- les [forums]({{ forums_url }}), pour discuter avec [la communauté]({{ members_url }}) et demander de l'aide.

Pour que les autres membres puissent t'aider au mieux, merci de respecter les règles suivantes sur le forum.

- Reste courtois (un bonjour, un merci et une orthographe lisible sont appréciés par tous :) ).
- Explique en détail ton problème et ce que tu as déjà fait (messages d'erreurs, tests effectués, résultat attendu, etc.).
- Pour la présentation, utilise le [Markdown](https://zestedesavoir.com/tutoriels/249/rediger-sur-zds/) avec parcimonie.
- Pour les formules, utilise le [mode mathématique de l'éditeur](https://zestedesavoir.com/tutoriels/244/comment-rediger-des-maths-sur-zeste-de-savoir/).
- Pour les codes sources, utilise la coloration syntaxique, accessible avec le bouton ||<>|| de l'éditeur.

Si tu veux transmettre ton savoir, il y a plusieurs possibilités :

- aider sur les forums ;
- commenter les [contenus en cours de rédaction](https://zestedesavoir.com/forums/communaute/beta-zone/) ;
- aider les [auteurs dans le besoin](https://zestedesavoir.com/contenus/aides/), en tant que co-auteur, illustrateur ou correcteur ;
- écrire un tutoriel ou un article (en pensant à la [ligne éditoriale](https://zestedesavoir.com/articles/222/la-ligne-editoriale-officielle-de-zeste-de-savoir/)).


L'ensemble du contenu disponible sur le site est et sera toujours gratuit, car la communauté de {{ site_name }} est attachée aux valeurs du libre partage et désire apporter le savoir à tout le monde quels que soient ses moyens.

En espérant que tu te plairas ici, je te laisse maintenant faire un petit tour.

Clem'

{% endblocktrans %}

