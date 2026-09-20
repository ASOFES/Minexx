"""
Utilitaires pour l'export PDF.
Priorité : pdfkit + wkhtmltopdf si disponible, sinon xhtml2pdf.
"""

import os
import shutil
import tempfile
from io import BytesIO

from django.http import HttpResponse
from django.template.loader import render_to_string


def _candidate_wkhtmltopdf_paths():
    """Chemins possibles selon l'OS / la config."""
    env_path = os.environ.get('WKHTMLTOPDF_CMD') or os.environ.get('WKHTMLTOPDF_PATH')
    if env_path:
        yield env_path

    which = shutil.which('wkhtmltopdf')
    if which:
        yield which

    yield r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    yield r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe'
    yield '/usr/local/bin/wkhtmltopdf'
    yield '/usr/bin/wkhtmltopdf'
    yield '/bin/wkhtmltopdf'


def find_wkhtmltopdf():
    """Retourne le chemin absolu de wkhtmltopdf, ou None."""
    for path in _candidate_wkhtmltopdf_paths():
        if path and os.path.isfile(path):
            return path
    return None


WKHTMLTOPDF_PATH = find_wkhtmltopdf()


def _pdfkit_config():
    import pdfkit
    path = find_wkhtmltopdf()
    if not path:
        return None
    return pdfkit.configuration(wkhtmltopdf=path)


def _pdfkit_options():
    return {
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


def _http_pdf_response(pdf_content, filename=None):
    response = HttpResponse(pdf_content, content_type='application/pdf')
    name = filename or 'export.pdf'
    response['Content-Disposition'] = f'attachment; filename="{name}"'
    return response


def _generate_with_pdfkit(html_content):
    import pdfkit

    config = _pdfkit_config()
    if not config:
        raise FileNotFoundError('wkhtmltopdf introuvable')

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        pdfkit.from_string(
            html_content,
            temp_path,
            options=_pdfkit_options(),
            configuration=config,
        )
        with open(temp_path, 'rb') as pdf_file:
            return pdf_file.read()
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def _generate_with_xhtml2pdf(html_content):
    from xhtml2pdf import pisa

    result = BytesIO()
    pdf = pisa.CreatePDF(html_content, dest=result, encoding='utf-8')
    if pdf.err:
        raise RuntimeError('xhtml2pdf a renvoyé une erreur de rendu')
    return result.getvalue()


def html_bytes_to_pdf(html_content):
    """
    Convertit du HTML en bytes PDF.
    Utilise pdfkit si wkhtmltopdf est présent, sinon xhtml2pdf.
    """
    if find_wkhtmltopdf():
        try:
            return _generate_with_pdfkit(html_content)
        except Exception:
            # Repli si pdfkit échoue malgré la présence du binaire
            pass
    return _generate_with_xhtml2pdf(html_content)


class PDFExportError(Exception):
    """Exception personnalisée pour les erreurs d'export PDF"""
    pass


def render_to_pdf(template_name, context, filename=None):
    """
    Génère un PDF à partir d'un template Django.
    """
    try:
        html_content = render_to_string(template_name, context)
        html_content = preprocess_html_for_pdf(html_content)
        pdf_content = html_bytes_to_pdf(html_content)
        return _http_pdf_response(pdf_content, filename)
    except Exception as e:
        error_message = f"Erreur lors de la génération du PDF: {str(e)}"
        return HttpResponse(error_message, content_type='text/plain; charset=utf-8', status=500)


def html_to_pdf(html_content, filename=None):
    """Convertit du HTML en PDF (HttpResponse)."""
    try:
        pdf_content = html_bytes_to_pdf(html_content)
        return _http_pdf_response(pdf_content, filename)
    except Exception as e:
        error_message = f"Erreur lors de la conversion HTML vers PDF: {str(e)}"
        return HttpResponse(error_message, content_type='text/plain; charset=utf-8', status=500)


def markdown_to_pdf(markdown_content, filename=None):
    """Convertit du Markdown en PDF."""
    try:
        import markdown

        html_content = markdown.markdown(markdown_content)
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
        return html_to_pdf(html_with_css, filename)
    except Exception as e:
        error_message = f"Erreur lors de la conversion Markdown vers PDF: {str(e)}"
        return HttpResponse(error_message, content_type='text/plain; charset=utf-8', status=500)


def is_pdf_available():
    """True si au moins un moteur PDF est utilisable."""
    if find_wkhtmltopdf():
        try:
            import pdfkit  # noqa: F401
            return True
        except ImportError:
            pass
    try:
        from xhtml2pdf import pisa  # noqa: F401
        return True
    except ImportError:
        return False


def preprocess_html_for_pdf(html_content):
    """Prétraite le HTML pour optimiser la génération PDF."""
    try:
        html_content = convert_image_paths(html_content)
        html_content = add_pdf_optimized_css(html_content)
        return html_content
    except Exception as e:
        print(f"Erreur lors du prétraitement HTML: {e}")
        return html_content


def convert_image_paths(html_content):
    """Convertit les chemins relatifs des images en chemins absolus."""
    try:
        import re
        from django.contrib.staticfiles import finders

        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'

        def replace_img_src(match):
            img_tag = match.group(0)
            src_path = match.group(1)

            if src_path.startswith(('http://', 'https://', 'data:', 'file:')):
                return img_tag

            if src_path.startswith('static/'):
                static_path = src_path.replace('static/', '', 1)
                absolute_path = finders.find(static_path)
                if absolute_path:
                    return img_tag.replace(f'src="{src_path}"', f'src="file:///{absolute_path}"')

            return img_tag

        return re.sub(img_pattern, replace_img_src, html_content)
    except Exception as e:
        print(f"Erreur lors de la conversion des chemins d'images: {e}")
        return html_content


def add_pdf_optimized_css(html_content):
    """Ajoute des styles CSS optimisés pour la génération PDF."""
    try:
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

        if '<head>' in html_content:
            return html_content.replace('<head>', f'<head>{pdf_css}', 1)

        return f'<html><head>{pdf_css}</head><body>{html_content}</body></html>'
    except Exception as e:
        print(f"Erreur lors de l'ajout du CSS PDF: {e}")
        return html_content


def get_pdf_status_message():
    """Message sur le statut de la génération PDF."""
    if is_pdf_available():
        engine = 'wkhtmltopdf' if find_wkhtmltopdf() else 'xhtml2pdf'
        return f"Export PDF disponible ({engine})"
    return "Export PDF non disponible - bibliothèques manquantes"
