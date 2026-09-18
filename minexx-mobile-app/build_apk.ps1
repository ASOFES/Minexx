# Script de construction automatique de l'APK MINEXX Mobile
# Exécutez ce script depuis le répertoire racine du projet

Write-Host "🚀 Début de la construction de l'APK MINEXX Mobile..." -ForegroundColor Green

# Vérifier que Flutter est installé
try {
    $flutterVersion = flutter --version
    Write-Host "✅ Flutter détecté:" -ForegroundColor Green
    Write-Host $flutterVersion -ForegroundColor Cyan
} catch {
    Write-Host "❌ Flutter n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "Veuillez installer Flutter depuis: https://flutter.dev/docs/get-started/install" -ForegroundColor Yellow
    exit 1
}

# Vérifier la configuration Flutter
Write-Host "🔍 Vérification de la configuration Flutter..." -ForegroundColor Yellow
flutter doctor

# Nettoyer le projet
Write-Host "🧹 Nettoyage du projet..." -ForegroundColor Yellow
flutter clean

# Installer les dépendances
Write-Host "📦 Installation des dépendances..." -ForegroundColor Yellow
flutter pub get

# Générer les fichiers de code
Write-Host "⚙️ Génération des fichiers de code..." -ForegroundColor Yellow
flutter packages pub run build_runner build --delete-conflicting-outputs

# Vérifier que la génération s'est bien passée
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la génération des fichiers de code" -ForegroundColor Red
    exit 1
}

# Construction de l'APK de debug
Write-Host "🔨 Construction de l'APK de debug..." -ForegroundColor Yellow
flutter build apk --debug

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la construction de l'APK de debug" -ForegroundColor Red
    exit 1
}

# Construction de l'APK de release
Write-Host "🔨 Construction de l'APK de release..." -ForegroundColor Yellow
flutter build apk --release

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la construction de l'APK de release" -ForegroundColor Red
    exit 1
}

# Construction des APK séparés par architecture
Write-Host "🔨 Construction des APK par architecture..." -ForegroundColor Yellow
flutter build apk --split-per-abi --release

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la construction des APK par architecture" -ForegroundColor Red
    exit 1
}

# Construction du bundle Android
Write-Host "🔨 Construction du bundle Android..." -ForegroundColor Yellow
flutter build appbundle --release

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la construction du bundle Android" -ForegroundColor Red
    exit 1
}

# Afficher les fichiers générés
Write-Host "📁 Fichiers générés:" -ForegroundColor Green

$debugApk = "build/app/outputs/flutter-apk/app-debug.apk"
$releaseApk = "build/app/outputs/flutter-apk/app-release.apk"
$arm64Apk = "build/app/outputs/flutter-apk/app-arm64-v8a-release.apk"
$arm32Apk = "build/app/outputs/flutter-apk/app-armeabi-v7a-release.apk"
$x64Apk = "build/app/outputs/flutter-apk/app-x86_64-release.apk"
$bundle = "build/app/outputs/bundle/release/app-release.aab"

if (Test-Path $debugApk) {
    $size = [math]::Round((Get-Item $debugApk).Length / 1MB, 2)
    Write-Host "✅ APK Debug: $debugApk ($size MB)" -ForegroundColor Green
}

if (Test-Path $releaseApk) {
    $size = [math]::Round((Get-Item $releaseApk).Length / 1MB, 2)
    Write-Host "✅ APK Release: $releaseApk ($size MB)" -ForegroundColor Green
}

if (Test-Path $arm64Apk) {
    $size = [math]::Round((Get-Item $arm64Apk).Length / 1MB, 2)
    Write-Host "✅ APK ARM64: $arm64Apk ($size MB)" -ForegroundColor Green
}

if (Test-Path $arm32Apk) {
    $size = [math]::Round((Get-Item $arm32Apk).Length / 1MB, 2)
    Write-Host "✅ APK ARM32: $arm32Apk ($size MB)" -ForegroundColor Green
}

if (Test-Path $x64Apk) {
    $size = [math]::Round((Get-Item $x64Apk).Length / 1MB, 2)
    Write-Host "✅ APK x64: $x64Apk ($size MB)" -ForegroundColor Green
}

if (Test-Path $bundle) {
    $size = [math]::Round((Get-Item $bundle).Length / 1MB, 2)
    Write-Host "✅ Bundle Android: $bundle ($size MB)" -ForegroundColor Green
}

# Ouvrir le dossier des builds
Write-Host "📂 Ouverture du dossier des builds..." -ForegroundColor Yellow
Start-Process "build/app/outputs/flutter-apk/"

Write-Host "🎉 Construction terminée avec succès !" -ForegroundColor Green
Write-Host "📱 Vos APK sont prêts dans le dossier build/app/outputs/flutter-apk/" -ForegroundColor Cyan
Write-Host "🔗 Pour installer sur un appareil connecté: flutter install --release" -ForegroundColor Yellow
