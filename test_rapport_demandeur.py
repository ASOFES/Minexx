#!/usr/bin/env python
"""
Script de test pour vérifier que la page rapport-demandeur fonctionne correctement
"""
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Course, Etablissement
from datetime import datetime, timedelta
from django.utils import timezone

def test_rapport_demandeur_basic():
    """Test basique de la page rapport-demandeur"""
    print("🔍 Test basique de la page rapport-demandeur...")
    
    client = Client()
    
    # Créer un utilisateur test
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='test_demandeur',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'Demandeur',
            'role': 'demandeur',
            'is_active': True,
        }
    )
    
    # Créer un établissement si nécessaire
    etablissement, _ = Etablissement.objects.get_or_create(
        nom='Test Département',
        defaults={'type': 'departement', 'actif': True}
    )
    user.etablissement = etablissement
    user.save()
    
    # Se connecter
    client.force_login(user)
    
    # Tester l'accès à la page
    response = client.get('/chauffeur/rapport-demandeur/')
    
    if response.status_code == 200:
        print("✅ Page accessible avec succès")
        print(f"   - Status: {response.status_code}")
        print(f"   - Template utilisé: {response.template_name if hasattr(response, 'template_name') else 'Non disponible'}")
    else:
        print(f"❌ Erreur d'accès: {response.status_code}")
        return False
    
    return True

def test_rapport_demandeur_with_filters():
    """Test avec filtres de date"""
    print("\n🔍 Test avec filtres de date...")
    
    client = Client()
    User = get_user_model()
    user = User.objects.get(username='test_demandeur')
    client.force_login(user)
    
    # Test avec filtres de date
    date_debut = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    date_fin = timezone.now().strftime('%Y-%m-%d')
    
    response = client.get(f'/chauffeur/rapport-demandeur/?date_debut={date_debut}&date_fin={date_fin}')
    
    if response.status_code == 200:
        print("✅ Filtres de date fonctionnent")
    else:
        print(f"❌ Erreur avec filtres: {response.status_code}")
        return False
    
    return True

def test_rapport_demandeur_admin_access():
    """Test d'accès admin"""
    print("\n🔍 Test d'accès admin...")
    
    client = Client()
    User = get_user_model()
    
    # Créer un admin
    admin_user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Test',
            'last_name': 'Admin',
            'role': 'admin',
            'is_active': True,
        }
    )
    
    client.force_login(admin_user)
    
    response = client.get('/chauffeur/rapport-demandeur/')
    
    if response.status_code == 200:
        print("✅ Accès admin fonctionne")
    else:
        print(f"❌ Erreur accès admin: {response.status_code}")
        return False
    
    return True

def test_rapport_demandeur_export():
    """Test des exports PDF et Excel"""
    print("\n🔍 Test des exports...")
    
    client = Client()
    User = get_user_model()
    user = User.objects.get(username='test_demandeur')
    client.force_login(user)
    
    # Test export PDF
    response_pdf = client.get('/chauffeur/rapport-demandeur/pdf/')
    if response_pdf.status_code == 200:
        print("✅ Export PDF fonctionne")
    else:
        print(f"❌ Erreur export PDF: {response_pdf.status_code}")
    
    # Test export Excel
    response_excel = client.get('/chauffeur/rapport-demandeur/excel/')
    if response_excel.status_code == 200:
        print("✅ Export Excel fonctionne")
    else:
        print(f"❌ Erreur export Excel: {response_excel.status_code}")
    
    return response_pdf.status_code == 200 and response_excel.status_code == 200

def test_rapport_demandeur_content():
    """Test du contenu de la page"""
    print("\n🔍 Test du contenu de la page...")
    
    client = Client()
    User = get_user_model()
    user = User.objects.get(username='test_demandeur')
    client.force_login(user)
    
    response = client.get('/chauffeur/rapport-demandeur/')
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        
        # Vérifier la présence d'éléments clés
        checks = [
            ('Titre de la page', 'Rapport Demandeur'),
            ('Formulaire de filtres', 'date_debut'),
            ('Bouton PDF', 'Exporter PDF'),
            ('Bouton Excel', 'Exporter Excel'),
            ('Section statistiques', 'Missions totales'),
        ]
        
        all_good = True
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: OK")
            else:
                print(f"❌ {check_name}: Manquant")
                all_good = False
        
        return all_good
    else:
        print(f"❌ Impossible de charger la page: {response.status_code}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Début des tests pour rapport-demandeur")
    print("=" * 50)
    
    tests = [
        test_rapport_demandeur_basic,
        test_rapport_demandeur_with_filters,
        test_rapport_demandeur_admin_access,
        test_rapport_demandeur_export,
        test_rapport_demandeur_content,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur dans le test: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 Tous les tests sont passés avec succès!")
        print("✅ La page rapport-demandeur fonctionne correctement")
    else:
        print("⚠️  Certains tests ont échoué")
        print("🔧 Des corrections peuvent être nécessaires")
    
    return passed == total

if __name__ == "__main__":
    main() 