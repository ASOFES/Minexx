#!/usr/bin/env python3
"""
Script d'injection des véhicules dans Supabase.
Les identifiants ne doivent JAMAIS être en clair : utiliser les variables d'environnement.
"""

import os
import sys
import json
from datetime import date

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Installer psycopg2-binary pour utiliser ce script.")
    sys.exit(1)

from supabase_config import SUPABASE_CONFIG


def parse_french_date(date_str):
    """Parse les dates françaises en objets date Python."""
    mois_fr = {
        'janv.': 1, 'févr.': 2, 'mars': 3, 'avr.': 4, 'mai': 5, 'juin': 6,
        'juil.': 7, 'août': 8, 'sept.': 9, 'oct.': 10, 'nov.': 11, 'déc.': 12,
    }
    try:
        parts = date_str.split()
        return date(int(parts[2]), mois_fr.get(parts[1], 1), int(parts[0]))
    except Exception:
        return date(2025, 12, 31)


def get_supabase_connection():
    """Établit la connexion à Supabase."""
    if not SUPABASE_CONFIG.get('host') or not SUPABASE_CONFIG.get('password'):
        raise RuntimeError(
            "Définir SUPABASE_DB_HOST (ou SUPABASE_URL) et SUPABASE_DB_PASSWORD"
        )
    return psycopg2.connect(**SUPABASE_CONFIG)


def load_vehicles():
    path = os.path.join(os.path.dirname(__file__), 'vehicles_data.json')
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), 'vehicles_data_updated.json')
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'vehicles' in data:
        return data['vehicles']
    return data


def main():
    print("Connexion Supabase...")
    conn = get_supabase_connection()
    vehicles = load_vehicles()
    print(f"{len(vehicles)} véhicule(s) chargés depuis JSON.")
    # L'injection SQL complète dépend du schéma distant ;
    # ce script sécurise la connexion — adapter les INSERT selon votre schéma.
    conn.close()
    print("Connexion OK. Compléter les INSERT selon le schéma Supabase.")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)
