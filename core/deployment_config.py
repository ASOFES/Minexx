"""
Configuration de déploiement pour contrôler les fonctionnalités
en fonction de l'environnement (développement vs production)
"""

import os

# Configuration par défaut
DEPLOYMENT_CONFIG = {
    'ENABLE_PDF_EXPORT': True,  # Réactivé avec pdfkit
    'ENABLE_EXCEL_EXPORT': True,  # Activé (xlsxwriter fonctionne)
    'ENABLE_CHARTS': False,  # Désactivé (matplotlib)
    'ENABLE_IMAGE_PROCESSING': False,  # Désactivé (Pillow)
    'ENABLE_ADVANCED_REPORTS': True,  # Réactivé
}

def is_feature_enabled(feature_name):
    """Vérifie si une fonctionnalité est activée"""
    return DEPLOYMENT_CONFIG.get(feature_name, False)

def get_deployment_message(feature_name):
    """Retourne un message informatif pour les fonctionnalités désactivées"""
    messages = {
        'ENABLE_PDF_EXPORT': 'Export PDF temporairement indisponible - En cours de configuration',
        'ENABLE_CHARTS': 'Graphiques temporairement indisponibles - En cours de configuration',
        'ENABLE_IMAGE_PROCESSING': 'Traitement d\'images temporairement indisponible - En cours de configuration',
        'ENABLE_ADVANCED_REPORTS': 'Rapports avancés temporairement indisponibles - En cours de configuration',
    }
    return messages.get(feature_name, 'Fonctionnalité temporairement indisponible')
