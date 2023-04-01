Commençons par créer un modèle assez simple. Le modèle va contenir les données de notre application. Pour celle-ci, ce sera simple : nous n'avons que le prénom du visiteur à récupérer.

Le visiteur va rentrer son prénom et celui-ci va être stocké dans une propriété **Prenom**. Nous allons donc créer une classe **Visiteur** contenant une unique propriété. Pour créer une classe, utilisons le clique droit de la souris sur le répertoire Models, puis Ajouter > Classe...

![Ajouter une classe de modèle](/media/galleries/304/653da272-8dd3-4930-b204-f9a895f8bb7a.png.960x960_q85.png)

Visual Studio Express pour le Web génère le code suivant :

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace BonjourMVC.Models
{
    public class Visiteur
    {
    }
}
```

Rajoutons maintenant notre propriété `Prenom`. Le visiteur va rentrer son prénom dans un champ de texte, donc la propriété sera de type `string`. Ce qui donne :

```csharp
public class Visiteur
{
    public string Prenom { get; set; }
}
```

C'est bon pour le modèle. Notre classe ne contient quasiment rien mais ce sera suffisant pour notre application. Prochaine étape : le contrôleur.
