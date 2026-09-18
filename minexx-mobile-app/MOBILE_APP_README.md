# 🚗 Application Mobile MINEXX

## 📱 Vue d'ensemble

L'**Application Mobile MINEXX** est une solution Flutter complète qui se connecte à votre backend Django pour la gestion des véhicules et missions. Elle offre trois interfaces distinctes selon le rôle de l'utilisateur.

## 🎯 Modules et Rôles

### 1. **Chauffeur** 🚙
- **Voir les courses assignées** : Liste des missions en attente et assignées
- **Démarrer une course** : Saisie du kilométrage avant départ
- **Terminer une course** : Saisie du kilométrage final
- **Historique des courses** : Consultation des missions terminées
- **Gestion de session** : Connexion/déconnexion sécurisée

### 2. **Dispatcher** 📋
- **Voir les demandes de missions** : Liste de toutes les missions en attente
- **Assigner les missions** : Attribution aux chauffeurs et véhicules
- **Historique d'assignation** : Suivi des missions assignées
- **Suivi des courses** : Monitoring en temps réel

### 3. **Demandeur de Mission** 📝
- **Nouvelle demande** : Création de missions avec détails complets
- **Historique des demandes** : Consultation de ses propres missions
- **Suivi du statut** : Évolution de la demande jusqu'à la livraison

## 🔧 Architecture Technique

### **Frontend**
- **Framework** : Flutter 3.10+
- **Langage** : Dart 3.0+
- **État** : Provider + GetX
- **Navigation** : Navigation par onglets adaptée au rôle

### **Backend**
- **API** : Django REST Framework
- **Authentification** : JWT Token
- **Base de données** : PostgreSQL (Supabase)
- **Notifications** : Firebase Cloud Messaging

### **Fonctionnalités**
- ✅ **Authentification par rôle** avec JWT
- ✅ **Interface adaptée** selon le profil utilisateur
- ✅ **Notifications push** en temps réel
- ✅ **Mode hors ligne** avec synchronisation
- ✅ **Gestion des sessions** sécurisée
- ✅ **Responsive design** pour tous les écrans

## 📱 Fonctionnalités Principales

### **Authentification et Sécurité**
- Connexion sécurisée avec nom d'utilisateur/mot de passe
- Gestion des tokens JWT (access + refresh)
- Stockage sécurisé des données sensibles
- Déconnexion automatique en cas d'expiration

### **Gestion des Missions**
- **Création** : Formulaire complet avec validation
- **Assignation** : Attribution chauffeur + véhicule
- **Suivi** : Statuts en temps réel (en attente → assignée → en cours → terminée)
- **Historique** : Consultation des missions passées

### **Gestion des Courses**
- **Démarrage** : Saisie kilométrage initial
- **Suivi** : Statut en cours avec notifications
- **Terminaison** : Saisie kilométrage final
- **Rapports** : Génération automatique des rapports

### **Notifications**
- **Push notifications** pour les changements de statut
- **Notifications locales** pour les actions importantes
- **Sons et vibrations** configurables
- **Badges** sur l'icône de l'application

## 🚀 Installation et Configuration

### **Prérequis**
```bash
# Flutter SDK
flutter --version  # >= 3.10.0

# Dépendances système
# - Android Studio / Xcode
# - Git
# - Java 11+ (Android)
```

### **Installation**
```bash
# Cloner le projet
git clone [URL_DU_REPO_MINEXX_MOBILE]

# Aller dans le dossier
cd minexx-mobile-app

# Installer les dépendances
flutter pub get

# Vérifier la configuration
flutter doctor
```

### **Configuration**
1. **URL de l'API** : Modifier `lib/config/app_config.dart`
2. **Firebase** : Configurer `google-services.json` (Android) et `GoogleService-Info.plist` (iOS)
3. **Permissions** : Vérifier les permissions dans `android/app/src/main/AndroidManifest.xml`

## 📊 Structure du Projet

```
minexx-mobile-app/
├── lib/
│   ├── main.dart                 # Point d'entrée principal
│   ├── config/
│   │   └── app_config.dart      # Configuration globale
│   ├── models/
│   │   ├── user_model.dart      # Modèle utilisateur
│   │   ├── mission_model.dart   # Modèle mission
│   │   └── vehicule_model.dart  # Modèle véhicule
│   ├── services/
│   │   ├── auth_service.dart    # Service d'authentification
│   │   └── notification_service.dart # Service notifications
│   ├── providers/
│   │   ├── auth_provider.dart   # Provider authentification
│   │   └── mission_provider.dart # Provider missions
│   ├── screens/
│   │   ├── login_screen.dart    # Écran de connexion
│   │   ├── home_screen.dart     # Écran principal
│   │   └── [autres écrans...]
│   └── widgets/
│       ├── custom_text_field.dart # Champs personnalisés
│       └── custom_button.dart     # Boutons personnalisés
├── assets/
│   ├── images/                   # Images de l'application
│   ├── icons/                    # Icônes personnalisées
│   ├── animations/               # Animations Lottie
│   └── fonts/                    # Polices personnalisées
├── android/                      # Configuration Android
├── ios/                         # Configuration iOS
└── pubspec.yaml                 # Dépendances Flutter
```

## 🔐 Configuration de l'API

### **Variables d'environnement**
```dart
// lib/config/app_config.dart
static const String baseUrl = 'https://votre-app-render.onrender.com';
static const String apiVersion = '/api/v1';
static const String apiUrl = baseUrl + apiVersion;
```

### **Endpoints requis**
- `POST /api/v1/auth/login/` - Connexion
- `POST /api/v1/auth/logout/` - Déconnexion
- `POST /api/v1/auth/refresh/` - Rafraîchissement token
- `GET /api/v1/missions/` - Liste des missions
- `POST /api/v1/missions/` - Créer une mission
- `PUT /api/v1/missions/{id}/` - Mettre à jour une mission
- `GET /api/v1/vehicules/` - Liste des véhicules

## 📱 Interface Utilisateur

### **Design System**
- **Couleurs** : Palette MINEXX (bleu principal #1976D2)
- **Typographie** : Police Poppins (Regular, Medium, SemiBold, Bold)
- **Composants** : Boutons, champs, cartes personnalisés
- **Animations** : Transitions fluides et feedback visuel

### **Responsive Design**
- **Mobile** : Interface optimisée pour smartphones
- **Tablette** : Adaptation automatique des layouts
- **Orientation** : Support portrait et paysage

## 🔔 Système de Notifications

### **Types de notifications**
- **Info** : Informations générales
- **Succès** : Actions réussies
- **Avertissement** : Attention requise
- **Erreur** : Problèmes détectés
- **Urgent** : Actions immédiates

### **Configuration Firebase**
1. Créer un projet Firebase
2. Ajouter l'application Android/iOS
3. Télécharger les fichiers de configuration
4. Activer Cloud Messaging

## 🗄️ Gestion des Données

### **Stockage Local**
- **SQLite** : Base de données locale pour le cache
- **SharedPreferences** : Paramètres utilisateur
- **Secure Storage** : Tokens d'authentification

### **Synchronisation**
- **Mode hors ligne** : Fonctionnement sans connexion
- **Sync automatique** : Mise à jour lors du retour en ligne
- **Gestion des conflits** : Résolution automatique

## 🧪 Tests et Débogage

### **Tests unitaires**
```bash
flutter test
```

### **Tests d'intégration**
```bash
flutter test integration_test/
```

### **Mode debug**
```bash
flutter run --debug
```

## 📦 Build et Déploiement

### **Build Android**
```bash
# APK de debug
flutter build apk --debug

# APK de release
flutter build apk --release

# Bundle AAB (Google Play)
flutter build appbundle --release
```

### **Build iOS**
```bash
# Archive pour App Store
flutter build ios --release
```

### **Configuration de production**
- **Code obfuscation** : Protection du code source
- **Signing** : Certificats de production
- **Optimisations** : Performance et taille

## 🔧 Maintenance et Mises à Jour

### **Gestion des versions**
- **Versioning sémantique** : MAJOR.MINOR.PATCH
- **Changelog** : Documentation des changements
- **Rollback** : Retour à la version précédente

### **Monitoring**
- **Crashlytics** : Suivi des erreurs
- **Analytics** : Métriques d'utilisation
- **Performance** : Mesures de performance

## 📞 Support et Documentation

### **Documentation API**
- **Swagger/OpenAPI** : Documentation interactive
- **Exemples** : Cas d'usage concrets
- **Codes d'erreur** : Gestion des erreurs

### **Support utilisateur**
- **Guide utilisateur** : Documentation complète
- **FAQ** : Questions fréquentes
- **Contact** : Support technique

## 🚀 Roadmap Future

### **Phase 2** (Q1 2026)
- [ ] **Géolocalisation** : Suivi GPS des véhicules
- [ ] **QR Codes** : Scan des documents
- [ ] **Signature électronique** : Validation des missions
- [ ] **Mode sombre** : Interface adaptée

### **Phase 3** (Q2 2026)
- [ ] **Intelligence artificielle** : Optimisation des routes
- [ ] **Analytics avancés** : Tableaux de bord
- [ ] **Intégration ERP** : Synchronisation complète
- [ ] **API publique** : Développeurs tiers

---

## 📋 Checklist de Déploiement

### **Pré-déploiement**
- [ ] Tests unitaires passent
- [ ] Tests d'intégration validés
- [ ] Configuration API vérifiée
- [ ] Permissions configurées
- [ ] Notifications testées

### **Déploiement**
- [ ] Build de production créé
- [ ] Signing appliqué
- [ ] Tests sur appareils réels
- [ ] Validation des fonctionnalités
- [ ] Upload vers stores

### **Post-déploiement**
- [ ] Monitoring activé
- [ ] Analytics configurés
- [ ] Support utilisateur prêt
- [ ] Documentation mise à jour
- [ ] Formation équipe

---

*Application Mobile MINEXX - Version 1.0.0*  
*Développée avec Flutter pour la gestion des véhicules et missions*
