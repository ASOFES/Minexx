#!/usr/bin/env python
"""
Script pour nettoyer la base de données tout en préservant l'utilisateur "toto"
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_vehicules.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import *
from chauffeur.models import *
from demandeur.models import *
from dispatch.models import *
from entretien.models import *
from ravitaillement.models import *
from rapport.models import *
from securite.models import *
from suivi.models import *
from notifications.models import *

def clean_database():
    """Nettoyer la base de données en préservant l'utilisateur toto"""
    print("🧹 Nettoyage de la base de données")
    print("=" * 60)
    
    # Créer ou mettre à jour l'utilisateur toto
    User = get_user_model()
    toto, created = User.objects.get_or_create(
        username='toto',
        defaults={
            'first_name': 'Toto',
            'last_name': 'Admin',
            'email': 'toto@minexx.com',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'role': 'admin'
        }
    )
    
    if created:
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if not password:
            raise RuntimeError("Définir DJANGO_SUPERUSER_PASSWORD pour créer l'utilisateur toto")
        toto.set_password(password)
        toto.save()
        print("✅ Utilisateur 'toto' créé avec succès")
    else:
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        if password:
            toto.set_password(password)
        toto.is_staff = True
        toto.is_superuser = True
        toto.is_active = True
        toto.role = 'admin'
        toto.save()
        print("✅ Utilisateur 'toto' mis à jour avec succès")
    
    print(f"   Username: toto")
    print(f"   Mot de passe: (défini via DJANGO_SUPERUSER_PASSWORD)")
    print(f"   Rôle: admin")
    
    # Supprimer tous les autres utilisateurs
    other_users = User.objects.exclude(username='toto')
    user_count = other_users.count()
    other_users.delete()
    print(f"🗑️  {user_count} autres utilisateurs supprimés")
    
    # Nettoyer les modèles par application
    models_to_clean = [
        # Core
        (Etablissement, "Établissements"),
        (Vehicule, "Véhicules"),
        (Course, "Courses"),
        (Message, "Messages"),
        (ActionTraceur, "Actions tracées"),
        (HistoriqueKilometrage, "Historiques kilométrage"),
        (HistoriqueCorrectionKilometrage, "Corrections kilométrage"),
        
        # Chauffeur
        (HistoriqueChauffeur, "Historiques chauffeur"),
        (CommentaireRapportChauffeur, "Commentaires rapports chauffeur"),
        (CommentaireRapportDemandeur, "Commentaires rapports demandeur"),
        (DistanceJournaliere, "Distances journalières"),
        
        # Demandeur
        (HistoriqueDemande, "Historiques demandes"),
        
        # Dispatch
        (HistoriqueDispatch, "Historiques dispatch"),
        
        # Entretien
        (Entretien, "Entretiens"),
        
        # Ravitaillement
        (Ravitaillement, "Ravitaillements"),
        (Station, "Stations"),
        
        # Rapport
        (Rapport, "Rapports"),
        
        # Sécurité
        (CheckListSecurite, "Checklists sécurité"),
        (IncidentSecurite, "Incidents sécurité"),
        
        # Suivi
        (SuiviVehicule, "Suivis véhicules"),
        
        # Notifications
        (PushSubscription, "Abonnements push"),
        (Notification, "Notifications"),
        (DocumentNotification, "Notifications documents"),
        (EntretienNotification, "Notifications entretien"),
    ]
    
    total_deleted = 0
    
    for model, name in models_to_clean:
        try:
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                print(f"🗑️  {count} {name} supprimés")
                total_deleted += count
            else:
                print(f"✅ {name}: déjà vide")
        except Exception as e:
            print(f"⚠️  Erreur lors de la suppression des {name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Résumé du nettoyage:")
    print(f"   ✅ Utilisateur 'toto' préservé")
    print(f"   🗑️  {total_deleted} enregistrements supprimés")
    print(f"   🎯 Base de données nettoyée avec succès!")
    print("=" * 60)
    
    # Vérifier que toto existe toujours
    try:
        toto_check = User.objects.get(username='toto')
        print(f"\n✅ Vérification: Utilisateur 'toto' existe toujours")
        print(f"   Username: {toto_check.username}")
        print(f"   Email: {toto_check.email}")
        print(f"   Staff: {toto_check.is_staff}")
        print(f"   Superuser: {toto_check.is_superuser}")
        print(f"   Actif: {toto_check.is_active}")
        print(f"   Rôle: {toto_check.role}")
    except User.DoesNotExist:
        print("❌ ERREUR: L'utilisateur 'toto' a été supprimé!")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Script de nettoyage de la base de données")
    print("⚠️  ATTENTION: Ce script va supprimer TOUTES les données")
    print("⚠️  sauf l'utilisateur 'toto'")
    print("=" * 60)
    
    # Demander confirmation
    response = input("\nÊtes-vous sûr de vouloir continuer? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Opération annulée")
        return
    
    print("\n🔄 Début du nettoyage...")
    
    try:
        if clean_database():
            print("\n🎉 Nettoyage terminé avec succès!")
            print("✅ Vous pouvez maintenant vous connecter avec:")
            print("   Username: toto")
            print("   Mot de passe: (via DJANGO_SUPERUSER_PASSWORD)")
        else:
            print("\n❌ Erreur lors du nettoyage")
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")

if __name__ == "__main__":
    main() 