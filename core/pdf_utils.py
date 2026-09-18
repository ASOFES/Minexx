"""
Utilitaires pour l'export PDF utilisant des alternatives compatibles Python 3.13
"""

# Nouvelles bibliothèques PDF compatibles Python 3.13
import os
import tempfile
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
import markdown
import pdfkit
from pathlib import Path

# Configuration globale pour wkhtmltopdf
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'

class PDFExportError(Exception):
    """Exception personnalisée pour les erreurs d'export PDF"""
    pass

def render_to_pdf(template_name, context, filename=None):
    """
    Génère un PDF à partir d'un template Django en utilisant pdfkit
    avec gestion optimisée des images et fichiers statiques
    
    Args:
        template_name: Nom du template à utiliser
        context: Contexte pour le template
        filename: Nom du fichier PDF (optionnel)
    
    Returns:
        HttpResponse avec le PDF en attachement
    """
    try:
        # Rendre le template en HTML
        html_content = render_to_string(template_name, context)
        
        # Prétraiter le HTML pour optimiser les images
        html_content = preprocess_html_for_pdf(html_content)
        
        # Créer un fichier temporaire pour le PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Configuration pdfkit optimisée pour Render
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
            'disable-smart-shrinking': None,
            'image-quality': 100,
            'image-dpi': 300,
            'javascript-delay': 1000,
            'no-stop-slow-scripts': None,
        }
        
        # Configuration du chemin vers wkhtmltopdf
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
        
        # Générer le PDF
        pdfkit.from_string(html_content, temp_path, options=options, configuration=config)
        
        # Lire le PDF généré
        with open(temp_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Nettoyer le fichier temporaire
        os.unlink(temp_path)
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf_content, content_type='application/pdf')
        if filename:
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        else:
            response['Content-Disposition'] = 'attachment; filename="export.pdf"'
        
        return response
        
    except Exception as e:
        # En cas d'erreur, retourner un message d'erreur
        error_message = f"Erreur lors de la génération du PDF: {str(e)}"
        return HttpResponse(error_message, content_type='text/plain', status=500)

def html_to_pdf(html_content, filename=None):
    """
    Convertit du HTML en PDF
    
    Args:
        html_content: Contenu HTML à convertir
        filename: Nom du fichier PDF (optionnel)
    
    Returns:
        HttpResponse avec le PDF en attachement
    """
    try:
        # Créer un fichier temporaire pour le PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Configuration pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
        }
        
        # Configuration du chemin vers wkhtmltopdf
        config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
        
        # Générer le PDF
        pdfkit.from_string(html_content, temp_path, options=options, configuration=config)
        
        # Lire le PDF généré
        with open(temp_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Nettoyer le fichier temporaire
        os.unlink(temp_path)
        
        # Créer la réponse HTTP
        response = HttpResponse(pdf_content, content_type='application/pdf')
        if filename:
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        else:
            response['Content-Disposition'] = 'attachment; filename="export.pdf"'
        
        return response
        
    except Exception as e:
        error_message = f"Erreur lors de la conversion HTML vers PDF: {str(e)}"
        return HttpResponse(error_message, content_type='text/plain', status=500)

def markdown_to_pdf(markdown_content, filename=None):
    """
    Convertit du Markdown en PDF
    
    Args:
        markdown_content: Contenu Markdown à convertir
        filename: Nom du fichier PDF (optionnel)
    
    Returns:
        HttpResponse avec le PDF en attachement
    """
    try:
        # Convertir Markdown en HTML
        html_content = markdown.markdown(markdown_content)
        
        # Ajouter du CSS de base
        html_with_css = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Convertir en PDF
        return html_to_pdf(html_with_css, filename)
        
    except Exception as e:
        error_message = f"Erreur lors de la conversion Markdown vers PDF: {str(e)}"
        return HttpResponse(error_message, content_type='text/plain', status=500)

def is_pdf_available():
    """
    Vérifie si la génération PDF est disponible
    
    Returns:
        bool: True si PDF disponible, False sinon
    """
    try:
        import pdfkit
        return True
    except ImportError:
        return False

def preprocess_html_for_pdf(html_content):
    """
    Prétraite le HTML pour optimiser la génération PDF avec pdfkit
    
    Args:
        html_content: Contenu HTML brut
    
    Returns:
        str: HTML prétraité optimisé pour PDF
    """
    try:
        # Convertir les chemins relatifs des images en chemins absolus
        html_content = convert_image_paths(html_content)
        
        # Ajouter des styles CSS optimisés pour PDF
        html_content = add_pdf_optimized_css(html_content)
        
        return html_content
        
    except Exception as e:
        print(f"Erreur lors du prétraitement HTML: {e}")
        return html_content

def convert_image_paths(html_content):
    """
    Convertit les chemins relatifs des images en chemins absolus
    
    Args:
        html_content: Contenu HTML
    
    Returns:
        str: HTML avec chemins d'images convertis
    """
    try:
        import re
        from django.contrib.staticfiles import finders
        
        # Pattern pour trouver les balises img avec src relatif
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        
        def replace_img_src(match):
            img_tag = match.group(0)
            src_path = match.group(1)
            
            # Si c'est déjà un chemin absolu ou une URL, ne rien changer
            if src_path.startswith(('http://', 'https://', 'data:', '/')):
                return img_tag
            
            # Si c'est un chemin statique, le convertir en chemin absolu
            if src_path.startswith('static/'):
                static_path = src_path.replace('static/', '')
                absolute_path = finders.find(static_path)
                if absolute_path:
                    # Convertir en chemin de fichier local pour pdfkit
                    return img_tag.replace(f'src="{src_path}"', f'src="file://{absolute_path}"')
            
            return img_tag
        
        # Appliquer les remplacements
        html_content = re.sub(img_pattern, replace_img_src, html_content)
        
        return html_content
        
    except Exception as e:
        print(f"Erreur lors de la conversion des chemins d'images: {e}")
        return html_content

def add_pdf_optimized_css(html_content):
    """
    Ajoute des styles CSS optimisés pour la génération PDF
    
    Args:
        html_content: Contenu HTML
    
    Returns:
        str: HTML avec CSS optimisé pour PDF
    """
    try:
        # CSS optimisé pour PDF
        pdf_css = """
        <style>
            @page {
                size: A4;
                margin: 0.75in;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
                color: #333;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                font-size: 11px;
            }
            th {
                background-color: #f2f2f2;
                font-weight: bold;
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 10px auto;
            }
            .logo {
                max-height: 60px;
                max-width: 200px;
            }
            h1, h2, h3 {
                color: #2c3e50;
                margin: 15px 0 10px 0;
            }
            h1 { font-size: 18px; }
            h2 { font-size: 16px; }
            h3 { font-size: 14px; }
        </style>
        """
        
        # Insérer le CSS dans le head du HTML
        if '<head>' in html_content:
            html_content = html_content.replace('<head>', f'<head>{pdf_css}')
        else:
            # Si pas de head, l'ajouter au début
            html_content = f'<html><head>{pdf_css}</head><body>{html_content}</body></html>'
        
        return html_content
        
    except Exception as e:
        print(f"Erreur lors de l'ajout du CSS PDF: {e}")
        return html_content

def get_pdf_status_message():
    """
    Retourne un message sur le statut de la génération PDF
    
    Returns:
        str: Message d'information
    """
    if is_pdf_available():
        return "Export PDF disponible"
    else:
        return "Export PDF non disponible - bibliothèques manquantes"
