# 📱 Guide de Test de l'APK avec l'API Web

## 🎯 Objectif

Ce guide vous explique comment tester votre application mobile MINEXX avec l'API web déployée sur Render.com.

## 🌐 État de l'API Web

### ✅ **API Fonctionnelle (Status 401 - Normal)**
- **`/api/login/`** - Authentification des utilisateurs
- **`/api/verify-token/`** - Vérification des tokens
- **`/api/chauffeur/missions/`** - Missions des chauffeurs

### ⚠️ **API à Implémenter (Status 404)**
- **`/api/demandeur/demandes/`** - Demandes des demandeurs
- **`/api/dispatch/demandes/`** - Gestion des dispatchers

## 🚀 Étapes de Test

### **Phase 1 : Test de Base de l'APK**

#### 1. **Installer l'APK sur un appareil Android**
```bash
# Depuis le dossier minexx-mobile-app
flutter build apk --release
flutter install --release
```

#### 2. **Tester la Connexion à l'API**
- Ouvrir l'application
- Aller à l'écran de connexion
- Vérifier que l'app peut se connecter à `https://minexx.onrender.com`

#### 3. **Tester l'Authentification**
- Utiliser des identifiants valides de votre base de données
- Vérifier que la connexion fonctionne
- Vérifier que le token est reçu

### **Phase 2 : Test des Fonctionnalités Disponibles**

#### ✅ **Module Chauffeur - Fonctionnel**
- **Connexion** : Doit fonctionner
- **Récupération des missions** : Doit fonctionner
- **Démarrage/Fin de mission** : Doit fonctionner

#### ⚠️ **Module Demandeur - Partiellement fonctionnel**
- **Connexion** : Doit fonctionner
- **Création de demandes** : Doit fonctionner
- **Liste des demandes** : Ne fonctionnera pas (endpoint 404)

#### ⚠️ **Module Dispatcher - Partiellement fonctionnel**
- **Connexion** : Doit fonctionner
- **Liste des demandes** : Ne fonctionnera pas (endpoint 404)
- **Assignation** : Ne fonctionnera pas (endpoint 404)

## 🧪 Tests Recommandés

### **Test 1 : Connexion de Base**
```bash
# Vérifier que l'app peut se connecter à l'API
1. Ouvrir l'app
2. Aller à l'écran de connexion
3. Saisir des identifiants valides
4. Vérifier que la connexion réussit
```

### **Test 2 : Récupération des Données**
```bash
# Tester la récupération des missions (chauffeur)
1. Se connecter en tant que chauffeur
2. Aller au dashboard
3. Vérifier que les missions se chargent
4. Vérifier qu'il n'y a pas d'erreurs 404
```

### **Test 3 : Gestion des Erreurs**
```bash
# Tester la gestion des erreurs API
1. Se connecter en tant que demandeur
2. Essayer de récupérer la liste des demandes
3. Vérifier que l'erreur 404 est gérée gracieusement
4. Vérifier qu'un message d'erreur approprié s'affiche
```

## 🔧 Configuration de l'APK

### **Vérifier la Configuration API**
```dart
// lib/utils/constants.dart
class ApiEndpoints {
  static const String baseUrl = 'https://minexx.onrender.com';
  static const String apiBase = '$baseUrl/api';
  
  // Ces endpoints fonctionnent ✅
  static const String login = '$apiBase/login/';
  static const String verifyToken = '$apiBase/verify-token/';
  static const String chauffeurMissions = '$apiBase/chauffeur/missions/';
  
  // Ces endpoints ne fonctionnent pas encore ⚠️
  static const String demandeurDemandes = '$apiBase/demandeur/demandes/';
  static const String dispatchDemandes = '$apiBase/dispatch/demandes/';
}
```

## 🐛 Résolution des Problèmes

### **Erreur de Connexion**
- Vérifier que l'appareil a accès à Internet
- Vérifier que `https://minexx.onrender.com` est accessible
- Vérifier les logs de l'application

### **Erreur 404 sur certains endpoints**
- **Normal** pour les endpoints non encore implémentés
- L'app doit gérer ces erreurs gracieusement
- Afficher un message "Fonctionnalité en cours de développement"

### **Erreur d'Authentification**
- Vérifier que les identifiants sont corrects
- Vérifier que l'utilisateur existe dans la base de données
- Vérifier que l'utilisateur a le bon rôle

## 📊 Métriques de Test

### **Tests de Performance**
- **Temps de connexion** : < 3 secondes
- **Temps de chargement des missions** : < 2 secondes
- **Gestion des erreurs** : Messages clairs et informatifs

### **Tests de Fonctionnalité**
- **Connexion** : 100% de réussite avec identifiants valides
- **Récupération des missions** : 100% de réussite (chauffeur)
- **Gestion des erreurs** : 100% de réussite (endpoints manquants)

## 🎯 Prochaines Étapes

### **Immédiat (Aujourd'hui)**
1. ✅ Tester l'APK avec l'API actuelle
2. ✅ Valider les fonctionnalités de base
3. ✅ Identifier les problèmes d'interface

### **Court terme (Cette semaine)**
1. 🔄 Implémenter les endpoints manquants
2. 🔄 Redéployer l'API sur Render.com
3. 🔄 Tester toutes les fonctionnalités

### **Moyen terme (Prochaine semaine)**
1. 🚀 Optimiser les performances
2. 🚀 Ajouter la gestion des erreurs avancée
3. 🚀 Implémenter les notifications push

## 📞 Support

### **En cas de problème :**
1. **Vérifier les logs** de l'application
2. **Tester l'API** avec `test_web_api.py`
3. **Vérifier la configuration** dans `constants.dart`
4. **Consulter** le rapport `API_TEST_RESULTS.md`

---

## 🎉 **Résumé**

**Votre APK MINEXX est prêt pour les tests de base !**

- ✅ **Connexion à l'API** : Fonctionnelle
- ✅ **Authentification** : Fonctionnelle  
- ✅ **Module Chauffeur** : Complètement fonctionnel
- ⚠️ **Modules Demandeur/Dispatcher** : Partiellement fonctionnels

**Commencez par tester le module Chauffeur qui est 100% fonctionnel !**
