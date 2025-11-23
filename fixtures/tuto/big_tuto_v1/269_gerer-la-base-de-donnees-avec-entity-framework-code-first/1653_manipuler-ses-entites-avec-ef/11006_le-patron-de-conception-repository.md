Le patron de conception `Repository` a pour but de faire partir la ligne `ApplicationDbContext bdd = ApplicationDbContext.Create();` par une ligne plus "générique".

J'entends par là, que nous allons créer une *abstraction* supplémentaire permettant de remplacer *à la volée* un `ApplicationDbContext` par autre chose ne dépendant pas d'entity Framework.

[[q]]
|Tu nous apprends Entity Framework, mais tu veux le remplacer par autre chose, je ne comprends pas pourquoi?

En fait il existe des projets qui doivent pouvoir s'adapter à n'importe quel ORM, c'est rare, mais ça arrive.

Mais surtout, il faut bien comprendre qu'un site web, ça ne se développe pas n'importe comment.

En effet, si on simplifie beaucoup les choses, quand vous développez un site web, module par module, vous allez réfléchir en répétant inlassablement quatre étapes :

![Méthode de développement d'un projet](/media/galleries/304/0ff84a4e-cfb6-4d34-8987-e554e75ea885.png.960x960_q85.jpg)

Premièrement, nous essayons de comprendre de quoi on a besoin. Jusqu'à maintenant, nous avons fait le travail pour vous. Par exemple, comme nous voulons créer un blog, nous vous avons dit "il faudra ajouter, modifier, supprimer  des articles".

Le besoin est là, maintenant on va "concevoir". Là encore, nous vous avons bien dirigé jusqu'à présent. Par exemple, nous avons dit "un article est composé d'un texte, un titre, un auteur et éventuellement une icône".

Et là, vous avez commencé à coder. Et qu'avez-vous fait, pour voir que "ça marche"? Eh bien vous avez testé.

N'avez-vous pas remarqué que c'est long et répétitif?

Nous verrons plus tard dans le cours qu'il existe des outils qui testent **automatiquement** votre site. Mais comme ces tests ont pour but de vérifier que votre site fonctionne aussi bien quand l'utilisateur donne quelque chose de normal que des choses totalement hallucinantes, vous ne pouvez pas tester sur une base de données normale. Non seulement cela aurait pour effet de la polluer si les tests échouent mais en plus cela ralentirait vos tests.

Alors on va utiliser des astuces que nous utiliseront plus tard mais qui elles n'utilisent pas EntityFramework.

C'est pourquoi nous allons vouloir limiter les liens entre les contrôleurs et EntityFramework. Nous allons créer un Repository[^articles]
[^articles]: Vous trouverez des renseignements complémentaires [ici](http://niccou.wordpress.com/2012/03/27/design-pattern-repository/) et [ici](http://code.tutsplus.com/tutorials/the-repository-design-pattern--net-35804).

En fait le but sera de créer une interface qui permettra de gérer les entités.

Par exemple, une telle interface peut ressembler à ça pour nos articles :

```csharp
public interface EntityRepository<T> where T: class{
    IEnumerable<T> GetList(int skip = 0, int limit = 5);
    T Find(int id);
    void Save(T entity);
    void Delete(T entity);
    void Delete(int id);
}
```
Code: l'interface commune à tous les Repository

Et comme on veut pouvoir utiliser EntityFramework quand même, on crée une classe qui implémente cette interface :

```csharp
public class EFArticleRepository: EntityRepository<Article>{
    private ApplicationDbContext bdd = new ApplicationDbContext();
    public IEnumerable<Article> GetList(int skip = 0, int limit = 5){
        return bdd.Articles.OrderBy(a => a.ID).Skip(skip).Take(limit);
    }
    public Article Find(int id){
        return bdd.Articles.Find(id);
    }
    public void Save(Article entity){
        Article existing = bdd.Articles.Find(entity.id);
        if(existing == null){
           bdd.Articles.Add(entity);
        }else{
           bdd.Entry<Article>(existing).State = EntityState.Modified;
           bdd.Entry<Article>(existing).CurrentValues.SetValues(entity);
        }
        bdd.SaveChanges();
     }
    public void Delete(Article entity){
       bdd.Articles.Remove(entity);
    }
    public void Delete(int id){
        Delete(bdd.Articles.Find(id));
    }
}
```
Code: Le Repository complet qui utilise Entity Framework

Dans la suite du cours, nous n'utiliserons pas ce pattern afin de réduire la quantité de code que vous devrez comprendre. Néanmoins, sachez que dès que vous devrez tester une application qui utilise une base de données, il faudra en passer par là !
