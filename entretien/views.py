from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from core.models import Vehicule, ActionTraceur, Course
from .models import Entretien, ReparationMecanique
from .forms import EntretienForm, ReparationMecaniqueForm, ConfirmerReparationForm
from core.utils import render_to_pdf, export_to_excel
from core.decorators import is_admin_or_dispatch_or_superuser
from ravitaillement.models import Ravitaillement

# Fonction pour vérifier si l'utilisateur est admin ou superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)


def recalculer_kilometrage_dernier_entretien(vehicule):
    """Recalcule kilometrage_dernier_entretien depuis le dernier entretien terminé."""
    dernier = (
        Entretien.objects.filter(vehicule=vehicule, statut='termine')
        .order_by('-date_entretien', '-id')
        .first()
    )
    if dernier:
        km = dernier.kilometrage_apres if dernier.kilometrage_apres is not None else dernier.kilometrage
        vehicule.kilometrage_dernier_entretien = km or 0
    else:
        vehicule.kilometrage_dernier_entretien = 0
    vehicule.save(update_fields=['kilometrage_dernier_entretien'])
    return vehicule.kilometrage_dernier_entretien

def _get_latest_kilometrage_for_vehicule(vehicule, exclude_entretien_id=None):
    dernier_kilometrage = 0

    # Vérifier le dernier ravitaillement
    dernier_ravitaillement = Ravitaillement.objects.filter(
        vehicule=vehicule
    ).order_by('-date_ravitaillement').first()
    if dernier_ravitaillement and dernier_ravitaillement.kilometrage_apres is not None and dernier_ravitaillement.kilometrage_apres > dernier_kilometrage:
        dernier_kilometrage = dernier_ravitaillement.kilometrage_apres

    # Vérifier la dernière course terminée
    derniere_course = Course.objects.filter(
        vehicule=vehicule,
        statut='terminee'
    ).order_by('-date_fin').first()
    if derniere_course and derniere_course.kilometrage_fin is not None and derniere_course.kilometrage_fin > dernier_kilometrage:
        dernier_kilometrage = derniere_course.kilometrage_fin

    # Vérifier le dernier entretien
    entretien_query = Entretien.objects.filter(
        vehicule=vehicule,
        kilometrage_apres__isnull=False
    )
    if exclude_entretien_id:
        entretien_query = entretien_query.exclude(id=exclude_entretien_id)
    
    dernier_entretien = entretien_query.order_by('-date_entretien').first()
    if dernier_entretien and dernier_entretien.kilometrage_apres is not None and dernier_entretien.kilometrage_apres > dernier_kilometrage:
        dernier_kilometrage = dernier_entretien.kilometrage_apres
    elif dernier_entretien and dernier_entretien.kilometrage is not None and dernier_entretien.kilometrage > dernier_kilometrage: # Fallback to kilometrage if kilometrage_apres is null or less
        dernier_kilometrage = dernier_entretien.kilometrage

    # Fallback to vehicule's own kilometrage if nothing else found
    if dernier_kilometrage == 0:
        dernier_kilometrage = vehicule.kilometrage_dernier_entretien or vehicule.kilometrage_actuel or 0

    return dernier_kilometrage

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def dashboard(request):
    """Vue pour le tableau de bord du module Entretien"""
    entretiens_qs = Entretien.objects.all()
    reparations_qs = ReparationMecanique.objects.all()
    if not request.user.is_superuser and getattr(request.user, 'etablissement', None):
        etab = request.user.etablissement
        entretiens_qs = entretiens_qs.filter(vehicule__etablissement=etab)
        reparations_qs = reparations_qs.filter(vehicule__etablissement=etab)

    entretiens_count = entretiens_qs.count()
    entretiens_recents = entretiens_qs.order_by('-date_creation')[:5]
    reparations_ouvertes = reparations_qs.filter(statut__in=['en_attente', 'en_cours']).count()
    reparations_attente = reparations_qs.filter(statut='en_attente').count()
    reparations_recentes = reparations_qs.order_by('-date_creation')[:5]

    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation du tableau de bord Entretien",
    )

    context = {
        'entretiens_count': entretiens_count,
        'entretiens_recents': entretiens_recents,
        'reparations_ouvertes': reparations_ouvertes,
        'reparations_attente': reparations_attente,
        'reparations_recentes': reparations_recentes,
    }

    return render(request, 'entretien/dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def liste_entretiens(request):
    """Vue pour afficher la liste des entretiens"""
    # Initialiser le queryset
    queryset = Entretien.objects.filter(vehicule__etablissement=request.user.etablissement)
    
    # Filtres
    vehicule_id = request.GET.get('vehicule')
    statut = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    recherche = request.GET.get('recherche')
    tri = request.GET.get('tri', '-date_entretien')  # Par défaut, tri par date décroissante
    
    # Appliquer les filtres
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if statut:
        queryset = queryset.filter(statut=statut)
    if date_debut:
        queryset = queryset.filter(date_entretien__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_entretien__lte=date_fin)
    if recherche:
        queryset = queryset.filter(
            Q(motif__icontains=recherche) | 
            Q(garage__icontains=recherche) |
            Q(vehicule__immatriculation__icontains=recherche) |
            Q(commentaires__icontains=recherche)
        )
    
    # Ordonner les résultats selon le critère de tri
    entretiens_list = queryset.order_by(tri)
    
    # Pagination - 5 entretiens par page
    paginator = Paginator(entretiens_list, 12)  # 12 entretiens par page
    page = request.GET.get('page')
    
    try:
        entretiens = paginator.page(page)
    except PageNotAnInteger:
        # Si la page n'est pas un entier, afficher la première page
        entretiens = paginator.page(1)
    except EmptyPage:
        # Si la page est hors limites, afficher la dernière page
        entretiens = paginator.page(paginator.num_pages)
    
    # Récupérer tous les véhicules pour le filtre
    vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement).order_by('immatriculation')
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation de la liste des entretiens",
    )
    
    context = {
        'entretiens': entretiens,
        'vehicules': vehicules,
        'tri_actuel': tri,
    }
    
    return render(request, 'entretien/liste_entretiens.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def creer_entretien(request):
    """Vue pour créer un nouvel entretien"""
    if request.method == 'POST':
        form = EntretienForm(request.POST, request.FILES, createur=request.user)
        if form.is_valid():
            entretien = form.save(commit=False)
            entretien.etablissement = entretien.vehicule.etablissement
            
            # Vérifier que le kilométrage n'est pas inférieur au dernier kilométrage enregistré
            dernier_kilometrage = _get_latest_kilometrage_for_vehicule(entretien.vehicule)
            
            if entretien.kilometrage < dernier_kilometrage:
                messages.error(request, f"Le kilométrage ({entretien.kilometrage} km) ne peut pas être inférieur au dernier kilométrage enregistré ({dernier_kilometrage} km).")
                return render(request, 'entretien/formulaire_entretien.html', {'form': form, 'title': 'Nouvel entretien'})
            
            if entretien.kilometrage_apres and entretien.kilometrage_apres <= entretien.kilometrage:
                messages.error(request, "Le kilométrage après doit être supérieur au kilométrage avant.")
                return render(request, 'entretien/formulaire_entretien.html', {'form': form, 'title': 'Nouvel entretien'})
            
            entretien.save()
            # Seul un entretien TERMINÉ met à jour la référence de maintenance
            if entretien.statut == 'termine':
                kilometrage_a_mettre_a_jour = (
                    entretien.kilometrage_apres
                    if entretien.kilometrage_apres is not None
                    else entretien.kilometrage
                )
                if kilometrage_a_mettre_a_jour is not None:
                    entretien.vehicule.kilometrage_dernier_entretien = kilometrage_a_mettre_a_jour
                    if (
                        entretien.vehicule.kilometrage_actuel is None
                        or entretien.vehicule.kilometrage_actuel < kilometrage_a_mettre_a_jour
                    ):
                        entretien.vehicule.kilometrage_actuel = kilometrage_a_mettre_a_jour
                    entretien.vehicule.save(
                        update_fields=["kilometrage_dernier_entretien", "kilometrage_actuel"]
                    )
            messages.success(request, 'Entretien enregistré avec succès.')
            return redirect('entretien:detail_entretien', entretien.id)
    else:
        vehicule_id = request.GET.get('vehicule')
        initial = {}
        if vehicule_id:
            try:
                vehicule = Vehicule.objects.get(id=vehicule_id)
                # Utiliser la fonction d'aide pour le kilométrage initial
                kilometrage = _get_latest_kilometrage_for_vehicule(vehicule)
                initial = {'vehicule': vehicule.id, 'kilometrage': kilometrage}
            except Exception:
                pass
        form = EntretienForm(createur=request.user, initial=initial)
    
    return render(request, 'entretien/formulaire_entretien.html', {
        'form': form,
        'title': 'Nouvel entretien'
    })

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def detail_entretien(request, entretien_id):
    """Vue pour afficher les détails d'un entretien"""
    # Récupération de l'entretien avec les relations nécessaires
    entretien = get_object_or_404(
        Entretien.objects.select_related(
            'vehicule',
            'vehicule__etablissement',
            'createur'
        ), 
        pk=entretien_id
    )
    
    # Vérification que le véhicule existe
    if not hasattr(entretien, 'vehicule') or not entretien.vehicule:
        messages.error(request, "Le véhicule associé à cet entretien est introuvable.")
        return redirect('entretien:liste_entretiens')
    
    # Debug: Vérifier les attributs du véhicule
    print(f"Véhicule ID: {entretien.vehicule.id}")
    print(f"Immatriculation: {getattr(entretien.vehicule, 'immatriculation', 'Non définie')}")
    print(f"Marque: {getattr(entretien.vehicule, 'marque', 'Non définie')}")
    print(f"Modèle: {getattr(entretien.vehicule, 'modele', 'Non défini')}")
    
    previous_entretien = Entretien.objects.filter(
        vehicule=entretien.vehicule,
        date_entretien__lt=entretien.date_entretien
    ).order_by('-date_entretien').first()

    date_ancien_entretien = "N/A"
    kilometrage_ancien_entretien = "N/A"
    kilometrage_prevu_actuel = 0
    ecart_prevu_realise = "N/A"

    if previous_entretien:
        date_ancien_entretien = previous_entretien.date_entretien.strftime('%d/%m/%Y')
        kilometrage_ancien_entretien = previous_entretien.kilometrage_apres or previous_entretien.kilometrage or 0
        
        kilometrage_prevu_actuel = (kilometrage_ancien_entretien or 0) + 4500
        
        if entretien.kilometrage is not None:
            ecart_prevu_realise = f"{(kilometrage_prevu_actuel - entretien.kilometrage):.0f} km"
        
    projection_prochain_entretien = (entretien.kilometrage_apres or entretien.kilometrage or 0) + 4500

    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Consultation des détails de l'entretien #{entretien_id}",
    )
    
    context = {
        'entretien': entretien,
        'date_ancien_entretien': date_ancien_entretien,
        'kilometrage_ancien_entretien': kilometrage_ancien_entretien,
        'kilometrage_prevu_actuel': kilometrage_prevu_actuel,
        'ecart_prevu_realise': ecart_prevu_realise,
        'projection_prochain_entretien': projection_prochain_entretien,
        'debug': False,  # Désactivation du mode debug
    }
    
    return render(request, 'entretien/detail_entretien.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def modifier_entretien(request, entretien_id):
    """Vue pour modifier un entretien existant"""
    entretien = get_object_or_404(Entretien, id=entretien_id)
    
    if request.method == 'POST':
        form = EntretienForm(request.POST, request.FILES, instance=entretien)
        if form.is_valid():
            entretien = form.save(commit=False)
            entretien.etablissement = entretien.vehicule.etablissement
            
            # Vérifier que le kilométrage n'est pas inférieur au dernier kilométrage enregistré
            dernier_kilometrage = _get_latest_kilometrage_for_vehicule(entretien.vehicule, exclude_entretien_id=entretien.id)
            
            if entretien.kilometrage < dernier_kilometrage:
                messages.error(request, f"Le kilométrage ({entretien.kilometrage} km) ne peut pas être inférieur au dernier kilométrage enregistré ({dernier_kilometrage} km).")
                return render(request, 'entretien/formulaire_entretien.html', {'form': form, 'entretien': entretien, 'title': 'Modifier entretien'})
            
            if entretien.kilometrage_apres and entretien.kilometrage_apres <= entretien.kilometrage:
                messages.error(request, "Le kilométrage après doit être supérieur au kilométrage avant.")
                return render(request, 'entretien/formulaire_entretien.html', {'form': form, 'entretien': entretien, 'title': 'Modifier entretien'})

            entretien.save()

            # Seul un entretien TERMINÉ met à jour la référence de maintenance
            if entretien.statut == 'termine':
                kilometrage_a_mettre_a_jour = (
                    entretien.kilometrage_apres
                    if entretien.kilometrage_apres is not None
                    else entretien.kilometrage
                )
                if kilometrage_a_mettre_a_jour is not None:
                    entretien.vehicule.kilometrage_dernier_entretien = kilometrage_a_mettre_a_jour
                    if (
                        entretien.vehicule.kilometrage_actuel is None
                        or entretien.vehicule.kilometrage_actuel < kilometrage_a_mettre_a_jour
                    ):
                        entretien.vehicule.kilometrage_actuel = kilometrage_a_mettre_a_jour
                    entretien.vehicule.save(
                        update_fields=["kilometrage_dernier_entretien", "kilometrage_actuel"]
                    )
            else:
                # Recalculer la référence à partir du dernier entretien terminé restant
                recalculer_kilometrage_dernier_entretien(entretien.vehicule)
            
            messages.success(request, 'Entretien modifié avec succès.')
            return redirect('entretien:detail_entretien', entretien.id)
    else:
        initial = {}
        if (not entretien.kilometrage or entretien.kilometrage == 0) and entretien.vehicule_id:
            try:
                vehicule = entretien.vehicule
                # Utiliser la fonction d'aide pour le kilométrage initial
                kilometrage = _get_latest_kilometrage_for_vehicule(vehicule)
                initial['kilometrage'] = kilometrage
            except Exception:
                pass
        form = EntretienForm(instance=entretien, initial=initial)
    
    return render(request, 'entretien/formulaire_entretien.html', {
        'form': form,
        'entretien': entretien,
        'title': 'Modifier entretien'
    })

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def supprimer_entretien(request, entretien_id):
    """Vue pour supprimer un entretien"""
    entretien = get_object_or_404(Entretien, pk=entretien_id)
    
    if request.method == 'POST':
        vehicule = entretien.vehicule
        # Tracer l'action
        ActionTraceur.objects.create(
            utilisateur=request.user,
            action=f"Suppression de l'entretien #{entretien_id}",
            details=f"Véhicule: {vehicule.immatriculation}",
        )
        
        entretien.delete()
        recalculer_kilometrage_dernier_entretien(vehicule)
        messages.success(request, "L'entretien a été supprimé avec succès.")
        return redirect('entretien:liste_entretiens')
    
    context = {
        'entretien': entretien,
    }
    
    return render(request, 'entretien/confirmer_suppression.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_entretiens_pdf(request):
    """Vue pour exporter la liste des entretiens en PDF"""
    # Filtrage par établissement
    queryset = Entretien.objects.all()
    if not request.user.is_superuser:
        # Assurez-vous que l'utilisateur a un établissement si ce n'est pas un superuser
        if hasattr(request.user, 'etablissement') and request.user.etablissement:
            queryset = queryset.filter(vehicule__etablissement=request.user.etablissement)
        else:
            # Si l'utilisateur n'est pas superuser et n'a pas d'établissement, retourner une liste vide ou un message d'erreur
            messages.error(request, "Votre compte n'est pas associé à un établissement. Veuillez contacter l'administrateur.")
            return HttpResponse("Erreur: Votre compte n'est pas associé à un établissement.", status=403)
    
    # Filtres
    vehicule_id = request.GET.get('vehicule')
    statut = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    # Appliquer les filtres
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if statut:
        queryset = queryset.filter(statut=statut)
    if date_debut:
        queryset = queryset.filter(date_entretien__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_entretien__lte=date_fin)
    
    # Préparer les données pour l'exportation
    data = []
    total_budget_consomme = 0
    for entretien in queryset:
        previous_entretien = Entretien.objects.filter(
            vehicule=entretien.vehicule,
            date_entretien__lt=entretien.date_entretien
        ).order_by('-date_entretien').first()

        date_ancien_entretien = "N/A"
        kilometrage_ancien_entretien = "N/A"
        kilometrage_prevu_actuel = 0
        ecart_prevu_realise = "N/A"

        if previous_entretien:
            date_ancien_entretien = previous_entretien.date_entretien.strftime('%d/%m/%Y')
            kilometrage_ancien_entretien = previous_entretien.kilometrage_apres or previous_entretien.kilometrage or 0
            
            # Calculate planned kilometrage for the current maintenance based on the previous one
            kilometrage_prevu_actuel = (kilometrage_ancien_entretien or 0) + 4500
            
            # Calculate deviation
            if entretien.kilometrage is not None:
                ecart_prevu_realise = f"{(kilometrage_prevu_actuel - entretien.kilometrage):.0f} km"
            
        projection_prochain_entretien = (entretien.kilometrage_apres or entretien.kilometrage or 0) + 4500

        data.append({
            'Véhicule': entretien.vehicule.immatriculation,
            'Département': entretien.vehicule.etablissement.nom if entretien.vehicule.etablissement else "-",
            'Date_Entretien_Actuel': entretien.date_entretien.strftime('%d/%m/%Y'),
            'Km_Entretien_Début': entretien.kilometrage,
            'Km_Entretien_Fin': entretien.kilometrage_apres,
            'Garage': entretien.garage or "-",
            'Motif': entretien.motif or "-",
            'Coût_': entretien.cout,
            'Statut': entretien.get_statut_display(),
            'Date_Ancien_Entretien': date_ancien_entretien,
            'Km_Ancien_Entretien': kilometrage_ancien_entretien,
            'Km_Prévu_Actuel': kilometrage_prevu_actuel,
            'Écart_Prévu_vs_Réalisé_Km': ecart_prevu_realise,
            'Projection_Prochain_Entretien_Km': projection_prochain_entretien,
        })
        if entretien.statut == 'termine' and entretien.cout is not None:
            total_budget_consomme += entretien.cout
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation PDF des entretiens",
    )
    
    # Préparer le contexte pour le template
    etablissement_nom = request.user.etablissement.nom if not request.user.is_superuser and hasattr(request.user, 'etablissement') and request.user.etablissement else 'Tous'
    
    context = {
        'title': 'Liste des Entretiens',
        'date_export': timezone.now(),
        'etablissement': etablissement_nom,
        'total_budget_consomme': total_budget_consomme,
        'data': data,
        'user': request.user
    }
    
    # Générer le PDF avec le template personnalisé
    return render_to_pdf(
        'entretien/pdf/liste_entretiens_pdf.html',
        context,
        filename="liste_entretiens.pdf"
    )

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_entretiens_excel(request):
    """Vue pour exporter la liste des entretiens en Excel"""
    queryset = Entretien.objects.all()
    if not request.user.is_superuser:
        # Assurez-vous que l'utilisateur a un établissement si ce n'est pas un superuser
        if hasattr(request.user, 'etablissement') and request.user.etablissement:
            queryset = queryset.filter(vehicule__etablissement=request.user.etablissement)
        else:
            messages.error(request, "Votre compte n'est pas associé à un établissement. Veuillez contacter l'administrateur.")
            return HttpResponse("Erreur: Votre compte n'est pas associé à un établissement.", status=403)
    
    # Filtres
    vehicule_id = request.GET.get('vehicule')
    statut = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    # Appliquer les filtres
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if statut:
        queryset = queryset.filter(statut=statut)
    if date_debut:
        queryset = queryset.filter(date_entretien__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_entretien__lte=date_fin)
    
    # Préparer les données pour l'exportation
    data = []
    total_budget_consomme = 0
    for entretien in queryset:
        previous_entretien = Entretien.objects.filter(
            vehicule=entretien.vehicule,
            date_entretien__lt=entretien.date_entretien
        ).order_by('-date_entretien').first()

        date_ancien_entretien = "N/A"
        kilometrage_ancien_entretien = "N/A"
        kilometrage_prevu_actuel = 0
        ecart_prevu_realise = "N/A"

        if previous_entretien:
            date_ancien_entretien = previous_entretien.date_entretien.strftime('%d/%m/%Y')
            kilometrage_ancien_entretien = previous_entretien.kilometrage_apres or previous_entretien.kilometrage or 0
            
            # Calculate planned kilometrage for the current maintenance based on the previous one
            kilometrage_prevu_actuel = (kilometrage_ancien_entretien or 0) + 4500
            
            # Calculate deviation
            if entretien.kilometrage is not None:
                ecart_prevu_realise = f"{(kilometrage_prevu_actuel - entretien.kilometrage):.0f} km"
            
        projection_prochain_entretien = (entretien.kilometrage_apres or entretien.kilometrage or 0) + 4500

        data.append({
            'Véhicule': entretien.vehicule.immatriculation,
            'Châssis': entretien.vehicule.numero_chassis or '',
            'Moteur': entretien.vehicule.numero_moteur or '',
            'Carte rose': entretien.vehicule.numero_carte_rose or '',
            'Km début véhicule': entretien.vehicule.kilometrage_debut if entretien.vehicule.kilometrage_debut is not None else '',
            'Pneus': entretien.vehicule.pneus_resume() or '',
            'Date Entretien Actuel': entretien.date_entretien.strftime('%d/%m/%Y'),
            'Km Entretien (Début)': entretien.kilometrage,
            'Km Entretien (Fin)': entretien.kilometrage_apres,
            'Garage': entretien.garage,
            'Motif': entretien.motif,
            'Coût ($)': entretien.cout,
            'Statut': entretien.get_statut_display(),
            'Date Ancien Entretien': date_ancien_entretien,
            'Km Ancien Entretien': kilometrage_ancien_entretien,
            'Km Prévu Actuel (basé sur l\'ancien)': kilometrage_prevu_actuel,
            'Écart Prévu vs Réalisé (Km)': ecart_prevu_realise,
            'Projection Prochain Entretien (Km)': projection_prochain_entretien,
        })
        if entretien.statut == 'termine' and entretien.cout is not None:
            total_budget_consomme += entretien.cout
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation Excel des entretiens",
    )
    
    # Ajouter le nom de l'établissement dans le titre et le budget consommé
    titre = f"Liste des Entretiens - Établissement : {request.user.etablissement.nom if not request.user.is_superuser and hasattr(request.user, 'etablissement') and request.user.etablissement else 'Tous'} (Budget Consommé: {total_budget_consomme:.2f} $)"
    
    # Générer le Excel
    return export_to_excel(
        titre,
        data,
        "entretiens.xlsx"
    )

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_entretien_pdf(request, entretien_id):
    """Vue pour exporter les détails d'un entretien en PDF avec une mise en page personnalisée"""
    # Pas besoin d'importer timezone ici, déjà importé en haut du fichier
    
    # Récupérer l'entretien
    entretien = get_object_or_404(Entretien, pk=entretien_id)
    
    # Récupérer l'entretien précédent pour les calculs
    previous_entretien = Entretien.objects.filter(
        vehicule=entretien.vehicule,
        date_entretien__lt=entretien.date_entretien
    ).order_by('-date_entretien').first()

    # Initialiser les variables pour le kilométrage
    kilometrage_ancien_entretien = "N/A"
    kilometrage_prevu_actuel = 0
    ecart_prevu_realise = "N/A"

    # Calculer les informations sur le kilométrage
    if previous_entretien:
        # Utiliser la date de l'ancien entretien pour le contexte
        _ = previous_entretien.date_entretien  # Variable non utilisée mais conservée pour référence
        kilometrage_ancien_entretien = previous_entretien.kilometrage_apres or previous_entretien.kilometrage or 0
        
        # Calculer le kilométrage prévu pour l'entretien actuel (ancien + 4500km)
        kilometrage_prevu_actuel = (kilometrage_ancien_entretien or 0) + 4500
        
        # Calculer l'écart entre le prévu et le réalisé
        if entretien.kilometrage is not None:
            ecart_km = (kilometrage_prevu_actuel - entretien.kilometrage)
            statut_ecart = "en avance" if ecart_km > 0 else "en retard" if ecart_km < 0 else "à temps"
            ecart_prevu_realise = f"{abs(ecart_km):.0f} km ({statut_ecart})"
    
    # Calculer la projection pour le prochain entretien
    projection_prochain_entretien = (entretien.kilometrage_apres or entretien.kilometrage or 0) + 4500
    
    # Vérifier s'il y a une pièce justificative
    piece_justificative = entretien.piece_justificative
    
    # Préparer le contexte pour le template
    context = {
        'title': f"Fiche d'Entretien - {entretien.vehicule.immatriculation}",
        'entretien': entretien,
        'date_export': timezone.now(),
        'kilometrage_ancien_entretien': kilometrage_ancien_entretien,
        'kilometrage_prevu_actuel': kilometrage_prevu_actuel,
        'ecart_prevu_realise': ecart_prevu_realise,
        'projection_prochain_entretien': projection_prochain_entretien,
        'piece_justificative': piece_justificative,
        'user': request.user,
        'logo_data_uri': None  # Sera rempli par la fonction render_to_pdf
    }
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Exportation PDF de l'entretien #{entretien_id}",
    )
    
    # Générer le PDF avec le template personnalisé
    from core.utils import render_to_pdf
    response = render_to_pdf('entretien/pdf/entretien_detail_pdf.html', context)
    
    # Si la génération a réussi, on renvoie la réponse avec le bon nom de fichier
    if response:
        filename = f"entretien_{entretien_id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_entretien_excel(request, entretien_id):
    """Vue pour exporter les détails d'un entretien en Excel"""
    entretien = get_object_or_404(Entretien, pk=entretien_id)
    
    previous_entretien = Entretien.objects.filter(
        vehicule=entretien.vehicule,
        date_entretien__lt=entretien.date_entretien
    ).order_by('-date_entretien').first()

    date_ancien_entretien = "N/A"
    kilometrage_ancien_entretien = "N/A"
    kilometrage_prevu_actuel = 0
    ecart_prevu_realise = "N/A"

    if previous_entretien:
        date_ancien_entretien = previous_entretien.date_entretien.strftime('%d/%m/%Y')
        kilometrage_ancien_entretien = previous_entretien.kilometrage_apres or previous_entretien.kilometrage or 0
        
        kilometrage_prevu_actuel = (kilometrage_ancien_entretien or 0) + 4500
        
        if entretien.kilometrage is not None:
            ecart_prevu_realise = (kilometrage_prevu_actuel - entretien.kilometrage)
        
    projection_prochain_entretien = (entretien.kilometrage_apres or entretien.kilometrage or 0) + 4500

    # Préparer les données pour l'exportation
    data = [{
        'Véhicule': entretien.vehicule.immatriculation,
        'Marque/Modèle': f"{entretien.vehicule.marque} {entretien.vehicule.modele}",
        'Châssis': entretien.vehicule.numero_chassis or '',
        'Moteur': entretien.vehicule.numero_moteur or '',
        'Carte rose': entretien.vehicule.numero_carte_rose or '',
        'Km début véhicule': entretien.vehicule.kilometrage_debut if entretien.vehicule.kilometrage_debut is not None else '',
        'Pneus': entretien.vehicule.pneus_resume() or '',
        'Date Entretien Actuel': entretien.date_entretien.strftime('%d/%m/%Y'),
        'Kilométrage (Début)': entretien.kilometrage,
        'Kilométrage (Fin)': entretien.kilometrage_apres,
        'Statut': entretien.get_statut_display(),
        'Motif': entretien.motif,
        'Coût ($)': entretien.cout,
        'Garage': entretien.garage,
        'Commentaires': entretien.commentaires or "Aucun commentaire",
        'Date Ancien Entretien': date_ancien_entretien,
        'Km Ancien Entretien': kilometrage_ancien_entretien,
        'Km Prévu Actuel (basé sur l\'ancien)': kilometrage_prevu_actuel,
        'Écart Prévu vs Réalisé (Km)': ecart_prevu_realise,
        'Projection Prochain Entretien (Km)': projection_prochain_entretien,
    }]
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Exportation Excel de l'entretien #{entretien_id}",
    )
    
    # Générer le Excel
    return export_to_excel(
        f"Détails de l'Entretien - {entretien.vehicule.immatriculation}", 
        data, 
        f"entretien_{entretien_id}.xlsx"
    )

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def get_vehicule_kilometrage(request):
    vehicule_id = request.GET.get('vehicule_id')
    if vehicule_id:
        try:
            vehicule = Vehicule.objects.get(id=vehicule_id)
            latest_kilometrage = _get_latest_kilometrage_for_vehicule(vehicule)
            prochain_entretien_km = (vehicule.kilometrage_dernier_entretien or 0) + 4500
            return JsonResponse({'kilometrage': latest_kilometrage, 'prochain_entretien_km': prochain_entretien_km})
        except Vehicule.DoesNotExist:
            return JsonResponse({'error': 'Véhicule non trouvé'}, status=404)
    return JsonResponse({'error': 'ID du véhicule manquant'}, status=400)


def _reparations_queryset(request):
    qs = ReparationMecanique.objects.select_related(
        'vehicule', 'vehicule__etablissement', 'createur', 'confirme_par'
    )
    if not request.user.is_superuser and getattr(request.user, 'etablissement', None):
        qs = qs.filter(vehicule__etablissement=request.user.etablissement)
    return qs


def _filtered_reparations_queryset(request):
    """Applique les filtres GET (liste / exports)."""
    queryset = _reparations_queryset(request)
    vehicule_id = request.GET.get('vehicule')
    statut = request.GET.get('statut')
    recherche = request.GET.get('recherche')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if statut:
        queryset = queryset.filter(statut=statut)
    if recherche:
        queryset = queryset.filter(
            Q(titre__icontains=recherche)
            | Q(description__icontains=recherche)
            | Q(vehicule__immatriculation__icontains=recherche)
            | Q(garage__icontains=recherche)
        )
    if date_debut:
        queryset = queryset.filter(date_signalement__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_signalement__lte=date_fin)
    return queryset.order_by('-date_signalement', '-id')


def _reparation_export_rows(queryset):
    data = []
    total_provisoire = 0
    total_confirme = 0
    for r in queryset:
        ecart = None
        if r.devis_confirme is not None:
            ecart = float(r.devis_confirme) - float(r.devis_provisoire or 0)
            total_confirme += float(r.devis_confirme)
        total_provisoire += float(r.devis_provisoire or 0)
        data.append({
            'ID': r.id,
            'Véhicule': r.vehicule.immatriculation,
            'Marque/Modèle': f"{r.vehicule.marque} {r.vehicule.modele}".strip(),
            'Département': r.vehicule.etablissement.nom if r.vehicule.etablissement else '-',
            'Problème': r.titre,
            'Description': r.description or '',
            'Garage': r.garage or '-',
            'Statut': r.get_statut_display(),
            'Devis provisoire ($)': float(r.devis_provisoire or 0),
            'Devis confirmé ($)': float(r.devis_confirme) if r.devis_confirme is not None else '',
            'Écart ($)': round(ecart, 2) if ecart is not None else '',
            'Date signalement': r.date_signalement.strftime('%d/%m/%Y') if r.date_signalement else '',
            'Début réparation': r.date_debut_reparation.strftime('%d/%m/%Y') if r.date_debut_reparation else '',
            'Date terminée': r.date_reparation.strftime('%d/%m/%Y') if r.date_reparation else '',
            'Créé par': (
                r.createur.get_full_name() or r.createur.username
            ) if r.createur else '',
            'Confirmé par': (
                r.confirme_par.get_full_name() or r.confirme_par.username
            ) if r.confirme_par else '',
            'Commentaires': r.commentaires or '',
        })
    return data, total_provisoire, total_confirme


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def liste_reparations(request):
    queryset = _filtered_reparations_queryset(request)
    vehicule_id = request.GET.get('vehicule')
    statut = request.GET.get('statut')
    recherche = request.GET.get('recherche')

    paginator = Paginator(queryset.order_by('-date_signalement', '-id'), 15)
    page = request.GET.get('page')
    try:
        reparations = paginator.page(page)
    except PageNotAnInteger:
        reparations = paginator.page(1)
    except EmptyPage:
        reparations = paginator.page(paginator.num_pages)

    vehicules = Vehicule.objects.all().order_by('immatriculation')
    if not request.user.is_superuser and getattr(request.user, 'etablissement', None):
        vehicules = vehicules.filter(etablissement=request.user.etablissement)

    return render(request, 'entretien/liste_reparations.html', {
        'reparations': reparations,
        'vehicules': vehicules,
        'statuts': ReparationMecanique.STATUS_CHOICES,
        'filtre_vehicule': vehicule_id or '',
        'filtre_statut': statut or '',
        'recherche': recherche or '',
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def creer_reparation(request):
    if request.method == 'POST':
        form = ReparationMecaniqueForm(request.POST, createur=request.user, user=request.user)
        if form.is_valid():
            reparation = form.save()
            messages.success(
                request,
                f"Problème signalé pour {reparation.vehicule.immatriculation} — devis provisoire {reparation.devis_provisoire} $."
            )
            return redirect('entretien:detail_reparation', reparation_id=reparation.id)
    else:
        initial = {}
        if request.GET.get('vehicule'):
            initial['vehicule'] = request.GET.get('vehicule')
        form = ReparationMecaniqueForm(createur=request.user, user=request.user, initial=initial)

    return render(request, 'entretien/formulaire_reparation.html', {
        'form': form,
        'title': 'Signaler un problème mécanique',
        'mode': 'create',
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def detail_reparation(request, reparation_id):
    reparation = get_object_or_404(_reparations_queryset(request), pk=reparation_id)
    return render(request, 'entretien/detail_reparation.html', {'reparation': reparation})


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def modifier_reparation(request, reparation_id):
    reparation = get_object_or_404(_reparations_queryset(request), pk=reparation_id)
    if reparation.statut == 'repare':
        messages.warning(request, "Cette réparation est clôturée. Utilisez la fiche détail pour consulter le devis confirmé.")
        return redirect('entretien:detail_reparation', reparation_id=reparation.id)

    if request.method == 'POST':
        form = ReparationMecaniqueForm(
            request.POST, instance=reparation, createur=request.user, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Réparation mise à jour.")
            return redirect('entretien:detail_reparation', reparation_id=reparation.id)
    else:
        form = ReparationMecaniqueForm(instance=reparation, createur=request.user, user=request.user)

    return render(request, 'entretien/formulaire_reparation.html', {
        'form': form,
        'title': 'Modifier la réparation',
        'reparation': reparation,
        'mode': 'edit',
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def confirmer_reparation(request, reparation_id):
    """Passe en statut Réparé avec devis confirmé (bilan comptable)."""
    reparation = get_object_or_404(_reparations_queryset(request), pk=reparation_id)
    if reparation.statut == 'repare':
        messages.info(request, "Cette réparation est déjà clôturée.")
        return redirect('entretien:detail_reparation', reparation_id=reparation.id)
    if reparation.statut == 'annule':
        messages.error(request, "Impossible de confirmer une réparation annulée.")
        return redirect('entretien:detail_reparation', reparation_id=reparation.id)

    if request.method == 'POST':
        form = ConfirmerReparationForm(request.POST, request.FILES, instance=reparation)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.statut = 'repare'
            obj.confirme_par = request.user
            if not obj.date_reparation:
                obj.date_reparation = timezone.localdate()
            obj.save()
            messages.success(
                request,
                f"Réparation clôturée — devis confirmé {obj.devis_confirme} $ enregistré pour le bilan."
            )
            return redirect('entretien:detail_reparation', reparation_id=reparation.id)
    else:
        form = ConfirmerReparationForm(instance=reparation)

    return render(request, 'entretien/confirmer_reparation.html', {
        'form': form,
        'reparation': reparation,
        'title': 'Confirmer la réparation (devis réel)',
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def supprimer_reparation(request, reparation_id):
    reparation = get_object_or_404(_reparations_queryset(request), pk=reparation_id)
    if request.method == 'POST':
        immat = reparation.vehicule.immatriculation
        reparation.delete()
        messages.success(request, f"Réparation de {immat} supprimée.")
        return redirect('entretien:liste_reparations')
    return render(request, 'entretien/confirmer_suppression_reparation.html', {
        'reparation': reparation,
    })


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_reparations_pdf(request):
    """Export PDF de la liste des réparations mécaniques (filtres GET respectés)."""
    queryset = _filtered_reparations_queryset(request)
    data, total_provisoire, total_confirme = _reparation_export_rows(queryset)
    etablissement_nom = (
        request.user.etablissement.nom
        if not request.user.is_superuser and getattr(request.user, 'etablissement', None)
        else 'Tous'
    )
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation PDF des réparations mécaniques",
    )
    return render_to_pdf(
        'entretien/pdf/liste_reparations_pdf.html',
        {
            'title': 'Liste des Réparations mécaniques',
            'date_export': timezone.now(),
            'etablissement': etablissement_nom,
            'total_provisoire': total_provisoire,
            'total_confirme': total_confirme,
            'reparations': queryset,
            'user': request.user,
        },
        filename=f"liste_reparations_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf",
    )


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_reparations_excel(request):
    """Export Excel de la liste des réparations mécaniques."""
    queryset = _filtered_reparations_queryset(request)
    data, total_provisoire, total_confirme = _reparation_export_rows(queryset)
    etablissement_nom = (
        request.user.etablissement.nom
        if not request.user.is_superuser and getattr(request.user, 'etablissement', None)
        else 'Tous'
    )
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation Excel des réparations mécaniques",
    )
    titre = (
        f"Réparations mécaniques — {etablissement_nom} "
        f"(Provisoire: {total_provisoire:.2f} $ / Confirmé: {total_confirme:.2f} $)"
    )
    return export_to_excel(
        titre,
        data,
        f"reparations_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx",
    )


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_reparation_pdf(request, reparation_id):
    """Export PDF du détail d'une réparation mécanique."""
    reparation = get_object_or_404(_reparations_queryset(request), pk=reparation_id)
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Exportation PDF réparation mécanique #{reparation_id}",
    )
    response = render_to_pdf(
        'entretien/pdf/reparation_detail_pdf.html',
        {
            'title': f"Réparation — {reparation.vehicule.immatriculation}",
            'reparation': reparation,
            'ecart': reparation.ecart_devis,
            'date_export': timezone.now(),
            'user': request.user,
        },
        filename=f"reparation_{reparation_id}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf",
    )
    return response


@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_reparation_excel(request, reparation_id):
    """Export Excel du détail d'une réparation mécanique."""
    reparation = get_object_or_404(_reparations_queryset(request), pk=reparation_id)
    data, _, _ = _reparation_export_rows([reparation])
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Exportation Excel réparation mécanique #{reparation_id}",
    )
    return export_to_excel(
        f"Réparation mécanique — {reparation.vehicule.immatriculation}",
        data,
        f"reparation_{reparation_id}.xlsx",
    )
