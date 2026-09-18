"""
Configuration de déploiement pour l'application chauffeur
pour contrôler les fonctionnalités en fonction de l'environnement
"""

import os

# Configuration par défaut
DEPLOYMENT_CONFIG = {
    'ENABLE_PDF_EXPORT': True,  # Réactivé avec pdfkit
    'ENABLE_EXCEL_EXPORT': True,  # Activé (openpyxl fonctionne)
    'ENABLE_ADVANCED_REPORTS': True,  # Activé (rapports Excel)
}

def is_feature_enabled(feature_name):
    """Vérifie si une fonctionnalité est activée"""
    return DEPLOYMENT_CONFIG.get(feature_name, False)

def get_deployment_message(feature_name):
    """Retourne un message informatif pour les fonctionnalités désactivées"""
    messages = {
        'ENABLE_PDF_EXPORT': 'Export PDF temporairement indisponible - En cours de configuration',
        'ENABLE_EXCEL_EXPORT': 'Export Excel disponible',
        'ENABLE_ADVANCED_REPORTS': 'Rapports avancés disponibles',
    }
    return messages.get(feature_name, 'Fonctionnalité temporairement indisponible')

def get_pdf_placeholder_response():
    """Retourne une réponse HTTP pour les exports PDF désactivés"""
    from django.http import HttpResponse
    return HttpResponse(
        "Export PDF temporairement indisponible - En cours de configuration",
        content_type='text/plain'
    )
