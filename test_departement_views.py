#!/usr/bin/env python
"""
Script de test pour vérifier que les vues de département fonctionnent
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from core.views import departement_list, departement_create, departement_detail, departement_edit
from core.models import Etablissement

def test_departement_views():
    """Test des vues de département"""
    print("🧪 Test des vues de département...")
    
    # Créer un utilisateur de test (admin)
    User = get_user_model()
    try:
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            print("❌ Aucun utilisateur admin trouvé")
            return False
        print(f"✅ Utilisateur admin trouvé: {admin_user.username}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'utilisateur admin: {e}")
        return False
    
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/departements/')
    request.user = admin_user
    
    try:
        # Test de la vue departement_list
        print("📋 Test de departement_list...")
        response = departement_list(request)
        print(f"✅ departement_list: {response.status_code}")
        
        # Test de la vue departement_create (GET)
        print("📝 Test de departement_create (GET)...")
        request = factory.get('/departements/create/')
        request.user = admin_user
        response = departement_create(request)
        print(f"✅ departement_create (GET): {response.status_code}")
        
        # Test de la vue departement_create (POST)
        print("📝 Test de departement_create (POST)...")
        request = factory.post('/departements/create/', {
            'nom': 'Département Test',
            'type': 'departement',
            'actif': True
        })
        request.user = admin_user
        response = departement_create(request)
        print(f"✅ departement_create (POST): {response.status_code}")
        
        # Vérifier que le département a été créé
        etablissement = Etablissement.objects.filter(nom='Département Test').first()
        if etablissement:
            print(f"✅ Département créé: {etablissement.nom} (ID: {etablissement.pk})")
            
            # Test de la vue departement_detail
            print("👁️ Test de departement_detail...")
            request = factory.get(f'/departements/{etablissement.pk}/')
            request.user = admin_user
            response = departement_detail(request, etablissement.pk)
            print(f"✅ departement_detail: {response.status_code}")
            
            # Test de la vue departement_edit (GET)
            print("✏️ Test de departement_edit (GET)...")
            request = factory.get(f'/departements/{etablissement.pk}/edit/')
            request.user = admin_user
            response = departement_edit(request, etablissement.pk)
            print(f"✅ departement_edit (GET): {response.status_code}")
            
            # Nettoyer le département de test
            etablissement.delete()
            print("🧹 Département de test supprimé")
        else:
            print("❌ Le département de test n'a pas été créé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test des vues: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("🎉 Tous les tests ont réussi !")
    return True

if __name__ == '__main__':
    success = test_departement_views()
    sys.exit(0 if success else 1)
