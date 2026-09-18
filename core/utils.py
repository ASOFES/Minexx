import os
import io
import base64
from datetime import datetime
from django.conf import settings
from django.db import models
from django.http import HttpResponse
from django.template.loader import get_template
# Nouvelles bibliothèques PDF compatibles Python 3.13
from .pdf_utils import render_to_pdf as new_render_to_pdf, html_to_pdf, markdown_to_pdf, is_pdf_available
from django.contrib.staticfiles import finders
import xlsxwriter
from django.core.mail import send_mail
from core.models import Utilisateur
from django.contrib import messages
from django.utils import timezone
from ravitaillement.models import Ravitaillement
from entretien.models import Entretien
from securite.models import CheckListSecurite


def format_local_datetime(dt, fmt='%Y-%m-%d %H:%M'):
    """Affiche une datetime en fuseau TIME_ZONE (Africa/Lubumbashi), pas en UTC brut."""
    if not dt:
        return ''
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    return dt.strftime(fmt)


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those resources
    """
    # Si l'URI est un chemin absolu, le retourner directement
    if os.path.isabs(uri):
        return uri
        
    # Essayer de trouver le fichier via le système de fichiers statiques de Django
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
        return path
        
    # Gérer les chemins relatifs
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Vérifier si c'est un chemin statique
    if uri.startswith('static/'):
        path = os.path.join(base_dir, uri)
        if os.path.isfile(path):
            return path
            
    # Vérifier si c'est un chemin média
    if uri.startswith('media/'):
        path = os.path.join(base_dir, uri)
        if os.path.isfile(path):
            return path
    
    # Dernier recours: essayer de trouver le fichier dans le répertoire statique
    path = os.path.join(base_dir, 'static', uri)
    if os.path.isfile(path):
        return path
        
    # Si tout échoue, retourner l'URI tel quel
    return uri


def render_to_pdf(template_src, context_dict=None, filename="export.pdf"):
    """
    Génère un PDF à partir d'un template HTML et d'un dictionnaire de contexte
    Utilise la nouvelle implémentation pdfkit compatible Python 3.13
    
    Args:
        template_src (str): Chemin vers le template HTML
        context_dict (dict, optional): Dictionnaire de contexte pour le template. Par défaut {}.
        filename (str, optional): Nom du fichier de sortie. Par défaut "export.pdf".
    
    Returns:
        HttpResponse: Réponse HTTP avec le fichier PDF en pièce jointe
    """
    if context_dict is None:
        context_dict = {}
    
    # Vérifier si la génération PDF est disponible
    if not is_pdf_available():
        return HttpResponse(
            "Export PDF temporairement indisponible - En cours de configuration",
            content_type='text/plain'
        )
    
    try:
        # Ajout du logo en base64 au contexte si le fichier existe
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.abspath(os.path.join(base_dir, 'static', 'images', 'logo_minexx.png'))
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                data_uri = f"data:image/png;base64,{encoded_string}"
                context_dict['logo_data_uri'] = data_uri
        
        # Utiliser la nouvelle implémentation pdfkit
        return new_render_to_pdf(template_src, context_dict, filename)
        
    except Exception as e:
        error_message = f"Erreur lors de la génération du PDF: {str(e)}"
        return HttpResponse(error_message, content_type='text/plain', status=500)
        # FONCTION TEMPORAIREMENT DÉSACTIVÉE POUR LE DÉPLOIEMENT
        # Les modules xhtml2pdf et reportlab causent des conflits avec Python 3.13 sur Render
        response.write("Export PDF temporairement indisponible")
        return response
        
    except Exception as e:
        # En cas d'erreur, retourner une réponse d'erreur
        response = HttpResponse(f"Erreur lors de la génération du PDF: {str(e)}", content_type='text/plain')
        response.status_code = 500
        return response


def export_to_pdf(title, data, filename, template=None, context=None, user=None):
    """
    Exporte des données au format PDF
    
    Args:
        title (str): Titre du document
        data (list): Liste de dictionnaires contenant les données à exporter
        filename (str): Nom du fichier de sortie
        template (str, optional): Template HTML à utiliser
        context (dict, optional): Contexte supplémentaire pour le template
        user (User, optional): L'utilisateur qui demande l'exportation
    
    Returns:
        HttpResponse: Réponse HTTP avec le fichier PDF
    """
    # FONCTION TEMPORAIREMENT DÉSACTIVÉE POUR LE DÉPLOIEMENT
    # Les modules xhtml2pdf et reportlab causent des conflits avec Python 3.13 sur Render
    return HttpResponse("Export PDF temporairement indisponible", content_type='text/plain')


def export_to_excel(title, data, filename):
    """
    Exporte des données au format Excel
    
    Args:
        title (str): Titre du document
        data (list): Liste de dictionnaires contenant les données à exporter
        filename (str): Nom du fichier de sortie
    
    Returns:
        HttpResponse: Réponse HTTP avec le fichier Excel
    """
    try:
        # Créer un buffer en mémoire pour le fichier Excel
        buffer = io.BytesIO()
        
        # Créer un nouveau classeur Excel
        workbook = xlsxwriter.Workbook(buffer)
        
        # Créer une feuille de calcul
        worksheet = workbook.add_worksheet('Données')
        
        # Définir des formats pour l'en-tête et les données
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        data_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1
        })
        
        # Écrire le titre
        worksheet.write(0, 0, title, header_format)
        worksheet.merge_range(0, 0, 0, len(data[0].keys()) - 1 if data else 0, title, header_format)
        
        # Écrire la date de génération
        worksheet.write(1, 0, f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", data_format)
        worksheet.merge_range(1, 0, 1, len(data[0].keys()) - 1 if data else 0, f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}", data_format)
        
        # Écrire les en-têtes
        if data and isinstance(data[0], dict):
            headers = list(data[0].keys())
            for col, header in enumerate(headers):
                worksheet.write(3, col, header, header_format)
            
            # Écrire les données
            for row, item in enumerate(data, start=4):
                for col, header in enumerate(headers):
                    value = item.get(header, '')
                    worksheet.write(row, col, value, data_format)
            
            # Ajuster automatiquement la largeur des colonnes
            for col, header in enumerate(headers):
                max_length = len(str(header))
                for item in data:
                    max_length = max(max_length, len(str(item.get(header, ''))))
                worksheet.set_column(col, col, min(max_length + 2, 50))  # Limiter à 50 caractères
        
        # Fermer le classeur
        workbook.close()
        
        # Préparer la réponse HTTP
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        # En cas d'erreur, retourner une réponse d'erreur
        response = HttpResponse(f"Erreur lors de la génération du fichier Excel: {str(e)}", content_type='text/plain')
        response.status_code = 500
        return response


# def export_to_pdf_with_image(title, data, filename, image_path=None, image_caption=None, user=None):
#     """
#     Exporte des données au format PDF en mode paysage avec logo et une image supplémentaire
#     
#     Args:
#         title (str): Titre du document
#         data (list): Liste de dictionnaires contenant les données à exporter
#         filename (str): Nom du fichier de sortie
#         image_path (str, optional): Chemin vers l'image à inclure
#         image_caption (str, optional): Légende de l'image
#         user (User, optional): L'utilisateur qui demande l'exportation
#     
#     Returns:
#         HttpResponse: Réponse HTTP avec le fichier PDF
#     """
#     # FONCTION TEMPORAIREMENT DÉSACTIVÉE POUR LE DÉPLOIEMENT
#     # Les modules xhtml2pdf et reportlab causent des conflits avec Python 3.13 sur Render
#     return HttpResponse("Export PDF temporairement indisponible", content_type='text/plain')


def notifier_anomalie_kilometrage(request, vehicule, utilisateur, module, valeur_saisie, valeur_attendue, commentaire=None):
    """
    Notifie une anomalie de kilométrage via email
    
    Args:
        request: La requête HTTP
        vehicule: L'objet véhicule concerné
        utilisateur: L'utilisateur qui a saisi la valeur
        module: Le module où l'anomalie a été détectée
        valeur_saisie: La valeur saisie par l'utilisateur
        valeur_attendue: La valeur attendue
        commentaire: Commentaire optionnel
    
    Returns:
        bool: True si la notification a été envoyée avec succès, False sinon
    """
    try:
        # Préparer le sujet et le message
        sujet = f"Anomalie de kilométrage détectée - {vehicule.marque} {vehicule.modele}"
        
        message = f"""
        Une anomalie de kilométrage a été détectée dans le module {module}.
        
        Détails:
        - Véhicule: {vehicule.marque} {vehicule.modele} (ID: {vehicule.id})
        - Utilisateur: {utilisateur.get_full_name() or utilisateur.username}
        - Valeur saisie: {valeur_saisie}
        - Valeur attendue: {valeur_attendue}
        - Date: {timezone.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        if commentaire:
            message += f"\nCommentaire: {commentaire}"
        
        # Envoyer l'email
        send_mail(
            sujet,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )
        
        # Ajouter un message de succès
        messages.success(request, f"Notification d'anomalie envoyée pour le véhicule {vehicule.marque} {vehicule.modele}")
        
        return True
        
    except Exception as e:
        # En cas d'erreur, ajouter un message d'erreur
        messages.error(request, f"Erreur lors de l'envoi de la notification: {str(e)}")
        return False


def get_latest_vehicle_kilometrage(vehicule):
    """
    Récupère le dernier kilométrage enregistré pour un véhicule.

    Priorité: kilometrage_actuel centralisé, puis sources historiques.
    Retourne 0 si aucune valeur n'est disponible (jamais None).
    """
    if vehicule is None:
        return 0

    try:
        if vehicule.kilometrage_actuel is not None:
            return vehicule.kilometrage_actuel

        dernier_ravitaillement = Ravitaillement.objects.filter(
            vehicule=vehicule
        ).order_by('-date_ravitaillement').first()

        if dernier_ravitaillement and dernier_ravitaillement.kilometrage_apres is not None:
            return dernier_ravitaillement.kilometrage_apres

        dernier_entretien = Entretien.objects.filter(
            vehicule=vehicule
        ).order_by('-date_entretien').first()

        if dernier_entretien:
            if getattr(dernier_entretien, 'kilometrage_apres', None) is not None:
                return dernier_entretien.kilometrage_apres
            if dernier_entretien.kilometrage is not None:
                return dernier_entretien.kilometrage

        derniere_checklist = CheckListSecurite.objects.filter(
            vehicule=vehicule
        ).order_by('-date_controle').first()

        if derniere_checklist and derniere_checklist.kilometrage is not None:
            return derniere_checklist.kilometrage

        return 0

    except Exception as e:
        print(f"Erreur lors de la récupération du kilométrage: {str(e)}")
        return 0
