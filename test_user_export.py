#!/usr/bin/env python
"""
Script de test pour vérifier que l'export Excel des utilisateurs fonctionne après la correction
"""
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from core.models import Etablissement
from datetime import datetime

def test_user_export_excel():
    """Test de l'export Excel des utilisateurs"""
    print("🔍 Test de l'export Excel des utilisateurs...")
    
    client = Client()
    
    # Créer un utilisateur admin test
    User = get_user_model()
    admin_user, created = User.objects.get_or_create(
        username='test_admin_export',
        defaults={
            'email': 'admin_export@example.com',
            'first_name': 'Test',
            'last_name': 'Admin Export',
            'role': 'admin',
            'is_active': True,
        }
    )
    
    # Créer un établissement si nécessaire
    etablissement, _ = Etablissement.objects.get_or_create(
        nom='Test Établissement Export',
        defaults={'type': 'departement', 'actif': True}
    )
    admin_user.etablissement = etablissement
    admin_user.save()
    
    # Se connecter
    client.force_login(admin_user)
    
    # Tester l'export Excel
    response = client.get('/users/export/excel/')
    
    if response.status_code == 200:
        print("✅ Export Excel fonctionne correctement")
        print(f"   - Status: {response.status_code}")
        print(f"   - Content-Type: {response.get('Content-Type', 'Non disponible')}")
        print(f"   - Content-Disposition: {response.get('Content-Disposition', 'Non disponible')}")
        
        # Vérifier que c'est bien un fichier Excel
        content_type = response.get('Content-Type', '')
        if 'excel' in content_type.lower() or 'spreadsheet' in content_type.lower():
            print("✅ Type de contenu Excel détecté")
        else:
            print(f"⚠️  Type de contenu inattendu: {content_type}")
        
        return True
    else:
        print(f"❌ Erreur d'export: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"   - Contenu: {response.content[:200]}...")
        return False

def test_user_export_with_etablissement():
    """Test avec des utilisateurs dans un établissement"""
    print("\n🔍 Test avec utilisateurs dans un établissement...")
    
    client = Client()
    User = get_user_model()
    
    # Créer un établissement
    etablissement, _ = Etablissement.objects.get_or_create(
        nom='Établissement Test Export',
        defaults={'type': 'departement', 'actif': True}
    )
    
    # Créer des utilisateurs dans cet établissement
    users_data = [
        {'username': 'user1_export', 'first_name': 'User', 'last_name': 'One', 'role': 'demandeur'},
        {'username': 'user2_export', 'first_name': 'User', 'last_name': 'Two', 'role': 'chauffeur'},
        {'username': 'user3_export', 'first_name': 'User', 'last_name': 'Three', 'role': 'dispatch'},
    ]
    
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': f"{user_data['username']}@example.com",
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'role': user_data['role'],
                'is_active': True,
                'etablissement': etablissement,
            }
        )
        if created:
            print(f"✅ Utilisateur créé: {user.username}")
    
    # Créer un admin dans le même établissement
    admin_user, created = User.objects.get_or_create(
        username='admin_etablissement_export',
        defaults={
            'email': 'admin_etab@example.com',
            'first_name': 'Admin',
            'last_name': 'Établissement',
            'role': 'admin',
            'is_active': True,
            'etablissement': etablissement,
        }
    )
    
    client.force_login(admin_user)
    
    # Tester l'export
    response = client.get('/users/export/excel/')
    
    if response.status_code == 200:
        print("✅ Export avec établissement fonctionne")
        return True
    else:
        print(f"❌ Erreur export avec établissement: {response.status_code}")
        return False

def test_user_export_superuser():
    """Test avec un superuser"""
    print("\n🔍 Test avec superuser...")
    
    client = Client()
    User = get_user_model()
    
    # Créer un superuser
    superuser, created = User.objects.get_or_create(
        username='superuser_export',
        defaults={
            'email': 'superuser@example.com',
            'first_name': 'Super',
            'last_name': 'User',
            'role': 'admin',
            'is_active': True,
            'is_superuser': True,
        }
    )
    
    client.force_login(superuser)
    
    # Tester l'export
    response = client.get('/users/export/excel/')
    
    if response.status_code == 200:
        print("✅ Export superuser fonctionne")
        return True
    else:
        print(f"❌ Erreur export superuser: {response.status_code}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Début des tests pour l'export Excel des utilisateurs")
    print("=" * 60)
    
    tests = [
        test_user_export_excel,
        test_user_export_with_etablissement,
        test_user_export_superuser,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur dans le test: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS DES TESTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 Tous les tests sont passés avec succès!")
        print("✅ L'export Excel des utilisateurs fonctionne correctement")
        print("✅ La correction de l'AttributeError est effective")
    else:
        print("⚠️  Certains tests ont échoué")
        print("🔧 Des corrections supplémentaires peuvent être nécessaires")
    
    return passed == total

if __name__ == "__main__":
    main() 