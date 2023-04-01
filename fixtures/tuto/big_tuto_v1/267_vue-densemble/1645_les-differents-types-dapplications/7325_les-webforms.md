ASP.NET WebForms c’est tout un mécanisme qui permet de faciliter la création d’une application web en faisant comme si c’était une application Windows. Plus précisément, nous allons nous inspirer des applications Windows Form. Le design par défaut des composants sera le même.

Il permet de travailler avec une approche événementielle, comme une application Windows. Le premier but d’ASP.NET WebForms était de faire en sorte que les personnes qui avaient déjà fait du développement Windows (en C# ou en VB.NET) puisse facilement faire du développement web, dans un contexte qui leur serait familier.

->![Principe d'une application ASP.NET Web Form](/media/galleries/304/ffe80943-ddd2-4b41-99ee-ebee7f5cde25.png.960x960_q85.png)<-

[[a]]
|Le web et les applications bureau sont deux mondes très différents. Si les grands principes sont les mêmes, beaucoup de différences existent. La plus évidente est la manière même avec laquelle sont gérés les événements.
|Les pages web retiennent beaucoup moins bien le contexte d'exécution, on dit qu'ils sont *stateless*.

Dans une application Web Form, un page HTML est constitué de contrôles serveur (un bouton, un champ de texte modifiable, un tableau, des cases à cocher, etc), de scripts clients et du code serveur (généralement du code C# directement inclus dans le HTML via des balises spéciales).

D'un autre côté, nous retrouvons aussi une séparation du code C# et du code HTML : les contrôles sont glissé sur la page Web et le C# gère la partie évènementielle en arrière plan : lorsque l'on clique sur ce bouton il va se passer ceci, etc. C'est une manière vraiment simple de réaliser une application Web.

Les inconvénients avec une application Web Form résident dans l'organisation du code et de l'abstraction nous entendons par là que le code est moins organisé et que lors du développement d'une grosse application Web, vous risquez de vous perdre facilement. Donc assez difficile à maintenir. Un autre défaut est le modèle de développement similaire à celui d'un application Windows, et donc un débutant aura tendance à développer de la même façon en Web Forms, ce qui est une erreur, car les deux n'ont rien à voir.
