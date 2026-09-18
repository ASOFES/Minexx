import random
from datetime import datetime, timedelta
import uuid

def generer_vehicule_aleatoire():
    marques = ['Toyota', 'Renault', 'Peugeot', 'Volkswagen', 'Ford', 'BMW', 'Mercedes', 'Audi']
    modeles = {
        'Toyota': ['Hilux', 'RAV4', 'Corolla', 'Land Cruiser', 'Hiace'],
        'Renault': ['Kangoo', 'Master', 'Trafic', 'Clio', 'Megane'],
        'Peugeot': ['Partner', 'Boxer', '208', '3008', '508'],
        'Volkswagen': ['Caddy', 'Transporter', 'Golf', 'Tiguan', 'Passat'],
        'Ford': ['Transit', 'Ranger', 'Focus', 'Kuga', 'Fiesta'],
        'BMW': ['Série 3', 'X5', 'Série 5', 'X3', 'Série 1'],
        'Mercedes': ['Classe V', 'Sprinter', 'Classe C', 'GLC', 'Classe A'],
        'Audi': ['A4', 'Q5', 'A6', 'Q3', 'A3']
    }
    
    marque = random.choice(marques)
    modele = random.choice(modeles[marque])
    annee = random.randint(2015, 2023)
    immatriculation = f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))}-{random.randint(100, 999)}-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))}"
    
    return {
        'id': str(uuid.uuid4()),
        'immatriculation': immatriculation,
        'marque': marque,
        'modele': modele,
        'annee': annee,
        'kilometrage_actuel': random.randint(10000, 200000),
        'date_mise_en_circulation': f"{annee}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
        'type_vehicule': random.choice(['Véhicule léger', 'Utilitaire', '4x4', 'Camionnette', 'Bus']),
        'statut': random.choice(['En service', 'En maintenance', 'Hors service']),
        'carburant': random.choice(['Diesel', 'Essence', 'Hybride', 'Électrique']),
        'consommation_moyenne': round(random.uniform(5.0, 15.0), 1)
    }

def generer_entretiens_aleatoires(vehicule_id, count=10):
    entretiens = []
    date_actuelle = datetime.now()
    
    for i in range(count):
        jours_depuis_aujourdhui = random.randint(1, 365*3)
        date_entretien = date_actuelle - timedelta(days=jours_depuis_aujourdhui)
        kilometrage = random.randint(10000, 200000)
        
        types_entretien = [
            'Vidange', 'Révision générale', 'Changement pneus', 
            'Freinage', 'Distribution', 'Climatisation'
        ]
        
        entretien = {
            'id': str(uuid.uuid4()),
            'vehicule_id': vehicule_id,
            'date_entretien': date_entretien.strftime('%Y-%m-%d'),
            'type_entretien': random.choice(types_entretien),
            'kilometrage': kilometrage,
            'cout': round(random.uniform(100, 1500), 2),
            'observations': f"Entretien {i+1} - " + random.choice([
                'Effectué selon les spécifications',
                'Pièces remplacées',
                'Contrôle technique OK',
                'Révision complète effectuée'
            ]),
            'prestataire': random.choice([
                'Garage Central', 'Auto Plus', 'Midas', 'Speedy', 'Feu Vert',
                'Norauto', 'Euromaster', 'ATU', 'Norauto', 'Mobivia'
            ])
        }
        entretiens.append(entretien)
    
    return sorted(entretiens, key=lambda x: x['date_entretien'], reverse=True)

def generer_ravitaillements_aleatoires(vehicule_id, count=15):
    ravitaillements = []
    date_actuelle = datetime.now()
    
    for i in range(count):
        jours_depuis_aujourdhui = random.randint(1, 365)
        date_ravitaillement = date_actuelle - timedelta(days=jours_depuis_aujourdhui)
        litres = round(random.uniform(20, 80), 1)
        prix_litre = round(random.uniform(1.50, 2.20), 2)
        
        ravitaillement = {
            'id': str(uuid.uuid4()),
            'vehicule_id': vehicule_id,
            'date_ravitaillement': date_ravitaillement.strftime('%Y-%m-%d'),
            'kilometrage_apres': random.randint(10000, 200000),
            'litres': litres,
            'cout_unitaire': prix_litre,
            'cout_total': round(litres * prix_litre, 2),
            'station': random.choice([
                'Total', 'Shell', 'Esso', 'BP', 'Avia', 'Carrefour', 'Leclerc',
                'Intermarché', 'Casino', 'Système U'
            ]) + ' ' + random.choice(['Centre', 'Nord', 'Sud', 'Est', 'Ouest']),
            'plein': random.choice([True, False])
        }
        ravitaillements.append(ravitaillement)
    
    return sorted(ravitaillements, key=lambda x: x['date_ravitaillement'], reverse=True)

def generer_missions_aleatoires(vehicule_id, count=20):
    missions = []
    date_actuelle = datetime.now()
    lieux = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Bordeaux', 'Lille', 'Nantes', 'Strasbourg']
    chauffeurs = ['Jean Dupont', 'Marie Martin', 'Pierre Durand', 'Sophie Bernard', 'Thomas Petit']
    
    for i in range(count):
        jours_depuis_aujourdhui = random.randint(1, 90)
        date_mission = date_actuelle - timedelta(days=jours_depuis_aujourdhui)
        distance = random.randint(10, 500)
        duree = random.randint(30, 480)
        
        mission = {
            'id': str(uuid.uuid4()),
            'vehicule_id': vehicule_id,
            'date_mission': date_mission.strftime('%Y-%m-%d'),
            'chauffeur': random.choice(chauffeurs),
            'distance_parcourue': distance,
            'lieu_depart': random.choice(lieux),
            'lieu_arrivee': random.choice([l for l in lieux if l != 'lieu_depart']),
            'statut': random.choice(['Terminée', 'Annulée', 'En cours', 'Planifiée']),
            'kilometrage_depart': random.randint(10000, 200000),
            'kilometrage_fin': random.randint(10000, 200000) + distance,
            'duree': f"{duree // 60:02d}:{duree % 60:02d}",
            'motif': random.choice([
                'Livraison', 'Rendez-vous client', 'Déplacement professionnel',
                'Course urgente', 'Transport de marchandises', 'Mission spéciale'
            ])
        }
        missions.append(mission)
    
    return sorted(missions, key=lambda x: x['date_mission'], reverse=True)

def generer_rapport_complet():
    # Générer un véhicule aléatoire
    vehicule = generer_vehicule_aleatoire()
    
    # Générer les données associées
    entretiens = generer_entretiens_aleatoires(vehicule['id'])
    ravitaillements = generer_ravitaillements_aleatoires(vehicule['id'])
    missions = generer_missions_aleatoires(vehicule['id'])
    
    # Calculer les statistiques
    cout_total_carburant = sum(r['cout_total'] for r in ravitaillements)
    cout_total_entretien = sum(e['cout'] for e in entretiens)
    distance_totale = sum(m['distance_parcourue'] for m in missions if m['statut'] == 'Terminée')
    conso_moyenne = round(sum(r['litres'] for r in ravitaillements) / (distance_totale / 100) if distance_totale > 0 else 0, 1)
    
    # Préparer le rapport
    rapport = {
        'vehicule': vehicule,
        'statistiques': {
            'km_actuel': vehicule['kilometrage_actuel'],
            'missions_count': len(missions),
            'distance_totale': distance_totale,
            'conso_moyenne': conso_moyenne,
            'cout_total_carburant': round(cout_total_carburant, 2),
            'cout_total_entretien': round(cout_total_entretien, 2),
            'cout_total': round(cout_total_carburant + cout_total_entretien, 2),
            'incidents': len([m for m in missions if 'incident' in m['motif'].lower()])
        },
        'entretiens': entretiens[:10],
        'ravitaillements': ravitaillements[:10],
        'missions': missions[:5],
        'alertes': [
            {
                'niveau': random.choice(['Alerte', 'Attention', 'Information']),
                'message': random.choice([
                    'Vidange nécessaire bientôt',
                    'Contrôle technique à prévoir',
                    'Pneus à vérifier',
                    'Niveau de liquide de frein bas'
                ]),
                'date_alerte': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
                'type': random.choice(['entretien', 'securite', 'performance'])
            }
            for _ in range(random.randint(1, 3))
        ]
    }
    
    return rapport
