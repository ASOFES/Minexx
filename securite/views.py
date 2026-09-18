from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, OuterRef, Subquery
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
# from weasyprint import HTML  # Temporairement commenté pour le déploiement, CSS
from django.template.loader import get_template, render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from datetime import datetime
import io
import os
import base64
# import pandas as pd  # Temporairement commenté pour le déploiement
from django.templatetags.static import static
import re
import tempfile, os
import openpyxl
from openpyxl.styles import Font

from core.models import Vehicule, ActionTraceur, HistoriqueKilometrage, Utilisateur
# Le décorateur securite_required est utilisé via le décorateur login_required avec des vérifications supplémentaires dans les vues
from .models import CheckListSecurite, IncidentSecurite
from .forms import ChecklistSecuriteForm, IncidentSecuriteForm
from core.models import HistoriqueCorrectionKilometrage

# Tentative d'importation de xhtml2pdf pour la génération de PDF
try:
    # from xhtml2pdf import pisa  # Temporairement commenté pour le déploiement
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False

@login_required
def dashboard(request):
    """Tableau de bord pour le personnel de sécurité"""
    # Vérifier que l'utilisateur est bien un agent de sécurité, un admin ou un superuser
    if request.user.role != 'securite' and request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('home')
    
    # Récupérer tous les véhicules pour le filtre
    vehicules = Vehicule.objects.all().order_by('immatriculation')
    
    # Filtres
    statut_filter = request.GET.get('statut')
    vehicule_filter = request.GET.get('vehicule')
    date_debut_filter = request.GET.get('date_debut')
    lieu_controle_filter = request.GET.get('lieu_controle')
    
    # Construire la requête de base
    checklists_query = CheckListSecurite.objects.all().order_by('-date_controle')
    
    # Appliquer les filtres
    if statut_filter:
        checklists_query = checklists_query.filter(statut=statut_filter)
    
    if vehicule_filter:
        checklists_query = checklists_query.filter(vehicule_id=vehicule_filter)
    
    if lieu_controle_filter:
        checklists_query = checklists_query.filter(lieu_controle__icontains=lieu_controle_filter)
    
    if date_debut_filter:
        try:
            date_debut = datetime.strptime(date_debut_filter, '%Y-%m-%d')
            checklists_query = checklists_query.filter(date_controle__date__gte=date_debut)
        except ValueError:
            pass
    
    # Paginer les résultats
    paginator = Paginator(checklists_query, 12)  # 12 checklists par page
    page_number = request.GET.get('page')
    checklists = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': CheckListSecurite.objects.count(),
        'conformes': CheckListSecurite.objects.filter(statut='conforme').count(),
        'anomalies_mineures': CheckListSecurite.objects.filter(statut='anomalie_mineure').count(),
        'non_conformes': CheckListSecurite.objects.filter(statut='non_conforme').count(),
    }

    # Statistiques des incidents
    incident_stats = {
        'total_incidents': IncidentSecurite.objects.count(),
        'open_incidents': IncidentSecurite.objects.filter(statut='ouvert').count(),
        'traite_incidents': IncidentSecurite.objects.filter(statut='traite').count(),
        'clos_incidents': IncidentSecurite.objects.filter(statut='clos').count(),
    }

    # Calcul du taux de conformité
    total_checklists = stats['total']
    conformes_count = stats['conformes']
    taux_conformite = (conformes_count / total_checklists * 100) if total_checklists > 0 else 0
    taux_anomalies_mineures = (stats['anomalies_mineures'] / total_checklists * 100) if total_checklists > 0 else 0
    taux_non_conformes = (stats['non_conformes'] / total_checklists * 100) if total_checklists > 0 else 0

    incidents_recents = IncidentSecurite.objects.order_by('-date_signalement')[:5]
    # Uniquement la DERNIÈRE checklist compte (une nouvelle conforme débloque le véhicule)
    latest_checklist = CheckListSecurite.objects.filter(
        vehicule=OuterRef('pk')
    ).order_by('-date_controle')
    vehicules_bloques = Vehicule.objects.annotate(
        last_checklist_statut=Subquery(latest_checklist.values('statut')[:1])
    ).filter(
        Q(last_checklist_statut='non_conforme') |
        Q(incidents_securite__statut='ouvert')
    ).distinct()
    
    context = {
        'checklists': checklists,
        'vehicules': vehicules,
        'stats': stats,
        'incidents_recents': incidents_recents,
        'vehicules_bloques': vehicules_bloques,
        'incident_stats': incident_stats,
        'taux_conformite': taux_conformite,
        'taux_anomalies_mineures': taux_anomalies_mineures,
        'taux_non_conformes': taux_non_conformes,
    }
    
    return render(request, 'securite/dashboard_simple.html', context)

@login_required
def nouvelle_checklist(request):
    """Créer une nouvelle checklist de sécurité avec contrôle d'ordre avant/après course"""
    if request.user.role != 'securite' and request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('home')

    vehicules = Vehicule.objects.all().order_by('immatriculation')
    vehicule_id = request.POST.get('vehicule') or request.GET.get('vehicule')
    
    if request.method == 'POST':
        form = ChecklistSecuriteForm(request.POST, user=request.user)
        if form.is_valid():
            checklist = form.save(commit=False)
            checklist.controleur = request.user
            # Valider avant save (empêche km inférieur au centralisé)
            try:
                checklist.full_clean()
            except Exception as e:
                messages.error(request, str(e))
                return render(request, 'securite/nouvelle_checklist_simple.html', {
                    'form': form,
                    'vehicules': vehicules,
                    'vehicule_id': vehicule_id,
                })
            checklist.save()

            # La checklist ne peut plus faire reculer le km ; correction via procédure dédiée uniquement
            if (
                checklist.kilometrage is not None
                and checklist.vehicule.kilometrage_actuel is not None
                and checklist.kilometrage < checklist.vehicule.kilometrage_actuel
            ):
                messages.warning(
                    request,
                    "Le kilométrage saisi est inférieur au kilométrage centralisé. "
                    "Utilisez la procédure de correction de kilométrage dédiée."
                )
            elif checklist.kilometrage is not None and (
                checklist.vehicule.kilometrage_actuel is None
                or checklist.kilometrage > checklist.vehicule.kilometrage_actuel
            ):
                messages.info(
                    request,
                    f"Le kilométrage du véhicule {checklist.vehicule.immatriculation} "
                    f"a été mis à jour à {checklist.vehicule.kilometrage_actuel} km."
                )

            if checklist.statut == 'conforme':
                messages.success(request, f'Check-list créée avec succès. Le véhicule {checklist.vehicule.immatriculation} est conforme.')
            elif checklist.statut == 'anomalie_mineure':
                messages.warning(request, f'Check-list créée avec succès. Le véhicule {checklist.vehicule.immatriculation} présente des anomalies mineures.')
            else:
                messages.error(request, f'Check-list créée avec succès. Le véhicule {checklist.vehicule.immatriculation} n\'est pas conforme et ne peut pas être utilisé.')
            return redirect('securite:detail_checklist', checklist.id)
    else:
        form = ChecklistSecuriteForm(user=request.user)

    context = {
        'form': form,
        'vehicules': vehicules,
        'vehicule_id': vehicule_id,
    }
    return render(request, 'securite/nouvelle_checklist_simple.html', context)

@login_required
def detail_checklist(request, checklist_id):
    """Afficher les détails d'une checklist de sécurité"""
    # Vérifier que l'utilisateur est bien un agent de sécurité, un admin ou un superuser
    if request.user.role != 'securite' and request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('home')
    
    checklist = get_object_or_404(CheckListSecurite, id=checklist_id)
    
    # Récupérer l'historique des actions liées à ce véhicule
    historique = ActionTraceur.objects.filter(
        Q(action__icontains=f"check-list") & Q(action__icontains=checklist.vehicule.immatriculation)
    ).order_by('-date_action')[:10]  # Limiter aux 10 dernières actions
    
    comparaison = None
    if checklist.type_check == 'retour':
        checklist_depart = CheckListSecurite.objects.filter(
            vehicule=checklist.vehicule,
            type_check='depart',
            date_controle__lt=checklist.date_controle
        ).order_by('-date_controle').first()
        if checklist_depart:
            comparaison = {}
            comparaison['distance'] = checklist.kilometrage - checklist_depart.kilometrage
            comparaison['changements'] = []
            champs = [
                'phares_avant', 'phares_arriere', 'clignotants', 'etat_pneus', 'carrosserie',
                'tableau_bord', 'freins', 'ceintures', 'proprete', 'carte_grise', 'assurance', 'triangle'
            ]
            for champ in champs:
                val_depart = getattr(checklist_depart, champ)
                val_retour = getattr(checklist, champ)
                if val_depart != val_retour:
                    comparaison['changements'].append({
                        'element': champ,
                        'avant': val_depart,
                        'apres': val_retour
                    })
    
    context = {
        'checklist': checklist,
        'historique': historique,
        'comparaison': comparaison,
    }
    
    return render(request, 'securite/detail_checklist_simple.html', context)

def link_callback(uri, rel):
    """Convertit les URI en chemins absolus pour xhtml2pdf"""
    
    # Utiliser le chemin absolu du projet
    sUrl = settings.STATIC_URL        # Typiquement /static/
    sRoot = settings.STATIC_ROOT      # Typiquement /home/userx/project/static/
    mUrl = settings.MEDIA_URL         # Typiquement /media/
    mRoot = settings.MEDIA_ROOT       # Typiquement /home/userx/project/media/

    # Convertir l'URI en chemin de fichier
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri  # Gérer les URI externes

    # Vérifier si le fichier existe
    if not os.path.isfile(path):
        raise Exception(f'Le fichier {path} n\'existe pas')
        
    return path

@login_required
def pdf_checklist(request, checklist_id):
    """Générer un PDF de la checklist de sécurité"""
    # Vérifier que l'utilisateur est bien un agent de sécurité, un admin ou un superuser
    if request.user.role != 'securite' and request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('home')
    
    if not PDF_ENABLED:
        messages.error(request, "La génération de PDF n'est pas disponible. Veuillez installer xhtml2pdf.")
        return redirect('securite:detail_checklist', checklist_id)
    
    checklist = get_object_or_404(CheckListSecurite, id=checklist_id)
    
    # Préparer le contexte pour le template
    context = {
        'checklist': checklist,
        'date_generation': timezone.now(),
        'MEDIA_URL': settings.MEDIA_URL,  # Ajouter l'URL des médias au contexte
    }
    
    # Charger le template
    template = get_template('securite/pdf_checklist.html')
    html = template.render(context)
    
    # Créer une réponse HTTP avec le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="checklist_{checklist_id}.pdf"'
    
    # Générer le PDF avec le gestionnaire de liens personnalisé
    pdf_status = pisa.CreatePDF(
        io.BytesIO(html.encode("UTF-8")),
        dest=response,
        link_callback=link_callback
    )
    
    if pdf_status.err:
        messages.error(request, "Une erreur est survenue lors de la génération du PDF.")
        return redirect('securite:detail_checklist', checklist_id)
    
    return response

@login_required
def signaler_incident(request):
    if request.user.role != 'securite' and request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('home')
    if request.method == 'POST':
        form = IncidentSecuriteForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.agent = request.user
            incident.save()
            messages.success(request, "Incident signalé avec succès.")
            # Notifier les admins/dispatchers ici si besoin
            return redirect('securite:dashboard')
    else:
        form = IncidentSecuriteForm()
    return render(request, 'securite/signalement_incident.html', {'form': form})

@login_required
def export_checklists_excel(request):
    checklists = CheckListSecurite.objects.all()
    if not request.user.is_superuser:
        checklists = checklists.filter(vehicule__etablissement=request.user.etablissement)
    data = []
    for c in checklists:
        distance = ''
        changements_str = 'Non applicable'  # Valeur par défaut
        if c.type_check == 'retour':
            checklist_depart = CheckListSecurite.objects.filter(
                vehicule=c.vehicule,
                type_check='depart',
                date_controle__lt=c.date_controle
            ).order_by('-date_controle').first()
            if checklist_depart:
                distance = c.kilometrage - checklist_depart.kilometrage
                # Ajouter les changements spécifiques
                champs_a_comparer = [
                    'phares_avant', 'phares_arriere', 'clignotants', 'etat_pneus', 'carrosserie',
                    'tableau_bord', 'freins', 'ceintures', 'proprete', 'carte_grise', 'assurance', 'triangle'
                ]
                changements_list = []
                for champ in champs_a_comparer:
                    val_depart = getattr(checklist_depart, champ)
                    val_retour = getattr(c, champ)
                    if val_depart != val_retour:
                        changements_list.append(f"{champ.replace('_', ' ').capitalize()}: {val_depart} -> {val_retour}")
                changements_str = "; ".join(changements_list) if changements_list else "Aucun changement"
            else:
                changements_str = "Pas de checklist de départ correspondante"
        data.append({
            'ID': c.id,
            'Date': c.date_controle.strftime('%d/%m/%Y %H:%M'),
            'Véhicule': c.vehicule.immatriculation,
            'Contrôleur': c.controleur.get_full_name(),
            'Type de Check': c.get_type_check_display(),
            'Lieu de Contrôle': c.lieu_controle,
            'Statut': c.get_statut_display(),
            'Kilométrage': c.kilometrage,
            'Phares avant': c.get_phares_avant_display(),
            'Phares arrière': c.get_phares_arriere_display(),
            'Clignotants': c.get_clignotants_display(),
            'État Pneus': c.get_etat_pneus_display(),
            'Carrosserie': c.get_carrosserie_display(),
            'Tableau de Bord': c.get_tableau_bord_display(),
            'Freins': c.get_freins_display(),
            'Ceintures': c.get_ceintures_display(),
            'Propreté': c.get_proprete_display(),
            'Carte Grise': c.get_carte_grise_display(),
            'Assurance': c.get_assurance_display(),
            'Triangle': c.get_triangle_display(),
            'Distance parcourue (Retour)': distance,
            'Changements (Retour)': changements_str,
            'Commentaires': c.commentaires or '',
        })
    # Temporairement désactivé pour le déploiement - pandas en cours de configuration
    return HttpResponse(
        "Export Excel temporairement indisponible - pandas en cours de configuration",
        content_type='text/plain'
    )

@login_required
def export_checklists_pdf(request):
    checklists = CheckListSecurite.objects.all()
    if not request.user.is_superuser:
        if hasattr(request.user, 'etablissement') and request.user.etablissement:
            checklists = checklists.filter(vehicule__etablissement=request.user.etablissement)
        else:
            messages.error(request, "Votre compte n'est pas associé à un établissement. Veuillez contacter l'administrateur.")
            return HttpResponse("Erreur: Votre compte n'est pas associé à un établissement.", status=403)

    data_for_pdf = []
    for c in checklists:
        distance = ''
        changements_str = ''
        if c.type_check == 'retour':
            checklist_depart = CheckListSecurite.objects.filter(
                vehicule=c.vehicule,
                type_check='depart',
                date_controle__lt=c.date_controle
            ).order_by('-date_controle').first()
            if checklist_depart:
                distance = c.kilometrage - checklist_depart.kilometrage
                champs_a_comparer = [
                    'phares_avant', 'phares_arriere', 'clignotants', 'etat_pneus', 'carrosserie',
                    'tableau_bord', 'freins', 'ceintures', 'proprete', 'carte_grise', 'assurance', 'triangle'
                ]
                changements_list = []
                for champ in champs_a_comparer:
                    val_depart = getattr(checklist_depart, champ)
                    val_retour = getattr(c, champ)
                    if val_depart != val_retour:
                        changements_list.append(f"{champ.replace('_', ' ').capitalize()}: {val_depart} -> {val_retour}")
                changements_str = "; ".join(changements_list) if changements_list else "Aucun changement"
            else:
                changements_str = "Pas de checklist de départ correspondante"

        data_for_pdf.append({
            'id': c.id,
            'date_controle': c.date_controle,
            'vehicule': c.vehicule.immatriculation,
            'controleur': c.controleur.get_full_name(),
            'type_check': c.get_type_check_display(),
            'lieu_controle': c.lieu_controle,
            'statut': c.get_statut_display(),
            'kilometrage': c.kilometrage,
            'phares_avant': c.get_phares_avant_display(),
            'phares_arriere': c.get_phares_arriere_display(),
            'clignotants': c.get_clignotants_display(),
            'etat_pneus': c.get_etat_pneus_display(),
            'carrosserie': c.get_carrosserie_display(),
            'tableau_bord': c.get_tableau_bord_display(),
            'freins': c.get_freins_display(),
            'ceintures': c.get_ceintures_display(),
            'proprete': c.get_proprete_display(),
            'carte_grise': c.get_carte_grise_display(),
            'assurance': c.get_assurance_display(),
            'triangle': c.get_triangle_display(),
            'distance_parcourue': distance,
            'changements': changements_str,
            'commentaires': c.commentaires or '',
        })
    
    titre_etablissement = request.user.etablissement.nom if not request.user.is_superuser and hasattr(request.user, 'etablissement') and request.user.etablissement else 'Tous'
    titre = f"Checklists Sécurité - Établissement : {titre_etablissement}"

    # Générer l'URI du logo
    logo_path = finders.find('images/logo_minexx.png')
    logo_data_uri = ''
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as image_file:
            logo_data_uri = "data:image/png;base64," + base64.b64encode(image_file.read()).decode('utf-8')
    
    # Rendu du template HTML
    html_string = render_to_string('securite/export_checklists_pdf.html', {
        'checklists': data_for_pdf,
        'request': request,
        'titre': titre,
        'now': timezone.now(),
        'logo_data_uri': logo_data_uri,
        'static_url': settings.STATIC_URL
    })
    
    # Création du PDF avec WeasyPrint
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    
    # Définition des styles CSS
    styles = [
        CSS(string='''
            @page {
                size: A4;
                margin: 1.5cm;
            }
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .checklist-container {
                page-break-inside: avoid;
                margin-bottom: 20px;
            }
            .checklist-header {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                margin-bottom: 15px;
                border-radius: 4px;
            }
            .checklist-details {
                width: 100%;
                margin-bottom: 15px;
            }
            .detail-row {
                display: flex;
                margin-bottom: 8px;
                page-break-inside: avoid;
            }
            .detail-item {
                width: 50%;
                margin-bottom: 8px;
                box-sizing: border-box;
                padding: 0 5px;
            }
            .detail-label {
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 2px;
                font-size: 9pt;
            }
            .detail-value {
                padding: 5px;
                background-color: #f8f9fa;
                border-radius: 4px;
                min-height: 20px;
                font-size: 9pt;
            }
            .status-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 8pt;
                font-weight: 600;
            }
            .status-ok {
                background-color: #d4edda;
                color: #155724;
            }
            .status-nok {
                background-color: #f8d7da;
                color: #721c24;
            }
        ''')
    ]
    
    # Génération du PDF
    pdf_bytes = html.write_pdf(stylesheets=styles)
    
    # Création de la réponse HTTP
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{titre.replace(" ", "_")}.pdf"'
    return response

@login_required
def corriger_kilometrage(request):
    # Restriction d'accès
    if not (request.user.is_superuser or getattr(request.user, 'role', '').lower().replace('é', 'e') in ['securite', 'admin']):
        messages.error(request, "Vous n'avez pas les droits pour accéder à cette page.")
        return redirect('home')

    from core.models import HistoriqueKilometrage  # Import unique pour toute la fonction
    vehicules = Vehicule.objects.all().order_by('immatriculation')
    selected_vehicule = None
    kilometrage_actuel = None
    if request.method == 'POST':
        vehicule_id = request.POST.get('vehicule')
        nouveau_km = request.POST.get('nouveau_kilometrage')
        try:
            selected_vehicule = Vehicule.objects.get(id=vehicule_id)
            kilometrage_actuel = selected_vehicule.kilometrage_actuel
            if nouveau_km is not None and nouveau_km != '':
                nouveau_km_int = int(nouveau_km)
                # Stocker l'ancien kilométrage AVANT modification
                ancien_km = selected_vehicule.kilometrage_actuel
                selected_vehicule.kilometrage_actuel = nouveau_km_int
                selected_vehicule.save(update_fields=["kilometrage_actuel"])
                # Correction sur toutes les checklists liées
                CheckListSecurite.objects.filter(vehicule=selected_vehicule).update(kilometrage=nouveau_km_int)
                # Correction sur tous les entretiens liés
                from entretien.models import Entretien
                Entretien.objects.filter(vehicule=selected_vehicule).update(kilometrage=nouveau_km_int)
                # Correction sur tous les ravitaillements liés
                from ravitaillement.models import Ravitaillement
                Ravitaillement.objects.filter(vehicule=selected_vehicule).update(kilometrage_avant=nouveau_km_int)
                Ravitaillement.objects.filter(vehicule=selected_vehicule).update(kilometrage_apres=nouveau_km_int)
                # Correction sur l'historique kilométrage
                HistoriqueKilometrage.objects.filter(vehicule=selected_vehicule).update(valeur_apres=nouveau_km_int)
                # Correction sur l'historique des actions (ActionTraceur.details)
                actions = ActionTraceur.objects.filter(action__icontains=selected_vehicule.immatriculation, details__icontains='Kilométrage:')
                for action in actions:
                    action.details = re.sub(r'(Kilométrage: )\d+', f'Kilométrage: {nouveau_km_int}', action.details)
                    action.save(update_fields=["details"])
                # Correction collective sur toutes les missions (Course) du véhicule
                from core.models import Course, HistoriqueKilometrage
                courses = Course.objects.filter(vehicule=selected_vehicule)
                for course in courses:
                    old_depart = course.kilometrage_depart
                    old_fin = course.kilometrage_fin
                    course.kilometrage_depart = nouveau_km_int
                    course.kilometrage_fin = nouveau_km_int
                    course.save(update_fields=["kilometrage_depart", "kilometrage_fin"])
                    # Historique de la modification
                    if old_depart != nouveau_km_int:
                        HistoriqueKilometrage.objects.create(
                            vehicule=selected_vehicule,
                            utilisateur=request.user,
                            module='course',
                            objet_id=course.pk,
                            valeur_avant=old_depart,
                            valeur_apres=nouveau_km_int,
                            commentaire=f"Correction collective du kilometrage_depart via admin sécurité"
                        )
                    if old_fin != nouveau_km_int:
                        HistoriqueKilometrage.objects.create(
                            vehicule=selected_vehicule,
                            utilisateur=request.user,
                            module='course',
                            objet_id=course.pk,
                            valeur_avant=old_fin,
                            valeur_apres=nouveau_km_int,
                            commentaire=f"Correction collective du kilometrage_fin via admin sécurité"
                        )
                # Correction collective sur tous les entretiens du véhicule
                from entretien.models import Entretien
                entretiens = Entretien.objects.filter(vehicule=selected_vehicule)
                for entretien in entretiens:
                    old_km = entretien.kilometrage
                    old_km_apres = entretien.kilometrage_apres
                    entretien.kilometrage = nouveau_km_int
                    entretien.kilometrage_apres = nouveau_km_int
                    entretien.save(update_fields=["kilometrage", "kilometrage_apres"])
                    # Historique de la modification
                    if old_km != nouveau_km_int:
                        HistoriqueKilometrage.objects.create(
                            vehicule=selected_vehicule,
                            utilisateur=request.user,
                            module='entretien',
                            objet_id=entretien.pk,
                            valeur_avant=old_km,
                            valeur_apres=nouveau_km_int,
                            commentaire=f"Correction collective du kilometrage via admin sécurité"
                        )
                    if old_km_apres != nouveau_km_int:
                        HistoriqueKilometrage.objects.create(
                            vehicule=selected_vehicule,
                            utilisateur=request.user,
                            module='entretien',
                            objet_id=entretien.pk,
                            valeur_avant=old_km_apres,
                            valeur_apres=nouveau_km_int,
                            commentaire=f"Correction collective du kilometrage_apres via admin sécurité"
                        )
                # Correction collective sur tous les ravitaillements du véhicule (seulement kilometrage_apres)
                from ravitaillement.models import Ravitaillement
                ravitaillements = Ravitaillement.objects.filter(vehicule=selected_vehicule)
                for ravitaillement in ravitaillements:
                    old_km_apres = ravitaillement.kilometrage_apres
                    ravitaillement.kilometrage_apres = nouveau_km_int
                    ravitaillement.save(update_fields=["kilometrage_apres"])
                    # Historique de la modification
                    if old_km_apres != nouveau_km_int:
                        HistoriqueKilometrage.objects.create(
                            vehicule=selected_vehicule,
                            utilisateur=request.user,
                            module='ravitaillement',
                            objet_id=ravitaillement.pk,
                            valeur_avant=old_km_apres,
                            valeur_apres=nouveau_km_int,
                            commentaire=f"Correction collective du kilometrage_apres via admin sécurité"
                        )
                # Avant la correction, stocker l'ancien kilométrage
                # ancien_km = selected_vehicule.kilometrage_actuel # This line is removed as it's now defined above
                # Après la correction, enregistrer dans l'historique de correction
                # (ancien_km est bien l'ancienne valeur, nouveau_km_int la nouvelle)
                motif = request.POST.get('motif', '').strip()
                if not motif:
                    messages.error(request, "Le motif de la correction est obligatoire.")
                    return redirect(request.path)
                chauffeur = None
                if 'chauffeur_id' in request.POST:
                    try:
                        chauffeur = Utilisateur.objects.get(id=request.POST['chauffeur_id'])
                    except Utilisateur.DoesNotExist:
                        chauffeur = None
                HistoriqueCorrectionKilometrage.objects.create(
                    vehicule=selected_vehicule,
                    chauffeur=chauffeur,
                    valeur_avant=ancien_km,
                    valeur_apres=nouveau_km_int,
                    motif=motif,
                    auteur=request.user
                )
                messages.success(request, f"Kilométrage du véhicule {selected_vehicule.immatriculation} corrigé à {nouveau_km} km partout (missions, entretiens et ravitaillements inclus - seul kilometrage_apres modifié pour ravitaillements).")
        except Vehicule.DoesNotExist:
            messages.error(request, "Véhicule introuvable.")
    elif request.method == 'GET' and request.GET.get('vehicule'):
        vehicule_id = request.GET.get('vehicule')
        try:
            selected_vehicule = Vehicule.objects.get(id=vehicule_id)
            kilometrage_actuel = selected_vehicule.kilometrage_actuel
        except Vehicule.DoesNotExist:
            selected_vehicule = None
            kilometrage_actuel = None
    context = {
        'vehicules': vehicules,
        'selected_vehicule': selected_vehicule,
        'kilometrage_actuel': kilometrage_actuel,
    }
    return render(request, 'securite/corriger_kilometrage.html', context)

def get_kilometrage_vehicule(request):
    vehicule_id = request.GET.get('vehicule_id')
    if not vehicule_id:
        return JsonResponse({'success': False, 'error': 'Aucun véhicule spécifié.'})
    try:
        vehicule = Vehicule.objects.get(id=vehicule_id)
        return JsonResponse({'success': True, 'kilometrage_actuel': vehicule.kilometrage_actuel})
    except Vehicule.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Véhicule introuvable.'})

@login_required
def historique_corrections_km(request):
    vehicule_id = request.GET.get('vehicule')
    chauffeur_id = request.GET.get('chauffeur')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    corrections = HistoriqueCorrectionKilometrage.objects.all().select_related('vehicule', 'chauffeur', 'auteur')
    if vehicule_id:
        corrections = corrections.filter(vehicule_id=vehicule_id)
    if chauffeur_id:
        corrections = corrections.filter(chauffeur_id=chauffeur_id)
    if date_debut:
        corrections = corrections.filter(date_correction__date__gte=date_debut)
    if date_fin:
        corrections = corrections.filter(date_correction__date__lte=date_fin)
    corrections = corrections.order_by('-date_correction')
    # Pagination
    paginator = Paginator(corrections, 30)
    page = request.GET.get('page')
    corrections_page = paginator.get_page(page)
    vehicules = Vehicule.objects.all()
    chauffeurs = Utilisateur.objects.filter(role='chauffeur')
    return render(request, 'securite/historique_corrections_km.html', {
        'corrections': corrections_page,
        'vehicules': vehicules,
        'chauffeurs': chauffeurs,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'vehicule_id': vehicule_id,
        'chauffeur_id': chauffeur_id,
    })

@login_required
def historique_corrections_km_pdf(request):
    vehicule_id = request.GET.get('vehicule')
    chauffeur_id = request.GET.get('chauffeur')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    corrections = HistoriqueCorrectionKilometrage.objects.all().select_related('vehicule', 'chauffeur', 'auteur')
    if vehicule_id and vehicule_id not in ('', 'None'):
        corrections = corrections.filter(vehicule_id=vehicule_id)
    if chauffeur_id and chauffeur_id not in ('', 'None'):
        corrections = corrections.filter(chauffeur_id=chauffeur_id)
    if date_debut and date_debut not in ('', 'None'):
        corrections = corrections.filter(date_correction__date__gte=date_debut)
    if date_fin and date_fin not in ('', 'None'):
        corrections = corrections.filter(date_correction__date__lte=date_fin)
    corrections = corrections.order_by('-date_correction')
    context = {
        'corrections': corrections,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    template = get_template('securite/historique_corrections_km_pdf.html')
    html = template.render(context)
    fd, path = tempfile.mkstemp(suffix=".pdf")
    try:
        HTML(string=html).write_pdf(path)
        with open(path, "rb") as f:
            pdf = f.read()
    finally:
        os.close(fd)
        os.remove(path)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=historique_corrections_km.pdf'
    return response

@login_required
def historique_corrections_km_excel(request):
    vehicule_id = request.GET.get('vehicule')
    chauffeur_id = request.GET.get('chauffeur')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    corrections = HistoriqueCorrectionKilometrage.objects.all().select_related('vehicule', 'chauffeur', 'auteur')
    if vehicule_id and vehicule_id not in ('', 'None'):
        corrections = corrections.filter(vehicule_id=vehicule_id)
    if chauffeur_id and chauffeur_id not in ('', 'None'):
        corrections = corrections.filter(chauffeur_id=chauffeur_id)
    if date_debut and date_debut not in ('', 'None'):
        corrections = corrections.filter(date_correction__date__gte=date_debut)
    if date_fin and date_fin not in ('', 'None'):
        corrections = corrections.filter(date_correction__date__lte=date_fin)
    corrections = corrections.order_by('-date_correction')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Corrections KM"
    ws.append(["Date", "Véhicule", "Chauffeur", "Valeur avant", "Valeur après", "Motif", "Auteur"])
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for corr in corrections:
        ws.append([
            corr.date_correction.strftime('%d/%m/%Y %H:%M'),
            corr.vehicule.immatriculation,
            corr.chauffeur.get_full_name() if corr.chauffeur else 'Non renseigné',
            corr.valeur_avant,
            corr.valeur_apres,
            corr.motif or 'Aucun',
            corr.auteur.get_full_name() if corr.auteur else 'Non renseigné',
        ])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=historique_corrections_km.xlsx'
    wb.save(response)
    return response
