ZDS utilise Solr, un moteur de recherche très performant développé par la fondation APACHE.  
Installer Solr est **nécessaire** dès que le site propose une recherche :

# Prérequis sur linux

Pour installer Solr, une multitude de choix est opérable. Une des plus simples est 
d'utiliser les exemples embarqués avec le paquet de release.

Avant toute chose soyez-sûr avoir [JAVA](http://www.java.com/fr/download/manual.jsp#lin).



téléchargez [l'archive SOLR](http://apache.crihan.fr/dist/lucene/solr/4.9.0/solr-4.9.0.zip) ou entrez la commande
`wget http://apache.crihan.fr/dist/lucene/solr/4.9.0/solr-4.9.0.zip`.

puis, décompressez l'archive avec `unzip solr-4.9.0.zip`.

# Prérequis sur windows

Pour installer SOLR, une multitude de choix est opérable. Une des plus simples est 
d'utiliser les exemples embarqués avec le paquet de release.

Avant toute chose soyez-sûr avoir [JAVA](http://www.java.com/fr/download/win8.jsp).

Ajoutez le dossier contenant java à votre PATH :

Dans "Ordinateur", clic droit puis "Proprétés", ouvrez les "propriétés avancées" puis cliquez sur "Variables d'environnement".

téléchargez [l'archive SOLR](http://apache.crihan.fr/dist/lucene/solr/4.9.0/solr-4.9.0.zip). Décompressez-la.

# Procédure commune

Ouvrez le terminal ou powershell.

A la racine de votre dépot zds, lancez la commande :

```
python manage.py build_solr_schema > %solr_home%/example/solr/collection1/conf/schema.xml
```

Placez-vous dans le dossier contenant solr exécutez :

```bash

cd solr-4.9.0/example/
java -jar start.jar

```

Vérifiez que solr est fonctionnel en entrant dans votre navigateur l'url http://localhost:8983/solr/

Maintenant que Solr est prêt, allez à la racine de votre dépôt zeste de savoir, une fois votre virtualenv activé entrez

```bash
python manage.py rebuild_index
```
Une fois terminé, vous avez une recherche fonctionnelle.