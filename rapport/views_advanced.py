from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.http import require_http_methods

from core.models import Vehicule, Utilisateur, Course, ActionTraceur
from entretien.models import Entretien
from ravitaillement.models import Ravitaillement
from .utils.generate_report_data import generer_rapport_complet

@login_required
def rapport_vehicule_advanced(request):
    """
    Vue pour afficher le rapport avancé d'un véhicule avec des données réelles
    """
    vehicules = Vehicule.objects.all().order_by('immatriculation')
    vehicule_id = request.GET.get('vehicule')
    selected_vehicule = None
    rapport = None
    if vehicule_id:
        try:
            selected_vehicule = Vehicule.objects.get(id=vehicule_id)
            rapport = get_vehicule_data(vehicule_id)
        except Vehicule.DoesNotExist:
            messages.error(request, f"Aucun véhicule trouvé avec l'ID {vehicule_id}.")
            rapport = None
    context = {
        'vehicules': vehicules,
        'selected_vehicule': selected_vehicule,
        'rapport': rapport,
        'page_title': 'Rapport avancé',
        'current_date': timezone.now().strftime('%d/%m/%Y'),
        'user': request.user,
    }
    export_format = request.GET.get('export')
    if export_format == 'pdf' and rapport:
        return generer_pdf_rapport_avance(context)
    elif export_format == 'excel' and rapport:
        return generer_excel_rapport_avance(context)
    return render(request, 'rapport/vehicule_advanced.html', context)

def generer_pdf_rapport_avance(context):
    """Génère un PDF du rapport avancé"""
    from weasyprint import HTML
    from django.template.loader import render_to_string
    
    # Rendre le template HTML en chaîne
    html_string = render_to_string('rapport/vehicule_advanced_pdf.html', context)
    
    # Créer un fichier PDF
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    # Créer la réponse HTTP avec le PDF
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f"rapport_avance_{context['rapport']['vehicule']['immatriculation']}_{timezone.now().strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def generer_excel_rapport_avance(context):
    """Génère un fichier Excel du rapport avancé"""
    import xlsxwriter
    from io import BytesIO
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    
    # Ajouter des formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#4F81BD',
        'color': 'white',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })
    
    # Feuille de synthèse
    worksheet = workbook.add_worksheet('Synthèse')
    
    # Écrire l'en-tête
    worksheet.merge_range('A1:D1', 'Rapport Avancé Véhicule', header_format)
    
    # Données du véhicule
    vehicule = context['rapport']['vehicule']
    stats = context['rapport']['statistiques']
    
    data = [
        ['Immatriculation', vehicule['immatriculation'], 'Marque', vehicule['marque']],
        ['Modèle', vehicule['modele'], 'Année', vehicule['annee']],
        ['Kilométrage actuel', f"{vehicule['kilometrage_actuel']} km", 'Statut', vehicule['statut']],
        ['Distance totale', f"{stats['distance_totale']} km", 'Nombre de missions', stats['missions_count']],
        ['Coût total carburant', f"{stats['cout_total_carburant']} €", 'Coût total entretien', f"{stats['cout_total_entretien']} €"],
    ]
    
    # Écrire les données
    for row_num, row_data in enumerate(data, 2):
        for col_num, cell_data in enumerate(row_data):
            worksheet.write(row_num, col_num, cell_data)
    
    # Ajuster la largeur des colonnes
    worksheet.set_column('A:D', 25)
    
    # Fermer le classeur
    workbook.close()
    
    # Préparer la réponse
    output.seek(0)
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"rapport_avance_{vehicule['immatriculation']}_{timezone.now().strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def get_vehicule_data(vehicule_id):
    """Récupère toutes les données réelles d'un véhicule et ses statistiques"""
    try:
        vehicule = Vehicule.objects.get(id=vehicule_id)
        entretiens = list(Entretien.objects.filter(vehicule=vehicule).order_by('-date_entretien'))
        ravitaillements = list(Ravitaillement.objects.filter(vehicule=vehicule).order_by('-date_ravitaillement'))
        missions = list(Course.objects.filter(vehicule=vehicule).order_by('-date_heure_depart'))
        # Incidents = missions avec commentaire contenant 'incident' ou statut particulier
        incidents = [m for m in missions if m.commentaires and 'incident' in m.commentaires.lower()]
        # Corrections km = actions traceur avec mot-clé
        corrections_km = list(ActionTraceur.objects.filter(vehicule=vehicule, action__icontains='correction').order_by('-date_action'))
        # Statistiques
        cout_total_carburant = sum(r.cout_total or 0 for r in ravitaillements)
        cout_total_entretien = sum(e.cout or 0 for e in entretiens)
        distance_totale = sum(m.distance_parcourue or 0 for m in missions if m.statut == 'terminee')
        litres_total = sum(r.litres or 0 for r in ravitaillements)
        conso_moyenne = round((litres_total * 100 / distance_totale), 2) if distance_totale > 0 else None
        # Alertes (exemple: entretien à venir)
        prochain_entretien = Entretien.objects.filter(vehicule=vehicule, date_entretien__gt=timezone.now()).order_by('date_entretien').first()
        # Préparer le rapport
        rapport = {
            'vehicule': {
                'immatriculation': vehicule.immatriculation,
                'marque': vehicule.marque,
                'modele': vehicule.modele,
                'annee': vehicule.annee,
                'kilometrage_actuel': vehicule.kilometrage_actuel,
                'type_vehicule': vehicule.type_vehicule,
                'statut': vehicule.statut,
                'carburant': vehicule.carburant,
                'consommation_moyenne': conso_moyenne,
                'date_mise_en_circulation': getattr(vehicule, 'date_mise_en_circulation', None),
            },
            'statistiques': {
                'missions_count': len(missions),
                'distance_totale': distance_totale,
                'conso_moyenne': conso_moyenne,
                'cout_total_carburant': cout_total_carburant,
                'cout_total_entretien': cout_total_entretien,
                'cout_total': cout_total_carburant + cout_total_entretien,
                'incidents': len(incidents),
            },
            'entretiens': entretiens,
            'ravitaillements': ravitaillements,
            'missions': missions,
            'incidents': incidents,
            'corrections_km': corrections_km,
            'prochain_entretien': prochain_entretien,
            'alertes': [],  # À enrichir plus tard
        }
        return rapport
    except Vehicule.DoesNotExist:
        return None
