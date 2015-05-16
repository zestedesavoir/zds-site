==================================
Installation du backend sous Linux
==================================

Pour installer une version locale de ZdS sur GNU/Linux, veuillez suivre les instructions suivantes.
Si une commande ne passe pas, essayez de savoir pourquoi avant de continuer.

Certaines des commandes d'installation (débutant par ``apt-get``) sont données ici pour Debian et ses dérivés, pour lesquels il est sûr qu'elles fonctionnent. Néanmoins, si vous utilisez une distribution différente, le nom des paquets à installer devrait être fort semblable, n'hésitez dès lors pas à employer la fonction "recherche" de votre gestionnaire de paquet préféré. Les autres commandes sont génériques et indépendantes de la distribution utilisée.

**NB** : il est impératif que la locale fr_FR.UTF-8 soit installée sur votre distribution.

L'installation se fait donc grâce à la commande suivante :

Sous Fedora
===========
.. sourcecode:: bash
    sudo yum install git python python-devel python-setuptools
    sudo easy_install pip
    sudo pip install tox
    sudo yum install libxml-devel libxslt-devel zlib-devel libjpeg libjpeg-devel freetype freetype-devel

Note : sous les versions supérieures ou égales à 22, vous serez invités à faire usage du gestionnaire de paquets dnf au lieu de yum. 
  
Et sous une autre distribution :
================================
.. sourcecode:: bash
    apt-get install git python-dev python-setuptools libxml2-dev python-lxml libxslt-dev libz-dev python-sqlparse libjpeg8 libjpeg8-dev libfreetype6 libfreetype6-dev
    easy_install pip tox
   

Toutes ces dépendances sont nécessaires au serveur Python, qui fait partie de l'environnement virtuel dans la configuration qui vous est proposée ici.



Installation et configuration de `virtualenv`
=============================================

(cette étape n'est pas obligatoire, mais fortement conseillée - cf. la partie "Présentation de l'environnement de travail")

.. sourcecode:: bash

    sudo pip install virtualenv

Commande de création de l'environnement de travail pour le projet Zeste de Savoir :

.. sourcecode:: bash

    virtualenv <chemin de répertoires que vous souhaitez + nom de l'environnement virtuel, par exemple « zds-virtual-env » (en tout, cela peut donc être : « /home/pnom/Documents/zds-virtual-env ») > --python=python2


Une documentation plus complète de cet outil `est disponible ici <http://docs.python-guide.org/en/latest/dev/virtualenvs/>`_.


Récupération du code-source de Zeste de Savoir 
==============================================
L'équipe de développement de Zeste de Savoir utilise la plateforme GitHub pour gérer les sources du site Web. Le dépôt officiel est situé à cette URL : https://github.com/zestedesavoir/zds-site. L'enjeu de cette partie est de récupérer ces sources grâce au paquet « git ».

Tout d'abord, créez-vous un compte GitHub et envoyez sur le site la clé publique que vous aurez préalablement générée.

Rendez-vous désormais sur le dépôt officiel (pour rappel, voici son URL : https://github.com/zestedesavoir/zds-site).

Cliquez sur le bouton « Fork » (en haut à droite). Enfin, faites une copie locale des sources de Zeste de Savoir depuis votre fork GitHub.

A titre d'information uniquement, votre fork GitHub est accessible à cette URL : https://github.com/<votre pseudo GitHub>/zds-site. Notez l'URL indiquée dans le bloc « HTTPS clone URL » : https://github.com/<votre pseudo GitHub>/zds-site.git (en bas à droite).

Créez votre fork local (le lecteur aura compris que le fork local est la copie locale du code-source, et que le fork GitHub est situé sur… GitHub).

Commande pour créer le fork local :

.. sourcecode:: bash

    git clone git@github.com:<votre pseudo GitHub>/zds-site.git <répertoire où vous voulez déposer ces sources, par exemple /home/<votre pseudo Fedora>/Documents/zeste-de-savoir-sources>

L'auteur conseille très fortement au lecteur de lire le tutoriel suivant, tutoriel qui explique la notion de fork notamment (la lecture de ce tutoriel est totalement facultative) : https://zestedesavoir.com/tutoriels/beta/656/participer-a-des-projets-open-sources-avec-git-et- github/.


Installation des outils front-end
=================================

Il vous faut installer les outils du front-end. Pour cela, rendez-vous sur `la documentation dédiée <frontend-install.html>`_.


Installation des dépendances autres que node.js et npm, et du serveur Python
==========

Rappelons-nous : nous avions installé, précédemment, node.js et npm, dont le serveur Python a besoin pour fonctionner (bien que ce soient des paquets JavaScript). Bien entendu, ce dernier nécessite l'installation d'autres dépendances, qui sont, elles, Python. Cette partie consiste à les installer dans l'environnement virtuel.

Rendez-vous dans votre fork local avec la commande « cd ». Vous devez y voir deux fichiers, entre autres :

- requirements.txt,
- requirements-dev.txt.

Ce sont ces fichiers qui contiennent les noms des dépendances Python dont le serveur Python de l'environnement virtual a besoin. Ils comportent également le nom du paquet « Django », qui contient le serveur Python dont nous parlons depuis le début.

Car, en effet, nous n'avions toujours pas installé ce serveur, bien que nous y ayons fait référence de multiples fois tout au long de ce document. Ce serveur, nous ne l'installerons jamais directement : en fait, il sera mis en place lorsque nous installerons Django (puisque pour rappel, Django contient le serveur Python).

Les paquets de ces deux fichiers (paquets = « Django » et dépendances de son serveur) seront automatiquement installés avec les commandes suivantes. Attention : il se peut qu'une erreur survienne. Si c'est le cas, supprimez votre environnement virtuel (le répertoire et tout ce qu'il contient). Puis, ré-installez-le (vous n'avez pas besoin de désinstaller puis d'installer de nouveau le paquet virtualenv : ré-installez simplement l'environnement virtuel de Zeste de Savoir – commande virtualenv <nom> –python=python2). Re-tapez ensuite les commandes qui suivent: Commandes pour installer Django (donc indirectement son serveur) et les dépendances de son serveur :

Attention : ne pas exécuter ces commandes en tant que super-utilisateur (donc pas de sudo ou autre).

.. sourcecode:: bash

    source <chemin pointant vers le répertoire de votre environnement virtuel>/bin/activate
    pip install --upgrade -r requirements.txt -r requirements-dev.txt
    python manage.py migrate
    deactivate

Explications sur la première et la dernière commande :
- La première vous permet d'entrer dans l'environnement virtuel dédié au projet (vous verrez juste en-dessous en quoi cela est intéressant) ;
- La dernière commande permet de quitter l'environnement virtuel et de recouvrer un « terminal » « normal ».

L'installation de l'environnement de travail de Zeste de Savoir est presque terminé. Le serveur Python a bien été installé (puisque vous avez installé Django), et ses dépendances également.


Accéder à votre site local 
==========================
Maintenant que tout est prêt, vous pouvez accéder à votre site local de Zeste de Savoir. C'est grâce à cela que vous pourrez tester les modifications de vos fichiers-sources de votre fork local. Cette étape est, bien sûr, indispensable. Vous êtes fortement invité à lire la partie 8, très courte.

Démarrez votre environnement virtuel.

Commande pour démarrer l'environnement virtuel :

.. sourcecode:: bash

    source <chemin pointant vers le répertoire de votre environnement virtuel>/bin/activate

Tapez la commande suivante pour lancer le serveur Python, qui permettra d'afficher le site Web et d'interpréter, bien évidemment, les divers fichiers-sources de votre fork local.

Commande pour démarrer le serveur Python de Django :

.. sourcecode:: bash

    python manage.py runserver

Considérez également les deux commandes suivantes.
Commande pour quitter le serveur Python :

.. sourcecode:: bash

    Appuyez sur CTRL + C.

Commande pour quitter l'environnement virtuel :

.. sourcecode:: bash

    deactivate

Pensez à d'abord quitter le serveur Python, et ensuite seulement vous pourrez quitter l'environnement virtuel (c'est plus propre).

Le site local se trouve à cette URL : http://127.0.0.1:8000/


Dans quel ordre dois-je travailler avec ces outils ?
====================================================
1- Ouvrez votre terminal, lancez votre environnement virtuel ;
2- Dans le terminal, démarrez votre serveur Python ;
3- Ouvrez votre navigateur Web, allez sur la page http://127.0.0.1:8000/ ;
4- Modifiez les fichiers-sources que vous voulez dans votre fork local et consultez/rafraîchissez la page précédemment citée pour tester vos modifications;
5- Une fois votre travail terminé : fermez votre serveur Python et fermez votre environnement virtuel ;
6- Sortez et faites du sport ! \o/


Aller plus loin
===============

Pour faire fonctionner ZdS dans son ensemble (ceci n'est pas obligatoire) vous pouvez installer les outils LateX,
Pandoc et les polices Microsoft.
Ce qui revient à lancer les commmandes suivantes :

.. sourcecode:: bash

    apt-get install --reinstall ttf-mscorefonts-installer
    apt-get install texlive texlive-xetex texlive-lang-french texlive-latex-extra
    apt-get install haskell-platform
    cabal update
    cabal install pandoc

Vous pouvez également `indiquer à Git de ne pas effectuer de commit s'il y a des erreurs de formatage dans le code <../utils/git-pre-hook.html>`__.
