# Interface contenus
## TODOs
- [x] Dans une (sous)catégorie, les flux RSS/Atom pour Derniers articles / derniers tutoriels doivent n’afficher que les contenus de la (sous)catégorie dans laquelle on se trouve
- [ ] Résoudre les TODOs en commentaire HTML

---

## Niveaux
1. lvl `1`: bibliothèque
  * point d’entrée
  * recherche
2. lvl `2`: bibliothèque > Informatique
  * on vient de lvl `1`
  * recherche
3. lvl `3`: bibliothèque > Informatique > OS
  * on vient de lvl `2`
  * recherche
4. lvl `4`: bibliothèque > Parcourir
  * on y arrive par “Plus de foo (dans bar)” dispo sur lvl `1`, `2` , `3`
  * pas de recherche
  * pré-filtré par type + (sous)catégorie
    * les filtres sont affichés à la place de la recherche
  * affichage en 2 colonnes, mais qu'une seule :
    1 2
    3 4
    5 6
  * (tri par date?) (tri par alphabétique?)
  * pagination
