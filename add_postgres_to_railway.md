# Guide pour ajouter PostgreSQL sur Railway

## Étape 1 : Ajouter une base de données PostgreSQL

1. **Allez sur Railway.app**
2. **Cliquez sur votre projet**
3. **Cliquez sur "New" → "Database" → "PostgreSQL"**
4. **Attendez que la base de données soit créée**

## Étape 2 : Connecter l'application à la base de données

1. **Dans votre projet Railway**
2. **Cliquez sur votre application Django**
3. **Allez dans l'onglet "Variables"**
4. **Ajoutez la variable `DATABASE_URL`** avec la valeur fournie par Railway

## Étape 3 : Redéployer

1. **Cliquez sur "Deploy"** pour redéployer l'application
2. **Attendez que le déploiement se termine**

## Étape 4 : Vérifier

1. **Testez votre URL :** `https://minexx-production.up.railway.app`
2. **L'application devrait maintenant fonctionner !**

## Variables d'environnement à ajouter :

- `DATABASE_URL` : URL PostgreSQL fournie par Railway
- `DEBUG` : `False` pour la production
- `SECRET_KEY` : Votre clé secrète Django
- `ALLOWED_HOSTS` : `.railway.app`

## En cas de problème :

1. **Vérifiez les logs Railway** pour voir les erreurs
2. **Assurez-vous que PostgreSQL est bien créé**
3. **Vérifiez que `DATABASE_URL` est correctement définie** 