#!/usr/bin/env python3
"""
Configuration Supabase pour MINEXX — secrets via variables d'environnement uniquement.
"""

import os
import sys

SUPABASE_CONFIG = {
    'host': os.getenv('SUPABASE_DB_HOST') or os.getenv('SUPABASE_URL', ''),
    'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
    'user': os.getenv('SUPABASE_DB_USER', 'postgres'),
    'password': os.getenv('SUPABASE_DB_PASSWORD', ''),
    'port': os.getenv('SUPABASE_DB_PORT', '5432'),
}

SETUP_INSTRUCTIONS = """
Configuration Supabase pour MINEXX

Définir les variables d'environnement :
  SUPABASE_DB_HOST (ou SUPABASE_URL)
  SUPABASE_DB_PASSWORD
  SUPABASE_DB_NAME (défaut: postgres)
  SUPABASE_DB_USER (défaut: postgres)
  SUPABASE_DB_PORT (défaut: 5432)

Ne jamais committer le mot de passe dans le code.
"""

if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)
    print("\nConfiguration actuelle :")
    for key, value in SUPABASE_CONFIG.items():
        if key == 'password':
            print(f"{key}: {'***' if value else '(non défini)'}")
        else:
            print(f"{key}: {value or '(non défini)'}")
    if not SUPABASE_CONFIG['host'] or not SUPABASE_CONFIG['password']:
        sys.exit(1)
