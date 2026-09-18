#!/bin/bash

# Script de construction automatique de l'APK MINEXX Mobile
# Exécutez ce script depuis le répertoire racine du projet

echo "🚀 Début de la construction de l'APK MINEXX Mobile..."

# Vérifier que Flutter est installé
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter n'est pas installé ou n'est pas dans le PATH"
    echo "Veuillez installer Flutter depuis: https://flutter.dev/docs/get-started/install"
    exit 1
fi

# Afficher la version de Flutter
echo "✅ Flutter détecté:"
flutter --version

# Vérifier la configuration Flutter
echo "🔍 Vérification de la configuration Flutter..."
flutter doctor

# Nettoyer le projet
echo "🧹 Nettoyage du projet..."
flutter clean

# Installer les dépendances
echo "📦 Installation des dépendances..."
flutter pub get

# Générer les fichiers de code
echo "⚙️ Génération des fichiers de code..."
flutter packages pub run build_runner build --delete-conflicting-outputs

# Vérifier que la génération s'est bien passée
if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la génération des fichiers de code"
    exit 1
fi

# Construction de l'APK de debug
echo "🔨 Construction de l'APK de debug..."
flutter build apk --debug

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la construction de l'APK de debug"
    exit 1
fi

# Construction de l'APK de release
echo "🔨 Construction de l'APK de release..."
flutter build apk --release

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la construction de l'APK de release"
    exit 1
fi

# Construction des APK séparés par architecture
echo "🔨 Construction des APK par architecture..."
flutter build apk --split-per-abi --release

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la construction des APK par architecture"
    exit 1
fi

# Construction du bundle Android
echo "🔨 Construction du bundle Android..."
flutter build appbundle --release

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors de la construction du bundle Android"
    exit 1
fi

# Afficher les fichiers générés
echo "📁 Fichiers générés:"

DEBUG_APK="build/app/outputs/flutter-apk/app-debug.apk"
RELEASE_APK="build/app/outputs/flutter-apk/app-release.apk"
ARM64_APK="build/app/outputs/flutter-apk/app-arm64-v8a-release.apk"
ARM32_APK="build/app/outputs/flutter-apk/app-armeabi-v7a-release.apk"
X64_APK="build/app/outputs/flutter-apk/app-x86_64-release.apk"
BUNDLE="build/app/outputs/bundle/release/app-release.aab"

if [ -f "$DEBUG_APK" ]; then
    SIZE=$(du -h "$DEBUG_APK" | cut -f1)
    echo "✅ APK Debug: $DEBUG_APK ($SIZE)"
fi

if [ -f "$RELEASE_APK" ]; then
    SIZE=$(du -h "$RELEASE_APK" | cut -f1)
    echo "✅ APK Release: $RELEASE_APK ($SIZE)"
fi

if [ -f "$ARM64_APK" ]; then
    SIZE=$(du -h "$ARM64_APK" | cut -f1)
    echo "✅ APK ARM64: $ARM64_APK ($SIZE)"
fi

if [ -f "$ARM32_APK" ]; then
    SIZE=$(du -h "$ARM32_APK" | cut -f1)
    echo "✅ APK ARM32: $ARM32_APK ($SIZE)"
fi

if [ -f "$X64_APK" ]; then
    SIZE=$(du -h "$X64_APK" | cut -f1)
    echo "✅ APK x64: $X64_APK ($SIZE)"
fi

if [ -f "$BUNDLE" ]; then
    SIZE=$(du -h "$BUNDLE" | cut -f1)
    echo "✅ Bundle Android: $BUNDLE ($SIZE)"
fi

# Ouvrir le dossier des builds (Linux)
if command -v xdg-open &> /dev/null; then
    echo "📂 Ouverture du dossier des builds..."
    xdg-open "build/app/outputs/flutter-apk/"
elif command -v open &> /dev/null; then
    echo "📂 Ouverture du dossier des builds..."
    open "build/app/outputs/flutter-apk/"
fi

echo "🎉 Construction terminée avec succès !"
echo "📱 Vos APK sont prêts dans le dossier build/app/outputs/flutter-apk/"
echo "🔗 Pour installer sur un appareil connecté: flutter install --release"
