# 🚀 Déploiement Railway - MINEXX

## 🎯 **Railway : La Solution Parfaite pour Django**

Railway est idéal pour votre projet MINEXX car il offre :
- ✅ **PostgreSQL gratuit** inclus
- ✅ **Déploiement automatique** depuis GitHub
- ✅ **SSL gratuit**
- ✅ **Monitoring** et logs
- ✅ **Backup automatique** de la base de données

## 📋 **Étapes de Déploiement**

### **Étape 1 : Créer un compte Railway**

1. **Aller sur [Railway.app](https://railway.app)**
2. **Cliquer sur "Start a New Project"**
3. **Se connecter avec GitHub**
4. **Autoriser l'accès à vos repositories**

### **Étape 2 : Déployer depuis GitHub**

1. **Cliquer sur "Deploy from GitHub repo"**
2. **Sélectionner le repository : `ASOFES/minexx`**
3. **Railway détectera automatiquement Django**
4. **Cliquer sur "Deploy Now"**

### **Étape 3 : Configurer la Base de Données**

1. **Dans le dashboard Railway, cliquer sur "New"**
2. **Sélectionner "Database" → "PostgreSQL"**
3. **Attendre que la base de données soit créée**
4. **Copier l'URL de connexion PostgreSQL**

### **Étape 4 : Configurer les Variables d'Environnement**

Dans le dashboard Railway, aller dans "Variables" et ajouter :

```env
DEBUG=False
SECRET_KEY=django-insecure-votre-clé-secrète-très-longue
ALLOWED_HOSTS=.railway.app
DATABASE_URL=postgresql://user:password@host:port/database
```

**Note :** Railway générera automatiquement `DATABASE_URL` si vous avez ajouté une base de données PostgreSQL.

### **Étape 5 : Déployer l'Application**

1. **Railway redéploiera automatiquement**
2. **Attendre que le build soit terminé**
3. **Vérifier les logs pour s'assurer que tout fonctionne**

## 🔧 **Configuration Avancée**

### **Variables d'Environnement Recommandées :**

```env
# Django
DEBUG=False
SECRET_KEY=django-insecure-votre-clé-secrète-très-longue
ALLOWED_HOSTS=.railway.app

# Base de données (généré automatiquement par Railway)
DATABASE_URL=postgresql://user:password@host:port/database

# Email (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
EMAIL_USE_TLS=True

# Fichiers statiques
STATIC_URL=/static/
STATIC_ROOT=staticfiles/
```

### **Configuration des Fichiers Statiques :**

Railway servira automatiquement les fichiers statiques. Assurez-vous que dans `settings.py` :

```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

## 🗄️ **Base de Données PostgreSQL**

### **Avantages PostgreSQL sur Railway :**
- ✅ **Gratuit** pour les projets personnels
- ✅ **Backup automatique** quotidien
- ✅ **Monitoring** en temps réel
- ✅ **Connexion sécurisée** SSL
- ✅ **Performance optimale**

### **Migration de SQLite vers PostgreSQL :**

Si vous avez des données dans SQLite :

```bash
# Exporter les données
python manage.py dumpdata > data.json

# Après déploiement sur Railway
python manage.py loaddata data.json
```

## 📊 **Monitoring et Logs**

### **Accès aux Logs :**
1. **Dashboard Railway** → Votre projet
2. **Onglet "Deployments"**
3. **Cliquer sur le dernier déploiement**
4. **Voir les logs en temps réel**

### **Monitoring :**
- ✅ **CPU et RAM** utilisés
- ✅ **Requêtes** par minute
- ✅ **Erreurs** en temps réel
- ✅ **Performance** de la base de données

## 🚀 **URLs de Déploiement**

Après le déploiement, votre application sera disponible sur :
- **Application :** `https://minexx-production.up.railway.app`
- **Admin Django :** `https://minexx-production.up.railway.app/admin/`

## 👤 **Superutilisateur**

Créer un admin via les variables d'environnement :
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_PASSWORD`
- `DJANGO_SUPERUSER_EMAIL` (optionnel)
- `DJANGO_SUPERUSER_ROLE=admin` (important pour le rôle métier)

## 🔄 **Mise à Jour Continue**

Chaque fois que vous poussez du code vers GitHub :
1. **Railway détecte automatiquement les changements**
2. **Relance le build**
3. **Applique les migrations automatiquement**
4. **Déploie la nouvelle version**

## 🆘 **Dépannage**

### **Problèmes courants :**

1. **Erreur de migration :**
   ```bash
   # Dans les logs Railway
   python manage.py migrate --run-syncdb
   ```

2. **Fichiers statiques manquants :**
   ```bash
   # Dans les logs Railway
   python manage.py collectstatic --noinput
   ```

3. **Erreur de base de données :**
   - Vérifier que `DATABASE_URL` est correct
   - S'assurer que la base de données PostgreSQL est active

4. **Erreur 500 :**
   - Vérifier les logs Railway
   - S'assurer que `DEBUG=False` en production

## 📈 **Avantages Railway**

| Fonctionnalité | Railway | Heroku | Netlify |
|----------------|---------|--------|---------|
| **Base de données** | ✅ PostgreSQL | ✅ PostgreSQL | ❌ Non |
| **Django complet** | ✅ Parfait | ✅ Excellent | ❌ Non |
| **Gratuit** | ✅ Oui | ❌ Payant | ✅ Oui |
| **SSL** | ✅ Oui | ✅ Oui | ✅ Oui |
| **Monitoring** | ✅ Oui | ✅ Oui | ❌ Non |
| **Backup DB** | ✅ Oui | ❌ Payant | ❌ Non |

## 🎯 **Étapes Finales**

1. **Déployer sur Railway** (suivre les étapes ci-dessus)
2. **Tester l'application** sur l'URL fournie
3. **Se connecter à l'admin** Django
4. **Créer des données de test**
5. **Partager l'URL** avec vos utilisateurs

---

**🚀 Votre application MINEXX sera bientôt en ligne avec une base de données PostgreSQL solide !** 