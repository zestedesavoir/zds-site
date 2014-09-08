===========
Les Membres
===========


L'interface de promotion
------------------------

Afin de pouvoir gérer les membres directement depuis le site (c'est à dire sans avoir besoin de passer par l'interface d'administration de Django), une interface de promotion a été développée.
Cette interface permet de :
1. Ajouter/Supprimer un membre dans un/des groupe(s)
2. Ajouter/Supprimer le statut super-utilisateur à un membre
3. (Dés)activer un compte

Le premier point permet notamment de passer un membre dans le groupe staff ou développeur. Si d'autres groupes voient le jour (valido ?) alors il sera possible ici aussi de le changer.
Le second point permet de donner accès au membre à l'interface Django et à cette interface de promotion.
Enfin, le dernier point concerne simplement l'activation du compte (normalement faite par le membre à l'inscription).

Elle est géré par le formulaire `PromoteMemberForm` présent dans le fichier `zds/member/forms.py`.
Elle est ensuite visible via le template `member/settings/promote.html` qui peut-être accédé en tant que super-utilisateur via le profil de n'importe quel membre.