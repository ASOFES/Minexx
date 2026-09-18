from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from core.models import Vehicule, ActionTraceur, Course
from .models import Ravitaillement, Station
from .forms import RavitaillementForm, StationForm
from core.utils import export_to_pdf, export_to_excel  # export_to_pdf_with_image temporairement commenté
from core.decorators import is_admin_or_dispatch_or_superuser
from django.utils import timezone
from entretien.models import Entretien
import os


def _ravitaillement_queryset_for_user(user):
    qs = Ravitaillement.objects.all()
    if not user.is_superuser:
        qs = qs.filter(vehicule__etablissement=user.etablissement)
    return qs


def _get_ravitaillement_for_user(user, ravitaillement_id):
    return get_object_or_404(_ravitaillement_queryset_for_user(user), pk=ravitaillement_id)


def recalculer_kilometrage_actuel_vehicule(vehicule):
    """Recalcule kilometrage_actuel à partir des sources restantes."""
    candidats = []
    dernier_rav = (
        Ravitaillement.objects.filter(vehicule=vehicule, kilometrage_apres__isnull=False)
        .order_by('-kilometrage_apres')
        .first()
    )
    if dernier_rav:
        candidats.append(dernier_rav.kilometrage_apres)

    derniere_course = (
        Course.objects.filter(vehicule=vehicule, statut='terminee', kilometrage_fin__isnull=False)
        .order_by('-kilometrage_fin')
        .first()
    )
    if derniere_course:
        candidats.append(derniere_course.kilometrage_fin)

    dernier_entretien = (
        Entretien.objects.filter(vehicule=vehicule, statut='termine')
        .order_by('-date_entretien')
        .first()
    )
    if dernier_entretien:
        km = dernier_entretien.kilometrage_apres or dernier_entretien.kilometrage
        if km is not None:
            candidats.append(km)

    vehicule.kilometrage_actuel = max(candidats) if candidats else None
    vehicule.save(update_fields=['kilometrage_actuel'])
    return vehicule.kilometrage_actuel


# Fonction pour vérifier si l'utilisateur est admin ou superuser
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.role in ['admin', 'dispatch'] or user.is_superuser)


# Vues pour la gestion des stations
class StationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Station
    template_name = 'ravitaillement/station_list.html'
    context_object_name = 'stations'
    paginate_by = 20
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_queryset(self):
        queryset = Station.objects.filter(etablissement=self.request.user.etablissement)
        
        # Filtrage par recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) |
                Q(ville__icontains=search_query) |
                Q(adresse__icontains=search_query) |
                Q(telephone__icontains=search_query)
            )
            
        # Filtre par statut actif/inactif
        est_active = self.request.GET.get('est_active')
        if est_active in ['true', 'false']:
            queryset = queryset.filter(est_active=est_active == 'true')
            
        return queryset.order_by('nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_stations_count'] = Station.objects.filter(
            etablissement=self.request.user.etablissement, 
            est_active=True
        ).count()
        context['total_stations'] = context['object_list'].count()
        return context


class StationCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Station
    form_class = StationForm
    template_name = 'ravitaillement/station_form.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def form_valid(self, form):
        form.instance.etablissement = self.request.user.etablissement
        response = super().form_valid(form)
        messages.success(self.request, f'La station "{self.object.nom}" a été créée avec succès.')
        return response
    
    def get_success_url(self):
        return reverse('ravitaillement:liste_stations')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Ajouter une station'
        context['submit_text'] = 'Créer la station'
        return context


class StationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Station
    form_class = StationForm
    template_name = 'ravitaillement/station_form.html'
    
    def test_func(self):
        return is_admin_or_superuser(self.request.user)
    
    def get_queryset(self):
        return Station.objects.filter(etablissement=self.request.user.etablissement)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'La station "{self.object.nom}" a été mise à jour avec succès.')
        return response
    
    def get_success_url(self):
        return reverse('ravitaillement:liste_stations')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Modifier la station: {self.object.nom}'
        context['submit_text'] = 'Mettre à jour'
        return context


@login_required
@user_passes_test(is_admin_or_superuser)
@require_http_methods(['POST'])
def toggle_station_status(request, pk):
    """Active ou désactive une station"""
    station = get_object_or_404(Station, pk=pk, etablissement=request.user.etablissement)
    station.est_active = not station.est_active
    station.save()
    
    action = 'activée' if station.est_active else 'désactivée'
    messages.success(request, f'La station "{station.nom}" a été {action} avec succès.')
    
    return HttpResponseRedirect(reverse('ravitaillement:liste_stations'))


@login_required
@user_passes_test(is_admin_or_superuser)
@require_http_methods(['POST'])
def supprimer_station(request, pk):
    """Supprime une station si elle n'est pas utilisée"""
    station = get_object_or_404(Station, pk=pk, etablissement=request.user.etablissement)
    
    # Vérifier si la station est utilisée dans des ravitaillements
    if station.ravitaillements.exists():
        messages.error(
            request,
            f'Impossible de supprimer la station "{station.nom}" car elle est utilisée dans {station.ravitaillements.count()} ravitaillement(s).'
        )
    else:
        station.delete()
        messages.success(request, f'La station "{station.nom}" a été supprimée avec succès.')
    
    return HttpResponseRedirect(reverse('ravitaillement:liste_stations'))

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def dashboard(request):
    """Vue pour le tableau de bord du module Ravitaillement"""
    # Récupérer les statistiques
    ravitaillements_count = Ravitaillement.objects.filter(vehicule__etablissement=request.user.etablissement).count()
    
    # Initialiser le queryset
    queryset = Ravitaillement.objects.filter(vehicule__etablissement=request.user.etablissement)
    
    # Filtres
    vehicule_id = request.GET.get('vehicule')
    tri = request.GET.get('tri', 'date')
    
    # Appliquer les filtres
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    
    # Appliquer le tri
    if tri == 'date':
        queryset = queryset.order_by('-date_ravitaillement')
    elif tri == 'date_asc':
        queryset = queryset.order_by('date_ravitaillement')
    elif tri == 'vehicule':
        queryset = queryset.order_by('vehicule__immatriculation')
    else:
        queryset = queryset.order_by('-date_ravitaillement')
    
    # Limiter aux 5 derniers ravitaillements pour l'affichage
    ravitaillements_recents = queryset[:5]
    
    # Récupérer tous les véhicules pour le filtre
    vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement).order_by('immatriculation')
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation du tableau de bord Ravitaillement",
    )
    
    context = {
        'ravitaillements_count': ravitaillements_count,
        'ravitaillements_recents': ravitaillements_recents,
        'vehicules': vehicules,
        'selected_vehicule': vehicule_id,
        'selected_tri': tri,
    }
    
    return render(request, 'ravitaillement/dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def liste_ravitaillements(request):
    """Vue pour afficher la liste des ravitaillements"""
    # Initialiser le queryset
    queryset = Ravitaillement.objects.filter(vehicule__etablissement=request.user.etablissement).select_related('chauffeur')
    
    # Filtres
    vehicule_id = request.GET.get('vehicule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    tri = request.GET.get('tri', 'date')
    
    # Appliquer les filtres
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if date_debut:
        queryset = queryset.filter(date_ravitaillement__date__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_ravitaillement__date__lte=date_fin)
    
    # Appliquer le tri
    if tri == 'date':
        queryset = queryset.order_by('-date_ravitaillement')
    elif tri == 'date_asc':
        queryset = queryset.order_by('date_ravitaillement')
    elif tri == 'litres':
        queryset = queryset.order_by('-litres')
    elif tri == 'litres_asc':
        queryset = queryset.order_by('litres')
    elif tri == 'cout':
        queryset = queryset.order_by('-cout_total')
    elif tri == 'cout_asc':
        queryset = queryset.order_by('cout_total')
    else:
        queryset = queryset.order_by('-date_ravitaillement')
    
    # Pagination
    page = request.GET.get('page', 1)
    items_per_page = 12  # Nombre d'éléments par page
    paginator = Paginator(queryset, items_per_page)
    
    try:
        ravitaillements_page = paginator.page(page)
    except PageNotAnInteger:
        # Si la page n'est pas un entier, afficher la première page
        ravitaillements_page = paginator.page(1)
    except EmptyPage:
        # Si la page est hors limites (par exemple 9999), afficher la dernière page
        ravitaillements_page = paginator.page(paginator.num_pages)
    
    # Récupérer tous les véhicules pour le filtre
    vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement).order_by('immatriculation')
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation de la liste des ravitaillements",
    )
    
    context = {
        'ravitaillements': ravitaillements_page,
        'vehicules': vehicules,
        'page_obj': ravitaillements_page,  # Pour la pagination
    }
    
    return render(request, 'ravitaillement/liste_ravitaillements.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def creer_ravitaillement(request):
    """Vue pour créer un nouveau ravitaillement"""
    if request.method == 'POST':
        # Toujours passer request.FILES au formulaire
        form = RavitaillementForm(request.POST, request.FILES, createur=request.user)
        if form.is_valid():
            ravitaillement = form.save(commit=False)
            ravitaillement.date_ravitaillement = timezone.now()

            # Vérification critique : S'assurer que le véhicule est bien associé
            if not ravitaillement.vehicule:
                messages.error(request, "Le véhicule n'a pas été correctement sélectionné ou associé. Veuillez vous assurer que le véhicule existe et est valide.")
                return render(request, 'ravitaillement/formulaire_ravitaillement.html', {'form': form, 'title': 'Nouveau Ravitaillement'})

            ravitaillement.etablissement = ravitaillement.vehicule.etablissement
            # Si l'utilisateur est chauffeur, il est automatiquement assigné
            if request.user.role == 'chauffeur':
                ravitaillement.chauffeur = request.user
            # Sinon, on garde le chauffeur choisi dans le formulaire
            # Gestion de l'image :
            if 'image' in request.FILES:
                ravitaillement.image = request.FILES['image']
            # Sinon, on laisse le champ vide
            # Vérifier que le kilométrage n'est pas inférieur au dernier kilométrage enregistré
            dernier_kilometrage = 0
            # Utiliser ravitaillement.pk pour la cohérence et exclure l'objet courant uniquement s'il existe
            
            print(f"DEBUG: Valeur de ravitaillement.vehicule avant la requête: {ravitaillement.vehicule}")

            ravitaillement_qs = Ravitaillement.objects.filter(vehicule=ravitaillement.vehicule)
            if ravitaillement.pk: # Si l'objet a déjà une clé primaire (est en cours de modification, mais ici c'est une création)
                ravitaillement_qs = ravitaillement_qs.exclude(pk=ravitaillement.pk)

            dernier_ravitaillement = ravitaillement_qs.order_by('-date_ravitaillement').first()

            if dernier_ravitaillement and dernier_ravitaillement.kilometrage_apres is not None:
                dernier_kilometrage = dernier_ravitaillement.kilometrage_apres
            derniere_course = Course.objects.filter(
                vehicule=ravitaillement.vehicule,
                statut='terminee'
            ).order_by('-date_fin').first()
            if derniere_course and derniere_course.kilometrage_fin > dernier_kilometrage:
                dernier_kilometrage = derniere_course.kilometrage_fin
            dernier_entretien = Entretien.objects.filter(
                vehicule=ravitaillement.vehicule,
                kilometrage_apres__isnull=False
            ).order_by('-date_entretien').first()
            if dernier_entretien and dernier_entretien.kilometrage_apres > dernier_kilometrage:
                dernier_kilometrage = dernier_entretien.kilometrage_apres
            if ravitaillement.kilometrage_avant < dernier_kilometrage:
                messages.error(request, f"Le kilométrage avant ({ravitaillement.kilometrage_avant}) ne peut pas être inférieur au dernier kilométrage enregistré ({dernier_kilometrage}).")
                return render(request, 'ravitaillement/formulaire_ravitaillement.html', {'form': form, 'title': 'Nouveau Ravitaillement'})
            ravitaillement.save()
            messages.success(request, "Ravitaillement ajouté avec succès.")
            return redirect('ravitaillement:liste_ravitaillements')
        else:
            # Ajout d'un message d'erreur explicite si le fichier image n'est pas reçu
            if 'image' not in request.FILES and form.fields['image'].required:
                messages.error(request, "Le fichier image n'a pas été reçu. Veuillez réessayer.")
    else:
        vehicule_id = request.GET.get('vehicule')
        initial = {}
        if vehicule_id:
            try:
                vehicule = Vehicule.objects.get(id=vehicule_id)
                # Chercher le dernier ravitaillement de ce véhicule
                dernier_ravitaillement = Ravitaillement.objects.filter(vehicule=vehicule).order_by('-date_ravitaillement').first()
                if dernier_ravitaillement and dernier_ravitaillement.kilometrage_apres is not None:
                    initial['kilometrage_avant'] = dernier_ravitaillement.kilometrage_apres
                else:
                    initial['kilometrage_avant'] = 0
                initial['vehicule'] = vehicule.id
            except Vehicule.DoesNotExist:
                initial['kilometrage_avant'] = 0
        form = RavitaillementForm(createur=request.user, initial=initial)
    return render(request, 'ravitaillement/formulaire_ravitaillement.html', {'form': form, 'title': 'Nouveau Ravitaillement'})

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def detail_ravitaillement(request, ravitaillement_id):
    """Vue pour afficher les détails d'un ravitaillement"""
    ravitaillement = _get_ravitaillement_for_user(request.user, ravitaillement_id)
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Consultation des détails du ravitaillement #{ravitaillement_id}",
    )
    
    context = {
        'ravitaillement': ravitaillement,
    }
    
    return render(request, 'ravitaillement/detail_ravitaillement.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def modifier_ravitaillement(request, ravitaillement_id):
    """Vue pour modifier un ravitaillement existant"""
    ravitaillement = _get_ravitaillement_for_user(request.user, ravitaillement_id)
    
    if request.method == 'POST':
        form = RavitaillementForm(request.POST, request.FILES, instance=ravitaillement, createur=request.user)
        if form.is_valid():
            ravitaillement = form.save(commit=False)
            # La logique pour attribuer le chauffeur doit être gérée dans le formulaire ou lors de la création initiale.
            # Ici, nous ne modifions pas le chauffeur si le formulaire a déjà géré cela.
            # Si l'utilisateur est chauffeur et qu'il modifie son propre ravitaillement, il reste le chauffeur.
            # Pour les admins/dispatchers, le chauffeur peut être sélectionné via le formulaire.
            # S'assurer que le chauffeur du ravitaillement est bien celui assigné, pas l'utilisateur courant si non chauffeur.
            # La logique de `createur` est différente de celle de `chauffeur`.
            # Nous laissons le formulaire gérer l'attribution du champ `chauffeur`.
            # Si `form.cleaned_data['chauffeur']` est présent, on l'utilise, sinon, on garde l'existant.
            if 'chauffeur' in form.cleaned_data and form.cleaned_data['chauffeur']:
                ravitaillement.chauffeur = form.cleaned_data['chauffeur']
            elif not ravitaillement.chauffeur and request.user.role == 'chauffeur':
                ravitaillement.chauffeur = request.user
            # else: ravitaillement.chauffeur reste inchangé si non modifié via formulaire ou pas un chauffeur.
            
            # Trouver le kilométrage maximal enregistré AVANT la date de ce ravitaillement
            # excluant ce ravitaillement lui-même (si existant)

            # Kilométrage du ravitaillement précédent (chronologiquement)
            previous_ravitaillement = Ravitaillement.objects.filter(
                vehicule=ravitaillement.vehicule,
                date_ravitaillement__lt=ravitaillement.date_ravitaillement # Strictement avant
            ).exclude(id=ravitaillement.id).order_by('-date_ravitaillement').first()

            dernier_kilometrage_ravitaillement = previous_ravitaillement.kilometrage_apres if previous_ravitaillement and previous_ravitaillement.kilometrage_apres is not None else 0

            # Kilométrage de la dernière course terminée avant ce ravitaillement
            derniere_course_avant = Course.objects.filter(
                vehicule=ravitaillement.vehicule,
                statut='terminee',
                date_fin__lt=ravitaillement.date_ravitaillement # Strictement avant
            ).order_by('-date_fin').first()

            dernier_kilometrage_course = derniere_course_avant.kilometrage_fin if derniere_course_avant and derniere_course_avant.kilometrage_fin is not None else 0

            # Kilométrage du dernier entretien avant ce ravitaillement
            dernier_entretien_avant = Entretien.objects.filter(
                vehicule=ravitaillement.vehicule,
                kilometrage_apres__isnull=False,
                date_entretien__lt=ravitaillement.date_ravitaillement # Strictement avant
            ).order_by('-date_entretien').first()

            dernier_kilometrage_entretien = dernier_entretien_avant.kilometrage_apres if dernier_entretien_avant and dernier_entretien_avant.kilometrage_apres is not None else 0

            # Prendre le maximum des kilométrages trouvés avant la date de ce ravitaillement
            dernier_kilometrage_valide = max(dernier_kilometrage_ravitaillement, dernier_kilometrage_course, dernier_kilometrage_entretien)

            if ravitaillement.kilometrage_avant < dernier_kilometrage_valide:
                messages.error(request, f"Le kilométrage avant ({ravitaillement.kilometrage_avant} km) ne peut pas être inférieur au dernier kilométrage enregistré ({dernier_kilometrage_valide} km) AVANT la date de ce ravitaillement.")
                return render(request, 'ravitaillement/formulaire_ravitaillement.html', {
                    'form': form,
                    'ravitaillement': ravitaillement,
                    'title': f'Modifier le ravitaillement #{ravitaillement.id}'
                })

            # Also, ensure kilometrage_apres is greater than kilometrage_avant
            if ravitaillement.kilometrage_apres <= ravitaillement.kilometrage_avant:
                messages.error(request, "Le kilométrage après doit être strictement supérieur au kilométrage avant.")
                return render(request, 'ravitaillement/formulaire_ravitaillement.html', {
                    'form': form,
                    'ravitaillement': ravitaillement,
                    'title': f'Modifier le ravitaillement #{ravitaillement.id}'
                })

            ravitaillement.save()
            messages.success(request, 'Ravitaillement modifié avec succès.')
            return redirect('ravitaillement:detail_ravitaillement', ravitaillement.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
            print(form.errors)
    else:
        form = RavitaillementForm(instance=ravitaillement, createur=request.user)
    
    return render(request, 'ravitaillement/formulaire_ravitaillement.html', {
        'form': form,
        'ravitaillement': ravitaillement,
        'title': f'Modifier le ravitaillement #{ravitaillement.id}'
    })

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def supprimer_ravitaillement(request, ravitaillement_id):
    """Vue pour supprimer un ravitaillement"""
    ravitaillement = _get_ravitaillement_for_user(request.user, ravitaillement_id)
    
    if request.method == 'POST':
        vehicule = ravitaillement.vehicule
        # Tracer l'action
        ActionTraceur.objects.create(
            utilisateur=request.user,
            action=f"Suppression du ravitaillement #{ravitaillement_id}",
            details=f"Véhicule: {vehicule.immatriculation}",
        )
        
        ravitaillement.delete()
        recalculer_kilometrage_actuel_vehicule(vehicule)
        messages.success(request, "Le ravitaillement a été supprimé avec succès.")
        return redirect('ravitaillement:liste_ravitaillements')
    
    context = {
        'ravitaillement': ravitaillement,
    }
    
    return render(request, 'ravitaillement/confirmer_suppression.html', context)

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_ravitaillements_pdf(request):
    """Vue pour exporter la liste des ravitaillements en PDF"""
    queryset = Ravitaillement.objects.all()
    if not request.user.is_superuser:
        queryset = queryset.filter(vehicule__etablissement=request.user.etablissement)
    
    # Appliquer les filtres comme dans la vue liste_ravitaillements
    vehicule_id = request.GET.get('vehicule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    tri = request.GET.get('tri', 'date')
    
    # Appliquer les filtres
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if date_debut:
        queryset = queryset.filter(date_ravitaillement__date__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_ravitaillement__date__lte=date_fin)
    
    # Appliquer le tri
    if tri == 'date':
        queryset = queryset.order_by('-date_ravitaillement')
    elif tri == 'date_asc':
        queryset = queryset.order_by('date_ravitaillement')
    elif tri == 'litres':
        queryset = queryset.order_by('-litres')
    elif tri == 'litres_asc':
        queryset = queryset.order_by('litres')
    elif tri == 'cout':
        queryset = queryset.order_by('-cout_total')
    elif tri == 'cout_asc':
        queryset = queryset.order_by('cout_total')
    elif tri == 'vehicule':
        queryset = queryset.order_by('vehicule__immatriculation')
    else:
        queryset = queryset.order_by('-date_ravitaillement')
    
    # Préparer les données pour l'exportation
    data = []
    for ravitaillement in queryset:
        data.append({
            'Véhicule': ravitaillement.vehicule.immatriculation,
            'Station': ravitaillement.nom_station or 'Non spécifiée',
            'Date': ravitaillement.date_ravitaillement.strftime('%d/%m/%Y %H:%M'),
            'Kilométrage': f"{ravitaillement.kilometrage_apres} km",
            'Distance': f"{ravitaillement.distance_parcourue} km",
            'Litres': f"{ravitaillement.litres} L",
            'Prix unitaire': f"{ravitaillement.cout_unitaire} $/L",
            'Coût total': f"{ravitaillement.cout_total} $",
            'Consommation': f"{ravitaillement.consommation_moyenne:.2f} L/100km" if ravitaillement.consommation_moyenne > 0 else "N/A",
            'Chauffeur': ravitaillement.chauffeur.get_full_name() if ravitaillement.chauffeur else 'Non assigné',
            'Pièce jointe': ravitaillement.image.url if ravitaillement.image else '-',
        })
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation PDF des ravitaillements",
    )
    
    titre = f"Liste des Ravitaillements - Établissement : {request.user.etablissement.nom if not request.user.is_superuser and hasattr(request.user, 'etablissement') and request.user.etablissement else 'Tous'}"
    return export_to_pdf(
        titre,
        data,
        "ravitaillements.pdf",
        user=request.user
    )

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_ravitaillements_excel(request):
    """Vue pour exporter la liste des ravitaillements en Excel"""
    queryset = Ravitaillement.objects.all()
    if not request.user.is_superuser:
        queryset = queryset.filter(vehicule__etablissement=request.user.etablissement)
    
    # Appliquer les filtres comme dans la vue liste_ravitaillements
    vehicule_id = request.GET.get('vehicule')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    tri = request.GET.get('tri', 'date')
    
    # Appliquer les filtres
    if vehicule_id:
        queryset = queryset.filter(vehicule_id=vehicule_id)
    if date_debut:
        queryset = queryset.filter(date_ravitaillement__date__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date_ravitaillement__date__lte=date_fin)
    
    # Appliquer le tri
    if tri == 'date':
        queryset = queryset.order_by('-date_ravitaillement')
    elif tri == 'date_asc':
        queryset = queryset.order_by('date_ravitaillement')
    elif tri == 'litres':
        queryset = queryset.order_by('-litres')
    elif tri == 'litres_asc':
        queryset = queryset.order_by('litres')
    elif tri == 'cout':
        queryset = queryset.order_by('-cout_total')
    elif tri == 'cout_asc':
        queryset = queryset.order_by('cout_total')
    elif tri == 'vehicule':
        queryset = queryset.order_by('vehicule__immatriculation')
    else:
        queryset = queryset.order_by('-date_ravitaillement')
    
    # Préparer les données pour l'exportation
    data = []
    for ravitaillement in queryset:
        data.append({
            'Véhicule': ravitaillement.vehicule.immatriculation,
            'Station': ravitaillement.nom_station or 'Non spécifiée',
            'Date': ravitaillement.date_ravitaillement.strftime('%d/%m/%Y %H:%M'),
            'Kilométrage': ravitaillement.kilometrage_apres,
            'Distance': ravitaillement.distance_parcourue,
            'Litres': ravitaillement.litres,
            'Prix unitaire': ravitaillement.cout_unitaire,
            'Coût total': ravitaillement.cout_total,
            'Consommation (L/100km)': round(ravitaillement.consommation_moyenne, 2) if ravitaillement.consommation_moyenne > 0 else "N/A",
            'Chauffeur': ravitaillement.chauffeur.get_full_name() if ravitaillement.chauffeur else 'Non assigné',
            'Pièce jointe': ravitaillement.image.url if ravitaillement.image else '-',
        })
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation Excel des ravitaillements",
    )
    
    titre = f"Liste des Ravitaillements - Établissement : {request.user.etablissement.nom if not request.user.is_superuser and hasattr(request.user, 'etablissement') and request.user.etablissement else 'Tous'}"
    return export_to_excel(
        titre,
        data,
        "ravitaillements.xlsx"
    )

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_ravitaillement_pdf(request, ravitaillement_id):
    """Vue pour exporter les détails d'un ravitaillement en PDF"""
    ravitaillement = get_object_or_404(Ravitaillement, pk=ravitaillement_id)

    # Préparer les données pour l'exportation
    data = [{
        'Véhicule': ravitaillement.vehicule.immatriculation,
        'Marque/Modèle': f"{ravitaillement.vehicule.marque} {ravitaillement.vehicule.modele}",
        'Station': ravitaillement.nom_station or 'Non spécifiée',
        'Date': ravitaillement.date_ravitaillement.strftime('%d/%m/%Y %H:%M'),
        'Kilométrage avant': f"{ravitaillement.kilometrage_avant} km",
        'Kilométrage après': f"{ravitaillement.kilometrage_apres} km",
        'Distance parcourue': f"{ravitaillement.distance_parcourue} km",
        'Litres': f"{ravitaillement.litres} L",
        'Prix unitaire': f"{ravitaillement.cout_unitaire} $/L",
        'Coût total': f"{ravitaillement.cout_total} $",
        'Consommation': f"{ravitaillement.consommation_moyenne:.2f} L/100km" if ravitaillement.consommation_moyenne > 0 else "N/A",
        'Commentaires': ravitaillement.commentaires or "Aucun commentaire"
    }]

    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Exportation PDF du ravitaillement #{ravitaillement_id}",
    )

    # Préparer le chemin de l'image si elle existe et est lisible
    image_path = None
    if ravitaillement.image:
        try:
            print(f"DEBUG: Chemin de l'image dans le modèle: {ravitaillement.image.path}")
            if ravitaillement.image.path and os.path.exists(ravitaillement.image.path):
                image_path = ravitaillement.image.path
                print(f"DEBUG: Chemin d'image trouvé et existant: {image_path}")
            else:
                print(f"DEBUG: L'image n'existe pas à l'emplacement: {ravitaillement.image.path}")
        except Exception as e:
            print(f"DEBUG: Erreur lors de la vérification du chemin de l'image: {e}")
            messages.warning(request, f"Impossible d'inclure l'image dans le PDF : {e}")
            image_path = None

    # Temporairement désactivé pour le déploiement - export_to_pdf_with_image en cours de configuration
    return HttpResponse(
        "Export PDF avec image temporairement indisponible - fonction en cours de configuration",
        content_type='text/plain'
    )

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def exporter_ravitaillement_excel(request, ravitaillement_id):
    """Vue pour exporter les détails d'un ravitaillement en Excel"""
    ravitaillement = get_object_or_404(Ravitaillement, pk=ravitaillement_id)
    
    # Préparer les données pour l'exportation
    data = [{
        'Véhicule': ravitaillement.vehicule.immatriculation,
        'Marque/Modèle': f"{ravitaillement.vehicule.marque} {ravitaillement.vehicule.modele}",
        'Station': ravitaillement.nom_station or 'Non spécifiée',
        'Date': ravitaillement.date_ravitaillement.strftime('%d/%m/%Y %H:%M'),
        'Kilométrage avant': ravitaillement.kilometrage_avant,
        'Kilométrage après': ravitaillement.kilometrage_apres,
        'Distance parcourue': ravitaillement.distance_parcourue,
        'Litres': ravitaillement.litres,
        'Prix unitaire': ravitaillement.cout_unitaire,
        'Coût total': ravitaillement.cout_total,
        'Consommation (L/100km)': round(ravitaillement.consommation_moyenne, 2) if ravitaillement.consommation_moyenne > 0 else "N/A",
        'Commentaires': ravitaillement.commentaires or "Aucun commentaire"
    }]
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Exportation Excel du ravitaillement #{ravitaillement_id}",
    )
    
    # Générer le Excel
    return export_to_excel(
        f"Détails du Ravitaillement - {ravitaillement.vehicule.immatriculation}", 
        data, 
        f"ravitaillement_{ravitaillement_id}.xlsx"
    )

@login_required
@user_passes_test(is_admin_or_dispatch_or_superuser)
def get_vehicule_kilometrage(request):
    """API pour récupérer le kilométrage actuel d'un véhicule"""
    vehicule_id = request.GET.get('vehicule_id')
    
    if not vehicule_id:
        return JsonResponse({'error': 'Aucun ID de véhicule fourni'}, status=400)
    
    try:
        vehicule = Vehicule.objects.get(id=vehicule_id)
        
        # Vérifier d'abord le dernier ravitaillement
        dernier_ravitaillement = Ravitaillement.objects.filter(
            vehicule=vehicule
        ).order_by('-date_ravitaillement').first()

        # Si un ravitaillement existe, utiliser son kilométrage après comme kilométrage de départ
        if dernier_ravitaillement and dernier_ravitaillement.kilometrage_apres is not None:
            kilometrage = dernier_ravitaillement.kilometrage_apres
        else:
            # Sinon (pas de ravitaillement ou kilométrage après nul), chercher dans les courses et entretiens
            kilometrage_course = 0
            derniere_course = Course.objects.filter(
                vehicule=vehicule, 
                statut='terminee'
            ).order_by('-date_fin').first()
            if derniere_course and derniere_course.kilometrage_fin is not None:
                kilometrage_course = derniere_course.kilometrage_fin
            
            kilometrage_entretien = 0
            dernier_entretien = Entretien.objects.filter(
                vehicule=vehicule,
                kilometrage_apres__isnull=False
            ).order_by('-date_entretien').first()
            if dernier_entretien and dernier_entretien.kilometrage_apres is not None:
                kilometrage_entretien = dernier_entretien.kilometrage_apres
            
            # Prendre le maximum des kilométrages trouvés (peut être 0 si aucun historique)
            kilometrage = max(kilometrage_course, kilometrage_entretien)
        
        return JsonResponse({
            'success': True,
            'kilometrage': kilometrage,
            'immatriculation': vehicule.immatriculation
        })
        
    except Vehicule.DoesNotExist:
        return JsonResponse({'error': 'Véhicule non trouvé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
