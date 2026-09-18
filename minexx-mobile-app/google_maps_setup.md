# Configuration Google Maps pour MINEXX Mobile App

## 🗺️ Vue d'ensemble

Ce guide explique comment configurer Google Maps pour l'application mobile MINEXX, incluant l'obtention des clés API et la configuration des plateformes.

## 🔑 1. Obtenir une clé API Google Maps

### 1.1 Accéder à Google Cloud Console
1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet ou sélectionner un projet existant
3. Activer l'API Google Maps Platform

### 1.2 Activer les APIs nécessaires
- **Maps SDK for Android**
- **Maps SDK for iOS**
- **Directions API**
- **Geocoding API**
- **Places API**

### 1.3 Créer une clé API
1. Aller dans "APIs & Services" > "Credentials"
2. Cliquer sur "Create Credentials" > "API Key"
3. Copier la clé générée

## 📱 2. Configuration Android

### 2.1 Ajouter la clé API
Dans `android/app/src/main/AndroidManifest.xml` :
```xml
<manifest ...>
  <application ...>
    <meta-data
        android:name="com.google.android.geo.API_KEY"
        android:value="VOTRE_CLE_API_ICI"/>
  </application>
</manifest>
```

### 2.2 Permissions requises
```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 2.3 Configuration build.gradle
Dans `android/app/build.gradle` :
```gradle
android {
    defaultConfig {
        minSdkVersion 21
        targetSdkVersion 33
    }
}
```

## 🍎 3. Configuration iOS

### 3.1 Ajouter la clé API
Dans `ios/Runner/AppDelegate.swift` :
```swift
import UIKit
import Flutter
import GoogleMaps

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    GMSServices.provideAPIKey("VOTRE_CLE_API_ICI")
    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
}
```

### 3.2 Permissions requises
Dans `ios/Runner/Info.plist` :
```xml
<key>NSLocationWhenInUseUsageDescription</key>
<string>Cette application nécessite l'accès à la localisation pour la navigation et le suivi des missions.</string>
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>Cette application nécessite l'accès à la localisation pour la navigation et le suivi des missions.</string>
```

## 🚀 4. Configuration de l'application

### 4.1 Mettre à jour la clé API
Dans `lib/services/maps_service.dart` :
```dart
class MapsService {
  static const String _googleApiKey = 'VOTRE_CLE_API_ICI';
  // ... reste du code
}
```

### 4.2 Variables d'environnement (recommandé)
Créer un fichier `.env` :
```bash
GOOGLE_MAPS_API_KEY=VOTRE_CLE_API_ICI
```

## 🔒 5. Sécurité et restrictions

### 5.1 Restreindre la clé API
1. Aller dans Google Cloud Console > "APIs & Services" > "Credentials"
2. Cliquer sur votre clé API
3. Dans "Application restrictions", sélectionner "Android apps" et/ou "iOS apps"
4. Ajouter les identifiants de votre application

### 5.2 Restreindre les APIs
1. Dans "API restrictions", sélectionner "Restrict key"
2. Sélectionner uniquement les APIs nécessaires

## 📊 6. Monitoring et facturation

### 6.1 Activer la facturation
- Google Maps Platform nécessite un compte de facturation activé
- Les premiers 200$ par mois sont gratuits
- Surveiller l'utilisation dans Google Cloud Console

### 6.2 Quotas recommandés
- **Maps SDK for Android/iOS** : 1000 requêtes/jour
- **Directions API** : 1000 requêtes/jour
- **Geocoding API** : 1000 requêtes/jour

## 🧪 7. Test de l'intégration

### 7.1 Tester sur émulateur
```bash
flutter run
```

### 7.2 Tester sur appareil physique
- Assurez-vous que la localisation est activée
- Vérifiez les permissions de l'application

### 7.3 Vérifier les logs
```bash
flutter logs
```

## 🚨 8. Dépannage courant

### 8.1 Erreur "API key not valid"
- Vérifier que la clé API est correcte
- Vérifier que l'API est activée
- Vérifier les restrictions de la clé

### 8.2 Carte ne s'affiche pas
- Vérifier la connexion internet
- Vérifier les permissions de localisation
- Vérifier la configuration du projet

### 8.3 Navigation ne fonctionne pas
- Vérifier que Directions API est activée
- Vérifier les quotas de l'API
- Vérifier la clé API dans le code

## 📱 9. Fonctionnalités implémentées

### 9.1 Carte interactive
- Affichage de Google Maps
- Marqueurs pour missions, véhicules, chauffeurs
- Zones de service
- Centrage automatique sur la position

### 9.2 Navigation GPS
- Calcul d'itinéraires
- Navigation en temps réel
- Suivi de position
- Notifications d'arrivée

### 9.3 Géolocalisation
- Position actuelle
- Calcul de distances
- Géocodage
- Zones géographiques

## 🎯 10. Prochaines étapes

### 10.1 Améliorations possibles
- Navigation par étapes
- Alertes de trafic en temps réel
- Points d'intérêt
- Historique des trajets

### 10.2 Optimisations
- Mise en cache des cartes
- Compression des données
- Mode hors ligne
- Gestion de la batterie

## 📚 11. Ressources utiles

- [Documentation Google Maps Flutter](https://pub.dev/packages/google_maps_flutter)
- [Google Maps Platform](https://developers.google.com/maps)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Flutter Documentation](https://flutter.dev/docs)

## 🎉 12. Conclusion

Avec cette configuration, votre application MINEXX dispose maintenant de :
- ✅ Cartes Google Maps interactives
- ✅ Navigation GPS en temps réel
- ✅ Géolocalisation précise
- ✅ Calcul d'itinéraires
- ✅ Suivi de position

L'application est prête pour un usage professionnel avec des fonctionnalités de cartographie avancées !
