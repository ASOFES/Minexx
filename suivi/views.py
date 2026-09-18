from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from core.models import Vehicule, Course, ActionTraceur
from entretien.models import Entretien
from ravitaillement.models import Ravitaillement
from .models import SuiviVehicule
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
import csv
import xlwt
from django.template.loader import get_template
# from xhtml2pdf import pisa  # Temporairement commenté pour le déploiement
from io import BytesIO
from django.utils import timezone
from django.conf import settings
from django.core.paginator import Paginator

# Fonction pour vérifier si l'utilisateur est admin ou superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin_or_superuser)
def dashboard(request):
    """Vue pour le tableau de bord du module Suivi"""
    # Récupérer les statistiques générales
    vehicules_count = Vehicule.objects.count()
    courses_count = Course.objects.count()
    entretiens_count = Entretien.objects.count()
    ravitaillements_count = Ravitaillement.objects.count()
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation du tableau de bord Suivi",
    )
    
    context = {
        'vehicules_count': vehicules_count,
        'courses_count': courses_count,
        'entretiens_count': entretiens_count,
        'ravitaillements_count': ravitaillements_count,
    }
    
    return render(request, 'suivi/dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def suivi_vehicules(request):
    """Vue pour le suivi des véhicules"""
    vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        vehicules = vehicules.filter(
            Q(immatriculation__icontains=search_query) |
            Q(marque__icontains=search_query) |
            Q(modele__icontains=search_query)
        )
    
    # Tri
    sort_by = request.GET.get('sort', 'immatriculation')
    if sort_by.startswith('-'):
        sort_field = sort_by[1:]  # Enlever le - pour le traitement
        reverse_sort = True
    else:
        sort_field = sort_by
        reverse_sort = False
    
    # Préparer les données de suivi pour chaque véhicule
    vehicules_data = []
    for vehicule in vehicules:
        # Calculer la distance totale parcourue
        distance_totale = Course.objects.filter(
            vehicule=vehicule, 
            statut='terminee'
        ).aggregate(Sum('distance_parcourue'))['distance_parcourue__sum'] or 0
        
        # Calculer le nombre d'entretiens
        nombre_entretiens = Entretien.objects.filter(vehicule=vehicule).count()
        
        # Calculer le volume de carburant consommé
        volume_carburant = Ravitaillement.objects.filter(
            vehicule=vehicule
        ).aggregate(Sum('litres'))['litres__sum'] or 0
        
        vehicules_data.append({
            'vehicule': vehicule,
            'distance_totale': distance_totale,
            'nombre_entretiens': nombre_entretiens,
            'volume_carburant': volume_carburant
        })
    
    # Tri des données
    if sort_field == 'immatriculation':
        vehicules_data.sort(key=lambda x: x['vehicule'].immatriculation, reverse=reverse_sort)
    elif sort_field == 'marque':
        vehicules_data.sort(key=lambda x: x['vehicule'].marque, reverse=reverse_sort)
    elif sort_field == 'date_immatriculation':
        vehicules_data.sort(key=lambda x: x['vehicule'].date_immatriculation or timezone.datetime.min.date(), reverse=reverse_sort)
    elif sort_field == 'distance_totale':
        vehicules_data.sort(key=lambda x: x['distance_totale'], reverse=reverse_sort)
    elif sort_field == 'nombre_entretiens':
        vehicules_data.sort(key=lambda x: x['nombre_entretiens'], reverse=reverse_sort)
    elif sort_field == 'volume_carburant':
        vehicules_data.sort(key=lambda x: x['volume_carburant'], reverse=reverse_sort)
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation du suivi des véhicules",
    )
    
    context = {
        'vehicules_data': vehicules_data,
    }
    
    return render(request, 'suivi/suivi_vehicules.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def export_vehicules_pdf(request):
    """Exporter la liste des véhicules en PDF"""
    # Temporairement désactivé pour le déploiement - xhtml2pdf en cours de configuration
    return HttpResponse(
        "Export PDF temporairement indisponible - xhtml2pdf en cours de configuration",
        content_type='text/plain'
    )

@login_required
@user_passes_test(is_admin_or_superuser)
def export_vehicules_excel(request):
    """Exporter la liste des véhicules en Excel"""
    vehicules = Vehicule.objects.all()
    if not request.user.is_superuser:
        vehicules = vehicules.filter(etablissement=request.user.etablissement)
    # Créer un nouveau classeur Excel
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Suivi Véhicules')
    
    # Définir les styles
    header_style = xlwt.easyxf('font: bold on; pattern: pattern solid, fore_colour gray25; align: horiz center')
    date_style = xlwt.easyxf('font: bold off; align: horiz right', num_format_str='DD/MM/YYYY')
    number_style = xlwt.easyxf('font: bold off; align: horiz right')
    
    # Écrire les en-têtes
    headers = [
        'Immatriculation', 'Marque', 'Modèle', 'Châssis', 'Moteur', 'Carte rose',
        'Pneu AG', 'Pneu AD', 'Pneu ARG', 'Pneu ARD', 'Pneu secours',
        'Km début', 'Km actuel', 'Date Immatriculation',
        'Distance Parcourue (km)', 'Nombre Entretiens', 'Volume Carburant (L)', 'Statut',
    ]
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, header_style)
        ws.col(col_num).width = 256 * 18
    
    # Récupérer les données
    row_num = 1
    
    for vehicule in vehicules:
        # Calculer la distance totale parcourue
        distance_totale = Course.objects.filter(
            vehicule=vehicule, 
            statut='terminee'
        ).aggregate(Sum('distance_parcourue'))['distance_parcourue__sum'] or 0
        
        # Calculer le nombre d'entretiens
        nombre_entretiens = Entretien.objects.filter(vehicule=vehicule).count()
        
        # Calculer le volume de carburant consommé
        volume_carburant = Ravitaillement.objects.filter(
            vehicule=vehicule
        ).aggregate(Sum('litres'))['litres__sum'] or 0
        
        # Écrire les données
        ws.write(row_num, 0, vehicule.immatriculation)
        ws.write(row_num, 1, vehicule.marque)
        ws.write(row_num, 2, vehicule.modele)
        ws.write(row_num, 3, vehicule.numero_chassis or '')
        ws.write(row_num, 4, vehicule.numero_moteur or '')
        ws.write(row_num, 5, vehicule.numero_carte_rose or '')
        ws.write(row_num, 6, vehicule.numero_pneu_avant_gauche or '')
        ws.write(row_num, 7, vehicule.numero_pneu_avant_droit or '')
        ws.write(row_num, 8, vehicule.numero_pneu_arriere_gauche or '')
        ws.write(row_num, 9, vehicule.numero_pneu_arriere_droit or '')
        ws.write(row_num, 10, vehicule.numero_pneu_secours or '')
        ws.write(row_num, 11, vehicule.kilometrage_debut if vehicule.kilometrage_debut is not None else '', number_style)
        ws.write(row_num, 12, vehicule.kilometrage_actuel if vehicule.kilometrage_actuel is not None else '', number_style)
        if vehicule.date_immatriculation:
            ws.write(row_num, 13, vehicule.date_immatriculation, date_style)
        else:
            ws.write(row_num, 13, "Non renseignée")
        ws.write(row_num, 14, distance_totale, number_style)
        ws.write(row_num, 15, nombre_entretiens, number_style)
        ws.write(row_num, 16, float(volume_carburant), number_style)
        ws.write(row_num, 17, "Disponible" if vehicule.est_disponible() else "Indisponible")
        
        row_num += 1
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Export Excel du suivi des véhicules",
    )
    
    # Préparer la réponse
    response = HttpResponse(content_type='application/ms-excel')
    etab_nom = request.user.etablissement.nom if getattr(request.user, 'etablissement', None) and not request.user.is_superuser else 'Tous'
    response['Content-Disposition'] = f'attachment; filename="suivi_vehicules_{etab_nom}.xls"'
    
    # Sauvegarder le classeur dans la réponse
    wb.save(response)
    
    return response

@login_required
@user_passes_test(is_admin_or_superuser)
def suivi_missions(request):
    """Vue pour le suivi des missions"""
    # Récupérer toutes les courses
    courses = Course.objects.filter(etablissement=request.user.etablissement)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(demandeur__first_name__icontains=search_query) |
            Q(demandeur__last_name__icontains=search_query) |
            Q(destination__icontains=search_query) |
            Q(vehicule__immatriculation__icontains=search_query) |
            Q(chauffeur__first_name__icontains=search_query) |
            Q(chauffeur__last_name__icontains=search_query)
        )
    
    # Tri
    sort_by = request.GET.get('sort', '-date_demande')
    # Valider le paramètre de tri pour éviter les injections SQL
    valid_sort_fields = [
        'date_demande', '-date_demande',
        'demandeur__last_name', '-demandeur__last_name',
        'destination', '-destination',
        'statut', '-statut'
    ]
    
    if sort_by not in valid_sort_fields:
        sort_by = '-date_demande'  # Valeur par défaut sécurisée
        
    courses = courses.order_by(sort_by)
    
    # Calculer la distance totale parcourue
    distance_totale = courses.aggregate(Sum('distance_parcourue'))['distance_parcourue__sum'] or 0
    
    # Pagination
    paginator = Paginator(courses, 12)  # 12 courses par page
    page_number = request.GET.get('page')
    courses_page = paginator.get_page(page_number)
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation du suivi des missions",
    )
    
    context = {
        'courses': courses_page,
        'distance_totale': distance_totale,
        'search_query': search_query,
    }
    
    return render(request, 'suivi/suivi_missions.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def export_missions_pdf(request):
    """Exporter la liste des missions en PDF"""
    # Temporairement désactivé pour le déploiement - xhtml2pdf en cours de configuration
    return HttpResponse(
        "Export PDF temporairement indisponible - xhtml2pdf en cours de configuration",
        content_type='text/plain'
    )

@login_required
@user_passes_test(is_admin_or_superuser)
def export_missions_excel(request):
    """Exporter la liste des missions en Excel"""
    queryset = Course.objects.all()
    if not request.user.is_superuser:
        queryset = queryset.filter(departement=request.user.departement)
    # Initialiser le queryset
    missions = queryset.order_by('-date_demande')
    
    # Calculer la distance totale parcourue
    distance_totale = queryset.aggregate(Sum('distance_parcourue'))['distance_parcourue__sum'] or 0
    
    # Créer un nouveau classeur Excel
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Suivi Missions')
    
    # Définir les styles
    header_style = xlwt.easyxf('font: bold on; pattern: pattern solid, fore_colour gray25; align: horiz center')
    date_style = xlwt.easyxf('font: bold off; align: horiz right', num_format_str='DD/MM/YYYY HH:MM')
    number_style = xlwt.easyxf('font: bold off; align: horiz right')
    total_style = xlwt.easyxf('font: bold on; align: horiz right')
    
    # Écrire les en-têtes
    headers = ['Date', 'Véhicule', 'Chauffeur', 'Demandeur', 'Destination', 'Statut', 'Distance (km)']
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, header_style)
        ws.col(col_num).width = 256 * 20  # 20 caractères de large
    
    # Écrire les données
    row_num = 1
    
    for mission in missions:
        # Écrire les données
        ws.write(row_num, 0, mission.date_demande, date_style)
        
        if mission.vehicule:
            ws.write(row_num, 1, mission.vehicule.immatriculation)
        else:
            ws.write(row_num, 1, "Non assigné")
            
        if mission.chauffeur:
            ws.write(row_num, 2, mission.chauffeur.get_full_name())
        else:
            ws.write(row_num, 2, "Non assigné")
            
        if mission.demandeur:
            if mission.demandeur.get_full_name():
                ws.write(row_num, 3, mission.demandeur.get_full_name())
            else:
                ws.write(row_num, 3, mission.demandeur.username)
        else:
            ws.write(row_num, 3, "Non spécifié")
            
        ws.write(row_num, 4, mission.destination)
        
        # Statut en français
        statut_map = {
            'en_attente': 'En attente',
            'validee': 'Validée',
            'en_cours': 'En cours',
            'terminee': 'Terminée',
            'annulee': 'Annulée'
        }
        ws.write(row_num, 5, statut_map.get(mission.statut, mission.statut))
        
        if mission.distance_parcourue:
            ws.write(row_num, 6, float(mission.distance_parcourue), number_style)
        else:
            ws.write(row_num, 6, "-")
        
        row_num += 1
    
    # Ajouter une ligne de total
    row_num += 1
    ws.write(row_num, 0, "TOTAL", total_style)
    ws.write(row_num, 6, float(distance_totale), total_style)
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Export Excel du suivi des missions",
    )
    
    # Préparer la réponse
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="Suivi Missions - Département : {request.user.departement.nom if not request.user.is_superuser else "Tous"}.xls"'
    
    # Sauvegarder le classeur dans la réponse
    wb.save(response)
    
    return response

@login_required
@user_passes_test(is_admin_or_superuser)
def suivi_entretiens(request):
    """Vue pour le suivi des entretiens"""
    # Initialiser le queryset
    queryset = Entretien.objects.filter(vehicule__etablissement=request.user.etablissement)
    
    # Recherche
    search_query = request.GET.get('search', '')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if search_query:
        queryset = queryset.filter(
            Q(vehicule__immatriculation__icontains=search_query) |
            Q(garage__icontains=search_query) |
            Q(motif__icontains=search_query)
        )
    
    # Filtrer par date
    if date_debut:
        queryset = queryset.filter(date_entretien__date__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_entretien__date__lte=date_fin)
    
    # Tri
    sort_by = request.GET.get('sort', '-date_entretien')
    valid_sort_fields = [
        'date_entretien', '-date_entretien',
        'vehicule__immatriculation', '-vehicule__immatriculation',
        'garage', '-garage',
        'cout', '-cout',
        'statut', '-statut'
    ]
    
    if sort_by not in valid_sort_fields:
        sort_by = '-date_entretien'  # Valeur par défaut sécurisée
    
    entretiens = queryset.order_by(sort_by)
    
    # Calculer le coût total des entretiens
    cout_total = queryset.aggregate(Sum('cout'))['cout__sum'] or 0
    
    # Pagination
    paginator = Paginator(entretiens, 12)  # 12 entretiens par page
    page_number = request.GET.get('page')
    entretiens_page = paginator.get_page(page_number)
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation du suivi des entretiens",
    )
    
    context = {
        'entretiens': entretiens_page,
        'cout_total': cout_total,
        'search_query': search_query,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'suivi/suivi_entretiens.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def export_entretiens_pdf(request):
    """Exporter la liste des entretiens en PDF"""
    # Temporairement désactivé pour le déploiement - xhtml2pdf en cours de configuration
    return HttpResponse(
        "Export PDF temporairement indisponible - xhtml2pdf en cours de configuration",
        content_type='text/plain'
    )

@login_required
@user_passes_test(is_admin_or_superuser)
def export_entretiens_excel(request):
    """Exporter la liste des entretiens en Excel"""
    queryset = Entretien.objects.all()
    if not request.user.is_superuser:
        queryset = queryset.filter(vehicule__departement=request.user.departement)
    # Recherche
    search_query = request.GET.get('search', '')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if search_query:
        queryset = queryset.filter(
            Q(vehicule__immatriculation__icontains=search_query) |
            Q(garage__icontains=search_query) |
            Q(motif__icontains=search_query)
        )
    
    # Filtrer par date
    if date_debut:
        queryset = queryset.filter(date_entretien__date__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_entretien__date__lte=date_fin)
    
    # Tri
    sort_by = request.GET.get('sort', '-date_entretien')
    valid_sort_fields = [
        'date_entretien', '-date_entretien',
        'vehicule__immatriculation', '-vehicule__immatriculation',
        'garage', '-garage',
        'cout', '-cout',
        'statut', '-statut'
    ]
    
    if sort_by not in valid_sort_fields:
        sort_by = '-date_entretien'  # Valeur par défaut sécurisée
    
    entretiens = queryset.order_by(sort_by)
    
    # Calculer le coût total des entretiens
    cout_total = queryset.aggregate(Sum('cout'))['cout__sum'] or 0
    
    # Créer un nouveau classeur Excel
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Suivi Entretiens')
    
    # Définir les styles
    header_style = xlwt.easyxf('font: bold on; pattern: pattern solid, fore_colour gray25; align: horiz center')
    date_style = xlwt.easyxf('font: bold off; align: horiz right', num_format_str='DD/MM/YYYY')
    number_style = xlwt.easyxf('font: bold off; align: horiz right')
    total_style = xlwt.easyxf('font: bold on; align: horiz right')
    
    # Écrire les en-têtes
    headers = ['Date', 'Véhicule', 'Châssis', 'Moteur', 'Carte rose', 'Km début', 'Pneus', 'Garage', 'Motif', 'Coût ($)', 'Statut']
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, header_style)
        ws.col(col_num).width = 256 * 20  # 20 caractères de large
    
    # Écrire les données
    row_num = 1
    
    for entretien in entretiens:
        # Écrire les données
        ws.write(row_num, 0, entretien.date_entretien, date_style)
        ws.write(row_num, 1, f"{entretien.vehicule.immatriculation} ({entretien.vehicule.marque} {entretien.vehicule.modele})")
        ws.write(row_num, 2, entretien.vehicule.numero_chassis or '')
        ws.write(row_num, 3, entretien.vehicule.numero_moteur or '')
        ws.write(row_num, 4, entretien.vehicule.numero_carte_rose or '')
        ws.write(row_num, 5, entretien.vehicule.kilometrage_debut if entretien.vehicule.kilometrage_debut is not None else '', number_style)
        ws.write(row_num, 6, entretien.vehicule.pneus_resume() or '')
        ws.write(row_num, 7, entretien.garage)
        ws.write(row_num, 8, entretien.motif)
        ws.write(row_num, 9, float(entretien.cout) if entretien.cout is not None else 0, number_style)
        
        # Statut en français
        statut_map = {
            'planifie': 'Planifié',
            'en_cours': 'En cours',
            'termine': 'Terminé',
            'annule': 'Annulé'
        }
        ws.write(row_num, 10, statut_map.get(entretien.statut, entretien.statut))
        
        row_num += 1
    
    # Ajouter une ligne de total
    row_num += 1
    ws.write(row_num, 0, "TOTAL", total_style)
    ws.write(row_num, 9, float(cout_total), total_style)
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Export Excel du suivi des entretiens",
    )
    
    # Préparer la réponse
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="Suivi Entretiens - Département : {request.user.departement.nom if not request.user.is_superuser else "Tous"}.xls"'
    
    # Sauvegarder le classeur dans la réponse
    wb.save(response)
    
    return response

@login_required
@user_passes_test(is_admin_or_superuser)
def suivi_carburant(request):
    """Vue pour le suivi de la consommation de carburant"""
    # Initialiser le queryset
    queryset = Ravitaillement.objects.filter(vehicule__etablissement=request.user.etablissement)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(vehicule__immatriculation__icontains=search_query) |
            Q(nom_station__icontains=search_query) |
            Q(commentaires__icontains=search_query)
        )
    
    # Filtres supplémentaires
    vehicule_id = request.GET.get('vehicule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if date_debut:
        queryset = queryset.filter(date_ravitaillement__date__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_ravitaillement__date__lte=date_fin)
    
    # Tri
    sort_by = request.GET.get('sort', '-date_ravitaillement')
    valid_sort_fields = [
        'date_ravitaillement', '-date_ravitaillement',
        'vehicule__immatriculation', '-vehicule__immatriculation',
        'litres', '-litres',
        'cout_total', '-cout_total',
        'consommation_moyenne', '-consommation_moyenne'
    ]
    
    if sort_by not in valid_sort_fields:
        sort_by = '-date_ravitaillement'  # Valeur par défaut sécurisée
        
    queryset = queryset.order_by(sort_by)
    
    # Calcul des totaux
    total_litres = queryset.aggregate(Sum('litres'))['litres__sum'] or 0
    total_cout = queryset.aggregate(Sum('cout_total'))['cout_total__sum'] or 0
    
    # Pagination
    paginator = Paginator(queryset, 12)  # 12 ravitaillements par page
    page_number = request.GET.get('page')
    ravitaillements_page = paginator.get_page(page_number)
    
    # Récupérer tous les véhicules pour le filtre
    vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement).order_by('immatriculation')
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation du suivi de la consommation de carburant",
    )
    
    context = {
        'ravitaillements': ravitaillements_page,
        'vehicules': vehicules,
        'total_litres': total_litres,
        'total_cout': total_cout,
        'search_query': search_query,
        'selected_vehicule': vehicule_id,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'selected_sort': sort_by,
        'departement_nom': request.user.departement.nom if not request.user.is_superuser else 'Tous'
    }
    
    return render(request, 'suivi/suivi_carburant.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def export_carburant_pdf(request):
    """Exporter le suivi de la consommation de carburant en PDF"""
    # Temporairement désactivé pour le déploiement - xhtml2pdf en cours de configuration
    return HttpResponse(
        "Export PDF temporairement indisponible - xhtml2pdf en cours de configuration",
        content_type='text/plain'
    )

@login_required
@user_passes_test(is_admin_or_superuser)
def export_carburant_excel(request):
    """Exporter le suivi de la consommation de carburant en Excel"""
    queryset = Ravitaillement.objects.all()
    if not request.user.is_superuser:
        queryset = queryset.filter(vehicule__departement=request.user.departement)
    # Initialiser le queryset
    ravitaillements = queryset.order_by('-date_ravitaillement')
    
    # Calcul des totaux
    total_litres = ravitaillements.aggregate(Sum('litres'))['litres__sum'] or 0
    total_cout = ravitaillements.aggregate(Sum('cout_total'))['cout_total__sum'] or 0
    
    # Créer un nouveau classeur Excel
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Suivi Carburant')
    
    # Définir les styles
    header_style = xlwt.easyxf('font: bold on; pattern: pattern solid, fore_colour gray25; align: horiz center')
    date_style = xlwt.easyxf('font: bold off; align: horiz right', num_format_str='DD/MM/YYYY HH:MM')
    number_style = xlwt.easyxf('font: bold off; align: horiz right')
    
    # Écrire les en-têtes
    headers = ['Date', 'Véhicule', 'Station', 'Kilométrage', 'Distance', 'Litres', 'Prix/L', 'Coût total', 'Conso. (L/100km)']
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header, header_style)
        ws.col(col_num).width = 256 * 20  # 20 caractères de large
    
    # Écrire les données
    row_num = 1
    for ravitaillement in ravitaillements:
        ws.write(row_num, 0, ravitaillement.date_ravitaillement, date_style)
        ws.write(row_num, 1, ravitaillement.vehicule.immatriculation)
        ws.write(row_num, 2, ravitaillement.nom_station or 'Non spécifiée')
        ws.write(row_num, 3, ravitaillement.kilometrage_apres, number_style)
        ws.write(row_num, 4, ravitaillement.distance_parcourue, number_style)
        ws.write(row_num, 5, float(ravitaillement.litres), number_style)
        ws.write(row_num, 6, float(ravitaillement.cout_unitaire), number_style)
        ws.write(row_num, 7, float(ravitaillement.cout_total), number_style)
        
        if ravitaillement.consommation_moyenne > 0:
            ws.write(row_num, 8, float(ravitaillement.consommation_moyenne), number_style)
        else:
            ws.write(row_num, 8, 'N/A')
        
        row_num += 1
    
    # Ajouter une ligne de total
    row_num += 1
    ws.write(row_num, 0, 'TOTAL', xlwt.easyxf('font: bold on'))
    ws.write(row_num, 5, float(total_litres), xlwt.easyxf('font: bold on; align: horiz right'))
    ws.write(row_num, 7, float(total_cout), xlwt.easyxf('font: bold on; align: horiz right'))
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Export Excel du suivi de la consommation de carburant",
    )
    
    # Préparer la réponse
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="Suivi Carburant - Département : {request.user.departement.nom if not request.user.is_superuser else "Tous"}.xls"'
    
    # Sauvegarder le classeur dans la réponse
    wb.save(response)
    
    return response
