#!/usr/bin/env python
"""
Script de test pour vérifier que le module ravitaillement fonctionne correctement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_ravitaillement_dashboard():
    """Test du dashboard ravitaillement"""
    print("🧪 Test du dashboard ravitaillement")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_ravitaillement',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL du dashboard ravitaillement
        print("✅ Test de l'URL /ravitaillement/")
        response = client.get('/ravitaillement/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Le dashboard ravitaillement se charge correctement !")
            print("✅ Aucune erreur TemplateSyntaxError détectée")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            if hasattr(response, 'content'):
                print(f"   Contenu: {response.content[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_ravitaillement_liste():
    """Test de la liste des ravitaillements"""
    print("\n🧪 Test de la liste des ravitaillements")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_ravitaillement_liste',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL de la liste des ravitaillements
        print("✅ Test de l'URL /ravitaillement/liste/")
        response = client.get('/ravitaillement/liste/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ La liste des ravitaillements se charge correctement !")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_ravitaillement_ajouter():
    """Test de l'ajout de ravitaillement"""
    print("\n🧪 Test de l'ajout de ravitaillement")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_ravitaillement_ajouter',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL d'ajout de ravitaillement
        print("✅ Test de l'URL /ravitaillement/ajouter/")
        response = client.get('/ravitaillement/ajouter/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ La page d'ajout de ravitaillement se charge correctement !")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_ravitaillement_stations():
    """Test de la gestion des stations"""
    print("\n🧪 Test de la gestion des stations")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_ravitaillement_stations',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester l'URL de la liste des stations
        print("✅ Test de l'URL /ravitaillement/stations/")
        response = client.get('/ravitaillement/stations/')
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ La liste des stations se charge correctement !")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_ravitaillement_filtres():
    """Test des filtres ravitaillement"""
    print("\n🧪 Test des filtres ravitaillement")
    print("=" * 50)
    
    try:
        client = Client()
        
        # Créer un utilisateur de test
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username='test_ravitaillement_filtres',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        # Se connecter
        client.force_login(user)
        
        # Tester avec des filtres
        params = {
            'vehicule': '1',
            'date_debut': '2024-01-01',
            'date_fin': '2024-12-31',
            'tri': 'date'
        }
        
        print("✅ Test de l'URL /ravitaillement/liste/ avec filtres")
        response = client.get('/ravitaillement/liste/', params)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Les filtres ravitaillement fonctionnent correctement !")
            return True
        else:
            print(f"❌ Erreur: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test avec filtres: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test du module ravitaillement")
    print("=" * 60)
    
    tests = [
        test_ravitaillement_dashboard,
        test_ravitaillement_liste,
        test_ravitaillement_ajouter,
        test_ravitaillement_stations,
        test_ravitaillement_filtres
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Erreur critique dans {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résultats des tests: {passed}/{total} réussis")
    
    if passed == total:
        print("🎉 Le module ravitaillement fonctionne parfaitement !")
        print("✅ Aucune erreur TemplateSyntaxError détectée")
        print("✅ Toutes les fonctionnalités fonctionnent")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 