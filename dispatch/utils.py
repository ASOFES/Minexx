# import pandas as pd  # Temporairement commenté pour le déploiement
from django.http import HttpResponse
from core.utils import render_to_pdf
from io import BytesIO

def get_demandeur_info(demandeur):
    """
    Retourne les informations complètes du demandeur sous forme de chaîne
    """
    if not demandeur:
        return 'N/A'
    
    # Essayer d'obtenir le nom complet
    full_name = demandeur.get_full_name()
    
    # Si le nom complet est vide, utiliser le nom d'utilisateur
    if not full_name.strip():
        full_name = demandeur.username
    
    # Ajouter l'email si disponible
    if demandeur.email:
        return f"{full_name} ({demandeur.email})"
    
    return full_name

def export_courses_to_excel(courses, filename='courses_export.xlsx'):
    """
    Exporte une liste de courses vers un fichier Excel
    """
    # Temporairement désactivé pour le déploiement
    return HttpResponse(
        "Export Excel temporairement indisponible - pandas en cours de configuration",
        content_type='text/plain'
    )

def export_course_detail_to_excel(course, filename='course_detail_export.xlsx'):
    """
    Exporte les détails d'une course vers un fichier Excel
    """
    # Temporairement désactivé pour le déploiement
    return HttpResponse(
        "Export Excel temporairement indisponible - pandas en cours de configuration",
        content_type='text/plain'
    )
