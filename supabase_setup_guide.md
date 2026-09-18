# Guide de Configuration Supabase

## 🚀 Étape 1 : Créer un compte Supabase

1. **Allez sur** [supabase.com](https://supabase.com)
2. **Cliquez sur "Start your project"**
3. **Connectez-vous avec GitHub**
4. **Créez un nouveau projet**

## 📋 Étape 2 : Configurer le projet

1. **Nom du projet :** `minexx-database`
2. **Mot de passe de base de données :** `<DEFINIR_VIA_ENV>`
3. **Région :** `West Europe` (ou la plus proche)
4. **Cliquez sur "Create new project"**

## 🔧 Étape 3 : Récupérer les informations de connexion

1. **Dans votre projet Supabase**
2. **Allez dans "Settings" → "Database"**
3. **Copiez les informations :**
   - **Host :** `db.xxxxxxxxxxxxx.supabase.co`
   - **Database name :** `postgres`
   - **Port :** `5432`
   - **User :** `postgres`
   - **Password :** `<DEFINIR_VIA_ENV>`

## 🌐 Étape 4 : Configurer Railway avec Supabase

1. **Allez sur Railway.app**
2. **Cliquez sur votre projet**
3. **Allez dans "Variables"**
4. **Ajoutez ces variables :**

```
SUPABASE_URL=db.xxxxxxxxxxxxx.supabase.co
SUPABASE_DB_PASSWORD=<DEFINIR_VIA_ENV>
```

## 🔄 Étape 5 : Redéployer

1. **Poussez les changements sur GitHub**
2. **Railway va automatiquement redéployer**
3. **L'application utilisera maintenant Supabase**

## ✅ Vérification

1. **Testez votre URL :** `https://minexx-production.up.railway.app`
2. **L'application devrait maintenant fonctionner !**

## 🔍 Avantages de Supabase

- ✅ **PostgreSQL gratuit** (500MB)
- ✅ **Interface web** pour gérer la DB
- ✅ **API REST automatique**
- ✅ **Authentification intégrée**
- ✅ **Très fiable et rapide**
- ✅ **Backup automatique**

## 📞 Support

Si vous avez des problèmes :
1. **Vérifiez les logs Railway**
2. **Vérifiez la connexion Supabase**
3. **Testez la connexion locale** 