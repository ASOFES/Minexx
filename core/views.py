from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
import os
from .models import Vehicule, Course, ActionTraceur, Utilisateur, Etablissement, ApplicationControl, Message
from .forms import UtilisateurCreationForm, UtilisateurChangeForm, ApplicationControlForm, AdminPasswordForm, EtablissementForm, ProfileSelfEditForm
from .vehicule_forms import VehiculeForm, VehiculeChangeEtablissementForm, VehiculeAccessoireFormSet
from .utils import render_to_pdf, get_latest_vehicle_kilometrage, export_to_excel
from entretien.models import Entretien
from ravitaillement.models import Ravitaillement
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .decorators import admin_required, departement_required, require_departement_password
from django import forms
from django.views.decorators.http import require_POST, require_GET
# from twilio.rest import Client  # Commenté pour le déploiement
from django.conf import settings
# import africastalking  # Commenté pour le déploiement
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from dotenv import load_dotenv
from django.db.models import Q
from datetime import datetime, time
import xlwt
from django.contrib.auth import get_user_model
from django.db import models
from django.views.i18n import set_language

# Fonction pour récupérer l'utilisateur système
def get_system_user():
    """
    Récupère l'utilisateur système ou le premier administrateur trouvé.
    Crée un utilisateur système si aucun n'existe.
    """
    User = get_user_model()
    # Essayer de récupérer l'utilisateur système
    system_user = User.objects.filter(username='system').first()
    
    if not system_user:
        # Si aucun utilisateur système n'existe, utiliser le premier superutilisateur
        system_user = User.objects.filter(is_superuser=True).first()
        
        if not system_user:
            # Ne jamais créer un superutilisateur automatiquement
            system_user = User(
                username='system',
                email='system@minexx.local',
                first_name='Système',
                last_name='MINEXX',
                role='admin',
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            system_user.set_unusable_password()
            system_user.save()
    
    return system_user

load_dotenv()

ADMIN_CONTROL_PASSWORD = os.environ.get('ADMIN_CONTROL_PASSWORD', '')
DEPARTEMENT_ACCESS_PASSWORD = os.environ.get('DEPARTEMENT_ACCESS_PASSWORD', '')

def home_view(request):
    """Vue pour la page d'accueil"""
    context = {}
    
    # Calcul du temps restant avant blocage
    try:
        control = ApplicationControl.objects.get(pk=1)
        now = timezone.now()
        if control.is_open and control.end_datetime and now < control.end_datetime:
            delta = control.end_datetime - now
            context['temps_restant'] = int(delta.total_seconds())
            context['temps_restant_str'] = str(delta).split('.')[0]  # HH:MM:SS
        else:
            context['temps_restant'] = 0
            context['temps_restant_str'] = None
    except ApplicationControl.DoesNotExist:
        context['temps_restant'] = None
        context['temps_restant_str'] = None
    
    if request.user.is_authenticated:
        if not request.user.is_superuser:
            if not request.user.etablissement:
                context['show_etablissement_modal'] = True
                context['etablissements'] = Etablissement.objects.all()
            if Etablissement.objects.count() == 0:
                context['no_etablissement'] = True
        # Récupérer les statistiques
        context['vehicules_count'] = Vehicule.objects.filter(etablissement=request.user.etablissement).count() if request.user.etablissement else 0
        context['courses_count'] = Course.objects.filter(etablissement=request.user.etablissement).count() if request.user.etablissement else 0
        context['entretiens_count'] = Entretien.objects.filter(vehicule__etablissement=request.user.etablissement).count() if request.user.etablissement else 0
        context['ravitaillements_count'] = Ravitaillement.objects.filter(vehicule__etablissement=request.user.etablissement).count() if request.user.etablissement else 0
        
        # Récupérer les activités récentes
        context['activites'] = ActionTraceur.objects.filter(utilisateur__etablissement=request.user.etablissement).order_by('-date_action')[:10] if request.user.etablissement else []
    
    return render(request, 'core/home.html', context)

def login_view(request):
    """Vue pour la page de connexion"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue, {user.username} !')
            
            # Rediriger vers la page appropriée en fonction du rôle
            if user.role == 'securite':
                return redirect('securite:dashboard')
            elif user.role == 'demandeur':
                return redirect('demandeur:dashboard')
            elif user.role == 'dispatch':
                return redirect('dispatch:dashboard')
            elif user.role == 'chauffeur':
                return redirect('chauffeur:dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'core/login.html')

def logout_view(request):
    """Vue pour la déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

@login_required
def profile_view(request):
    """Vue pour la page de profil utilisateur"""
    return render(request, 'core/profile.html')


@login_required
def profile_edit(request):
    """Permet à l'utilisateur connecté de modifier son propre profil."""
    if request.method == 'POST':
        form = ProfileSelfEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            ActionTraceur.objects.create(
                utilisateur=request.user,
                action="Modification de son profil",
                details=f"Utilisateur: {request.user.username}",
            )
            messages.success(request, "Votre profil a été mis à jour.")
            return redirect('profile')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
    else:
        form = ProfileSelfEditForm(instance=request.user)
    return render(request, 'core/profile_edit.html', {'form': form})


@login_required
def profile_password_change(request):
    """Permet à l'utilisateur connecté de changer son mot de passe."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            ActionTraceur.objects.create(
                utilisateur=request.user,
                action="Changement de mot de passe",
                details=f"Utilisateur: {request.user.username}",
            )
            messages.success(request, "Votre mot de passe a été modifié.")
            return redirect('profile')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{error}")
    else:
        form = PasswordChangeForm(request.user)
    for name in form.fields:
        form.fields[name].widget.attrs['class'] = 'form-control'
    return render(request, 'core/profile_password_change.html', {'form': form})


# Fonction pour vérifier si l'utilisateur est administrateur ou super administrateur
def is_admin_or_superuser(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

@login_required
@user_passes_test(is_admin_or_superuser)
def user_list(request):
    """Vue pour afficher la liste des utilisateurs (réservée aux administrateurs)"""
    etablissement_id = request.GET.get('etablissement')
    if request.user.is_superuser:
        etablissements = Etablissement.objects.all()
        users_list = Utilisateur.objects.all()
        if etablissement_id:
            users_list = users_list.filter(etablissement_id=etablissement_id)
    else:
        etablissements = Etablissement.get_departements_utilisateur(request.user)
        users_list = Utilisateur.objects.filter(etablissement__in=etablissements)
        if etablissement_id:
            users_list = users_list.filter(etablissement_id=etablissement_id)
    users_list = users_list.order_by('etablissement__nom', 'username')
    # Pagination - 5 utilisateurs par page
    paginator = Paginator(users_list, 5)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation de la liste des utilisateurs",
    )
    return render(request, 'core/user_list.html', {
        'users': users,
        'etablissements': etablissements,
        'etablissement_selected': int(etablissement_id) if etablissement_id else None,
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def user_create(request):
    """Vue pour créer un nouvel utilisateur (réservée aux administrateurs)"""
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            try:
                # Récupérer le mot de passe AVANT form.save()
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                telephone = form.cleaned_data.get('telephone')
                user = form.save()
                # Tracer l'action
                ActionTraceur.objects.create(
                    utilisateur=request.user,
                    action=f"Création de l'utilisateur {user.username}",
                    details=f"Rôle: {user.get_role_display()}"
                )
                # Envoi du SMS si le téléphone est renseigné
                if telephone:
                    # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN) # Commenté pour le déploiement
                    # try:
                    #     message = client.messages.create(
                    #         body=f"Bienvenue sur MAMO !\nIdentifiant: {username}\nMot de passe: {password}",
                    #         from_=settings.TWILIO_PHONE_NUMBER,
                    #         to=telephone
                    #     )
                    #     messages.success(request, f"SMS envoyé à {telephone}.")
                    # except Exception as e:
                    #     messages.error(request, f"Erreur lors de l'envoi du SMS: {e}")
                    pass # Commenté pour le déploiement
                messages.success(request, f"L'utilisateur {user.username} a été créé avec succès.")
                return redirect('user_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de l'utilisateur: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = UtilisateurCreationForm(user=request.user)
    # Afficher les champs disponibles dans le formulaire pour le débogage
    print(f"Champs disponibles dans le formulaire: {list(form.fields.keys())}")
    return render(request, 'core/user_form.html', {'form': form, 'title': 'Créer un utilisateur', 'mode': 'create'})

@login_required
@user_passes_test(is_admin_or_superuser)
def user_edit(request, pk):
    """Vue pour modifier un utilisateur existant (réservée aux administrateurs)"""
    user_to_edit = get_object_or_404(Utilisateur, pk=pk)
    
    if request.method == 'POST':
        form = UtilisateurChangeForm(request.POST, request.FILES, instance=user_to_edit)
        if form.is_valid():
            try:
                form.save()
                
                # Tracer l'action
                ActionTraceur.objects.create(
                    utilisateur=request.user,
                    action=f"Modification de l'utilisateur {user_to_edit.username}",
                    details=f"Rôle: {user_to_edit.get_role_display()}"
                )
                
                messages.success(request, f"L'utilisateur {user_to_edit.username} a été modifié avec succès.")
                return redirect('user_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de la modification de l'utilisateur: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        form = UtilisateurChangeForm(instance=user_to_edit)
    
    return render(request, 'core/user_form.html', {'form': form, 'title': 'Modifier un utilisateur', 'user_to_edit': user_to_edit, 'mode': 'edit'})

@login_required
@user_passes_test(is_admin_or_superuser)
def user_password_reset(request, pk):
    """Vue pour réinitialiser le mot de passe d'un utilisateur (réservée aux administrateurs)"""
    user = get_object_or_404(Utilisateur, pk=pk)
    
    if request.method == 'POST':
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            
            # Tracer l'action
            ActionTraceur.objects.create(
                utilisateur=request.user,
                action=f"Réinitialisation du mot de passe de l'utilisateur {user.username}",
            )
            
            messages.success(request, f"Le mot de passe de l'utilisateur {user.username} a été réinitialisé avec succès.")
            return redirect('user_list')
    else:
        form = SetPasswordForm(user)
    
    return render(request, 'core/user_password_reset.html', {'form': form, 'user': user})

@login_required
@user_passes_test(is_admin_or_superuser)
def user_toggle_active(request, pk):
    """Vue pour activer/désactiver un utilisateur (réservée aux administrateurs)"""
    user = get_object_or_404(Utilisateur, pk=pk)
    
    # Ne pas permettre de désactiver son propre compte
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect('user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    action = "Activation" if user.is_active else "Désactivation"
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"{action} de l'utilisateur {user.username}",
    )
    
    messages.success(request, f"L'utilisateur {user.username} a été {'activé' if user.is_active else 'désactivé'} avec succès.")
    return redirect('user_list')

@login_required
@user_passes_test(is_admin_or_superuser)
def user_delete(request, pk):
    user_to_delete = get_object_or_404(Utilisateur, pk=pk)
    if user_to_delete == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('user_list')
    if request.method == 'POST':
        ActionTraceur.objects.create(
            utilisateur=request.user,
            action=f"Suppression de l'utilisateur {user_to_delete.username}",
            details=f"Rôle: {user_to_delete.get_role_display()}"
        )
        user_to_delete.delete()
        messages.success(request, f"L'utilisateur {user_to_delete.username} a été supprimé avec succès.")
        return redirect('user_list')
    return render(request, 'core/user_confirm_delete.html', {'user_to_delete': user_to_delete})

# Gestion des véhicules
@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_list(request):
    """Liste des véhicules filtrée par département avec tri dynamique"""
    sort = request.GET.get('sort', 'immatriculation')
    valid_sorts = ['immatriculation', 'marque', 'modele', 'couleur']
    if sort not in valid_sorts:
        sort = 'immatriculation'
    if request.user.is_superuser:
        vehicules = Vehicule.objects.all().order_by(sort)
        departement_nom = "TOUS DÉPARTEMENTS"
    else:
        vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement).order_by(sort)
        departement_nom = request.user.etablissement.nom if request.user.etablissement else "Non assigné"
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Consultation de la liste des véhicules",
        details=f"Module: Véhicules, Tri: {sort}"
    )
    return render(request, 'core/vehicule/list.html', {
        'vehicules': vehicules,
        'departement_nom': departement_nom,
        'sort': sort,
    })

def _vehicule_accessoires_formset(request, instance=None):
    """Construit le formset accessoires; ignore un POST sans ManagementForm."""
    prefix = 'accessoires'
    if request.method == 'POST' and f'{prefix}-TOTAL_FORMS' in request.POST:
        if instance is not None:
            return VehiculeAccessoireFormSet(request.POST, instance=instance, prefix=prefix)
        return VehiculeAccessoireFormSet(request.POST, prefix=prefix)
    if instance is not None:
        return VehiculeAccessoireFormSet(instance=instance, prefix=prefix)
    return VehiculeAccessoireFormSet(prefix=prefix)


@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_create(request):
    """Vue pour créer un nouveau véhicule (réservée aux administrateurs)"""
    if request.method == 'POST':
        form = VehiculeForm(request.POST, request.FILES, user=request.user, createur=request.user)
        formset = _vehicule_accessoires_formset(request)
        formset_ok = (not formset.is_bound) or formset.is_valid()
        if form.is_valid() and formset_ok:
            try:
                vehicule = form.save()
                if formset.is_bound:
                    formset.instance = vehicule
                    formset.save()
                
                ActionTraceur.objects.create(
                    utilisateur=request.user,
                    action=f"Création du véhicule {vehicule.immatriculation}",
                    details=f"Marque: {vehicule.marque}, Modèle: {vehicule.modele}"
                )
                
                msg = f"Le véhicule {vehicule.immatriculation} a été créé avec succès."
                if not vehicule.est_fiche_complete():
                    msg += " Fiche partielle — à compléter plus tard."
                messages.success(request, msg)
                return redirect('vehicule_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du véhicule: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
            if formset.is_bound and not formset.is_valid():
                for err in formset.non_form_errors():
                    messages.error(request, str(err))
            # Réafficher un formset propre si le ManagementForm était cassé
            if formset.is_bound and not formset.is_valid() and formset.non_form_errors():
                formset = VehiculeAccessoireFormSet(prefix='accessoires')
    else:
        form = VehiculeForm(user=request.user, createur=request.user)
        formset = VehiculeAccessoireFormSet(prefix='accessoires')
    
    return render(request, 'core/vehicule_form.html', {
        'form': form,
        'accessoires_formset': formset,
        'title': 'Ajouter un véhicule',
        'mode': 'create',
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_edit(request, pk):
    """Vue pour modifier un véhicule existant (réservée aux administrateurs)"""
    vehicule = get_object_or_404(Vehicule, pk=pk)
    
    if request.method == 'POST':
        form = VehiculeForm(request.POST, request.FILES, instance=vehicule, createur=request.user)
        formset = _vehicule_accessoires_formset(request, instance=vehicule)
        formset_ok = (not formset.is_bound) or formset.is_valid()
        if form.is_valid() and formset_ok:
            try:
                form.save()
                if formset.is_bound:
                    formset.save()
                
                ActionTraceur.objects.create(
                    utilisateur=request.user,
                    action=f"Modification du véhicule {vehicule.immatriculation}",
                    details=f"Marque: {vehicule.marque}, Modèle: {vehicule.modele}"
                )
                
                messages.success(request, f"Le véhicule {vehicule.immatriculation} a été modifié avec succès.")
                return redirect('vehicule_list')
            except Exception as e:
                messages.error(request, f"Erreur lors de la modification du véhicule: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
            if formset.is_bound and not formset.is_valid():
                for err in formset.non_form_errors():
                    messages.error(request, str(err))
            if formset.is_bound and not formset.is_valid() and formset.non_form_errors():
                formset = VehiculeAccessoireFormSet(instance=vehicule, prefix='accessoires')
    else:
        form = VehiculeForm(instance=vehicule, createur=request.user)
        formset = VehiculeAccessoireFormSet(instance=vehicule, prefix='accessoires')
    
    return render(request, 'core/vehicule_form.html', {
        'form': form,
        'accessoires_formset': formset,
        'title': 'Modifier un véhicule',
        'vehicule': vehicule,
        'mode': 'edit',
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_delete(request, pk):
    """Vue pour supprimer un véhicule (réservée aux administrateurs)"""
    vehicule = get_object_or_404(Vehicule, pk=pk)
    
    if request.method == 'POST':
        # Enregistrer l'action
        ActionTraceur.objects.create(
            utilisateur=request.user,
            action=f"Suppression du véhicule {vehicule.immatriculation}",
            details="Module: Véhicules"
        )
        
        # Supprimer le véhicule
        vehicule.delete()
        
        messages.success(request, f"Le véhicule {vehicule.immatriculation} a été supprimé avec succès.")
        return redirect('vehicule_list')
    
    context = {
        'vehicule': vehicule
    }
    
    return render(request, 'core/vehicule_confirm_delete.html', context)

# Vue pour afficher les détails d'un véhicule
@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_detail(request, pk):
    """Vue pour afficher les détails d'un véhicule (réservée aux administrateurs)"""
    vehicule = get_object_or_404(Vehicule, pk=pk)
    
    # Enregistrer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Consultation des détails du véhicule {vehicule.immatriculation}",
        details="Module: Véhicules"
    )
    
    context = {
        'vehicule': vehicule
    }
    
    return render(request, 'core/vehicule_detail.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_detail_pdf(request, pk):
    """Vue pour générer un PDF des détails d'un véhicule (réservée aux administrateurs)"""
    vehicule = get_object_or_404(Vehicule, pk=pk)
    # Enregistrer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action=f"Exportation PDF des détails du véhicule {vehicule.immatriculation}",
        details="Module: Véhicules"
    )
    # Chemin absolu du logo
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.abspath(os.path.join(base_dir, 'static', 'images', 'logo_minexx.png'))
    # Image véhicule en base64
    import base64
    vehicle_image_base64 = None
    if vehicule.image and hasattr(vehicule.image, 'path') and os.path.exists(vehicule.image.path):
        try:
            with open(vehicule.image.path, 'rb') as img_file:
                img_data = img_file.read()
                vehicle_image_base64 = base64.b64encode(img_data).decode('utf-8')
        except Exception as e:
            vehicle_image_base64 = None
    context = {
        'vehicule': vehicule,
        'vehicule_image_base64': vehicle_image_base64,
        'date_generation': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'logo_path': logo_path,
    }
    pdf = render_to_pdf('core/pdf/vehicule_detail_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"vehicule_{vehicule.immatriculation}_{timezone.now().strftime('%Y%m%d')}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Une erreur s'est produite lors de la génération du PDF.")

@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_list_pdf(request):
    """Vue pour générer un PDF de la liste des véhicules (réservée aux administrateurs)"""
    if request.user.is_superuser:
        vehicules = Vehicule.objects.all().order_by('immatriculation')
        departement_nom = "TOUS DÉPARTEMENTS"
    else:
        vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement).order_by('immatriculation')
        departement_nom = request.user.etablissement.nom if request.user.etablissement else "Non assigné"
    
    # Filtrage si demandé
    marque = request.GET.get('marque', '')
    if marque:
        vehicules = vehicules.filter(marque__icontains=marque)
    
    modele = request.GET.get('modele', '')
    if modele:
        vehicules = vehicules.filter(modele__icontains=modele)
    
    immatriculation = request.GET.get('immatriculation', '')
    if immatriculation:
        vehicules = vehicules.filter(immatriculation__icontains=immatriculation)
    
    # Enregistrer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation PDF de la liste des véhicules",
        details=f"Module: Véhicules, Filtres: {marque} {modele} {immatriculation}"
    )
    
    # Chemin du logo MINEXX (à adapter selon l'emplacement réel du logo)
    logo_path = os.path.join('static', 'images', 'logo_minexx.png')
    
    context = {
        'vehicules': vehicules,
        'date_generation': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'logo_path': logo_path,
        'departement_nom': departement_nom
    }
    
    # Générer le PDF
    pdf = render_to_pdf('core/pdf/vehicule_list_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"liste_vehicules_{timezone.now().strftime('%Y%m%d')}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    
    return HttpResponse("Une erreur s'est produite lors de la génération du PDF.")

class EtablissementForm(forms.ModelForm):
    class Meta:
        model = Etablissement
        fields = ['nom']

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_etablissement(request):
    if request.method == 'POST':
        form = EtablissementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Département créé avec succès.")
            return redirect('home')
    else:
        form = EtablissementForm()
    return render(request, 'core/create_etablissement.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_user(request):
    if request.method == 'POST':
        form = UtilisateurCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur créé avec succès.")
            return redirect('user_list')
    else:
        form = UtilisateurCreationForm()
    return render(request, 'core/user_form.html', {'form': form, 'title': 'Créer un utilisateur', 'mode': 'create'})

@require_POST
@login_required
def choose_etablissement(request):
    if request.user.is_superuser:
        return redirect('home')
    etab_id = request.POST.get('etablissement')
    if etab_id:
        try:
            etab = Etablissement.objects.get(id=etab_id)
            request.user.etablissement = etab
            request.user.save()
            messages.success(request, "Département sélectionné avec succès.")
        except Etablissement.DoesNotExist:
            messages.error(request, "Département invalide.")
    else:
        messages.error(request, "Veuillez sélectionner un département.")
    return redirect('home')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def send_test_sms(request):
    # Récupérer l'utilisateur concerné depuis la requête
    user_id = request.GET.get('user_id')
    if not user_id:
        messages.error(request, "Aucun utilisateur spécifié")
        return redirect('home')
    
    try:
        # Récupérer l'utilisateur
        user = Utilisateur.objects.get(id=user_id)
        
        # Configuration Twilio
        # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN) # Commenté pour le déploiement
        # try:
        #     message = client.messages.create(
        #         body=f"Bonjour {user.username}, ceci est un message de test depuis Django avec Twilio!",
        #         from_=settings.TWILIO_PHONE_NUMBER,
        #         to=user.telephone
        #     )
        #     sms_sent = True
        #     sms_sid = message.sid
        # except Exception as e:
        #     sms_sent = False
        #     sms_sid = None
        
        # Envoi de l'email uniquement si l'utilisateur a un email
        if user.email:
            subject = f"Notification pour {user.username}"
            html_message = render_to_string('core/email_template.html', {
                'username': user.username,
                'message': "Ceci est un message de test depuis Django avec Twilio!",
                # 'sms_status': "envoyé" if sms_sent else "non envoyé (pas de numéro de téléphone)", # Commenté pour le déploiement
                # 'sms_sid': sms_sid # Commenté pour le déploiement
            })
            plain_message = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            
            # email_response = send_mail( # Commenté pour le déploiement
            #     subject,
            #     plain_message,
            #     from_email,
            #     [user.email],  # Email uniquement à l'utilisateur concerné
            #     html_message=html_message,
            #     fail_silently=False,
            # )
            email_sent = True
        else:
            email_sent = False
            email_response = None
        
        # Message de confirmation approprié
        # if sms_sent and email_sent: # Commenté pour le déploiement
        #     messages.success(request, f"Notifications envoyées à {user.username} (SMS et Email)") # Commenté pour le déploiement
        # elif sms_sent: # Commenté pour le déploiement
        #     messages.success(request, f"SMS envoyé à {user.username} (pas d'email configuré)") # Commenté pour le déploiement
        # elif email_sent: # Commenté pour le déploiement
        #     messages.success(request, f"Email envoyé à {user.username} (pas de numéro de téléphone configuré)") # Commenté pour le déploiement
        # else: # Commenté pour le déploiement
        #     messages.warning(request, f"Aucune notification envoyée à {user.username} (pas d'email ni de téléphone configuré)") # Commenté pour le déploiement
            
    except Utilisateur.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé")
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi : {e}")
    
    return redirect('home')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def send_test_sms_africastalking(request):
    # Récupérer l'utilisateur concerné depuis la requête
    user_id = request.GET.get('user_id')
    if not user_id:
        messages.error(request, "Aucun utilisateur spécifié")
        return redirect('home')
    
    try:
        # Récupérer l'utilisateur
        user = Utilisateur.objects.get(id=user_id)
        
        # Configuration Africa's Talking
        # africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY) # Commenté pour le déploiement
        # sms = africastalking.SMS # Commenté pour le déploiement
        # whatsapp = africastalking.WhatsApp # Commenté pour le déploiement
        
        # Envoi du SMS uniquement si l'utilisateur a un numéro de téléphone
        if user.telephone:
            # Envoi du SMS
            # sms_response = sms.send( # Commenté pour le déploiement
            #     message=f"Bonjour {user.username}, ceci est un message de test depuis Django avec Africa's Talking!", # Commenté pour le déploiement
            #     recipients=[user.telephone], # Commenté pour le déploiement
            #     sender_id=settings.AFRICASTALKING_SENDER_ID # Commenté pour le déploiement
            # ) # Commenté pour le déploiement
            sms_sent = True
            
            # Envoi du message WhatsApp
            # try: # Commenté pour le déploiement
            #     whatsapp_response = whatsapp.send( # Commenté pour le déploiement
            #         message=f"Bonjour {user.username}, ceci est un message WhatsApp de test depuis Django avec Africa's Talking!", # Commenté pour le déploiement
            #         recipients=[user.telephone] # Commenté pour le déploiement
            #     ) # Commenté pour le déploiement
            #     whatsapp_sent = True # Commenté pour le déploiement
            # except Exception as whatsapp_error: # Commenté pour le déploiement
            #     whatsapp_sent = False # Commenté pour le déploiement
            #     whatsapp_response = str(whatsapp_error) # Commenté pour le déploiement
        else:
            sms_sent = False
            # whatsapp_sent = False # Commenté pour le déploiement
            # sms_response = None # Commenté pour le déploiement
            # whatsapp_response = None # Commenté pour le déploiement
        
        # Envoi de l'email uniquement si l'utilisateur a un email
        if user.email:
            subject = f"Notification pour {user.username}"
            html_message = render_to_string('core/email_template.html', {
                'username': user.username,
                'message': "Ceci est un message de test depuis Django avec Africa's Talking!",
                # 'sms_status': "envoyé" if sms_sent else "non envoyé (pas de numéro de téléphone)", # Commenté pour le déploiement
                # 'whatsapp_status': "envoyé" if whatsapp_sent else "non envoyé", # Commenté pour le déploiement
                # 'sms_response': sms_response, # Commenté pour le déploiement
                # 'whatsapp_response': whatsapp_response # Commenté pour le déploiement
            })
            plain_message = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            
            # email_response = send_mail( # Commenté pour le déploiement
            #     subject, # Commenté pour le déploiement
            #     plain_message, # Commenté pour le déploiement
            #     from_email, # Commenté pour le déploiement
            #     [user.email],  # Email uniquement à l'utilisateur concerné
            #     html_message=html_message, # Commenté pour le déploiement
            #     fail_silently=False, # Commenté pour le déploiement
            # ) # Commenté pour le déploiement
            email_sent = True
        else:
            email_sent = False
            email_response = None
        
        # Message de confirmation approprié
        notifications = []
        # if sms_sent: # Commenté pour le déploiement
        #     notifications.append("SMS") # Commenté pour le déploiement
        # if whatsapp_sent: # Commenté pour le déploiement
        #     notifications.append("WhatsApp") # Commenté pour le déploiement
        if email_sent:
            notifications.append("Email")
            
        if notifications:
            messages.success(request, f"Notifications envoyées à {user.username} ({', '.join(notifications)})")
        else:
            messages.warning(request, f"Aucune notification envoyée à {user.username} (pas d'email ni de téléphone configuré)")
            
    except Utilisateur.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé")
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi : {e}")
    
    return redirect('home')

def send_mission_notifications(mission):
    """
    Envoie les notifications (SMS, WhatsApp, Email) lors de la validation d'une mission.
    """
    try:
        # Configuration Africa's Talking
        # africastalking.initialize(settings.AFRICASTALKING_USERNAME, settings.AFRICASTALKING_API_KEY) # Commenté pour le déploiement
        # sms = africastalking.SMS # Commenté pour le déploiement
        # whatsapp = africastalking.WhatsApp # Commenté pour le déploiement
        
        # Message de base
        base_message = f"Votre mission #{mission.id} a été validée.\n"
        base_message += f"Destination: {mission.destination}\n"
        base_message += f"Date souhaitée: {mission.date_souhaitee.strftime('%d/%m/%Y %H:%M') if mission.date_souhaitee else 'Non spécifiée'}\n"
        if mission.chauffeur:
            base_message += f"Chauffeur: {mission.chauffeur.get_full_name()}\n"
        if mission.vehicule:
            base_message += f"Véhicule: {mission.vehicule.immatriculation}"
        
        # Envoi du SMS si le demandeur a un numéro de téléphone
        if mission.demandeur.telephone:
            # try: # Commenté pour le déploiement
            #     sms_response = sms.send( # Commenté pour le déploiement
            #         message=base_message, # Commenté pour le déploiement
            #         recipients=[mission.demandeur.telephone], # Commenté pour le déploiement
            #         sender_id=settings.AFRICASTALKING_SENDER_ID # Commenté pour le déploiement
            #     ) # Commenté pour le déploiement
            #     sms_sent = True # Commenté pour le déploiement
            # except Exception as sms_error: # Commenté pour le déploiement
            #     sms_sent = False # Commenté pour le déploiement
            #     sms_response = str(sms_error) # Commenté pour le déploiement
            sms_sent = False # Commenté pour le déploiement
            sms_response = None # Commenté pour le déploiement
        else:
            sms_sent = False
            sms_response = None
        
        # Envoi du message WhatsApp si le demandeur a un numéro de téléphone
        if mission.demandeur.telephone:
            # try: # Commenté pour le déploiement
            #     whatsapp_message = f"*Mission #{mission.id} Validée*\n\n{base_message}\n\nMerci d'avoir utilisé notre service." # Commenté pour le déploiement
            #     whatsapp_response = whatsapp.send( # Commenté pour le déploiement
            #         message=whatsapp_message, # Commenté pour le déploiement
            #         recipients=[mission.demandeur.telephone] # Commenté pour le déploiement
            #     ) # Commenté pour le déploiement
            #     whatsapp_sent = True # Commenté pour le déploiement
            # except Exception as whatsapp_error: # Commenté pour le déploiement
            #     whatsapp_sent = False # Commenté pour le déploiement
            #     whatsapp_response = str(whatsapp_error) # Commenté pour le déploiement
            whatsapp_sent = False # Commenté pour le déploiement
            whatsapp_response = None # Commenté pour le déploiement
        
        # Envoi de l'email si le demandeur a une adresse email
        if mission.demandeur.email:
            subject = f"Mission #{mission.id} Validée"
            html_message = render_to_string('core/email_template.html', {
                'username': mission.demandeur.username,
                'message': base_message,
                # 'sms_status': "envoyé" if sms_sent else "non envoyé (pas de numéro de téléphone)", # Commenté pour le déploiement
                # 'whatsapp_status': "envoyé" if whatsapp_sent else "non envoyé", # Commenté pour le déploiement
                # 'sms_response': sms_response, # Commenté pour le déploiement
                # 'whatsapp_response': whatsapp_response # Commenté pour le déploiement
            })
            plain_message = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            
            # email_response = send_mail( # Commenté pour le déploiement
            #     subject, # Commenté pour le déploiement
            #     plain_message, # Commenté pour le déploiement
            #     from_email, # Commenté pour le déploiement
            #     [mission.demandeur.email], # Commenté pour le déploiement
            #     html_message=html_message, # Commenté pour le déploiement
            #     fail_silently=False, # Commenté pour le déploiement
            # ) # Commenté pour le déploiement
            email_sent = True
        else:
            email_sent = False
            email_response = None
        
        # Retourner le statut des notifications
        return {
            'sms_sent': sms_sent,
            'whatsapp_sent': whatsapp_sent,
            'email_sent': email_sent,
            'sms_response': sms_response,
            'whatsapp_response': whatsapp_response,
            'email_response': email_response
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'sms_sent': False,
            'whatsapp_sent': False,
            'email_sent': False
        }

def application_control_password(request):
    # Toujours supprimer la session spéciale pour forcer l'affichage du formulaire
    if request.session.get('admin_control_authenticated'):
        del request.session['admin_control_authenticated']
    if request.method == 'POST':
        form = AdminPasswordForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] and ADMIN_CONTROL_PASSWORD and form.cleaned_data['password'] == ADMIN_CONTROL_PASSWORD:
                request.session['admin_control_authenticated'] = True
                messages.info(request, "Veuillez configurer la nouvelle période d'utilisation avant de réactiver l'application.")
                return redirect('application_control')
            else:
                if not ADMIN_CONTROL_PASSWORD:
                    messages.error(request, "ADMIN_CONTROL_PASSWORD non configuré côté serveur.")
                else:
                    messages.error(request, "Mot de passe incorrect.")
    else:
        form = AdminPasswordForm()
    return render(request, 'core/application_control_password.html', {'form': form})

def application_control(request):
    if not request.session.get('admin_control_authenticated'):
        return redirect('application_control_password')
    control, _ = ApplicationControl.objects.get_or_create(pk=1)
    if request.method == 'POST':
        form = ApplicationControlForm(request.POST, instance=control)
        if form.is_valid():
            form.save()
            try:
                del request.session['admin_control_authenticated']
            except KeyError:
                pass
            messages.success(request, "Paramètres de contrôle mis à jour. Vous avez été déconnecté pour plus de sécurité.")
            return redirect('application_control_password')
    else:
        form = ApplicationControlForm(instance=control)
    return render(request, 'core/application_control.html', {'form': form, 'control': control})

def application_blocked(request):
    message = request.session.get('block_message', "L'application est actuellement bloquée. Veuillez contacter l'administrateur.")
    return render(request, 'core/application_blocked.html', {'message': message})

def application_control_logout(request):
    try:
        del request.session['admin_control_authenticated']
    except KeyError:
        pass
    return redirect('application_control_password')

@require_departement_password
@login_required
def departement_list(request):
    """Liste des départements accessibles à l'utilisateur"""
    departements = Etablissement.get_departements_utilisateur(request.user)
    return render(request, 'core/departement/list.html', {
        'departements': departements,
        'can_edit': request.user.role in ['admin', 'dispatch']
    })

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'dispatch'])
def departement_create(request):
    """Création d'un nouveau département"""
    if request.method == 'POST':
        form = EtablissementForm(request.POST)
        if form.is_valid():
            departement = form.save()
            messages.success(request, f'Département {departement.nom} créé avec succès.')
            return redirect('departement_list')
    else:
        form = EtablissementForm()
    return render(request, 'core/departement/form.html', {
        'form': form,
        'title': 'Créer un département'
    })

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'dispatch'])
def departement_edit(request, pk):
    """Modification d'un département existant"""
    departement = get_object_or_404(Etablissement, pk=pk)
    if request.method == 'POST':
        form = EtablissementForm(request.POST, instance=departement)
        if form.is_valid():
            departement = form.save()
            messages.success(request, f'Département {departement.nom} modifié avec succès.')
            return redirect('departement_list')
    else:
        form = EtablissementForm(instance=departement)
    return render(request, 'core/departement/form.html', {
        'form': form,
        'departement': departement,
        'title': f'Modifier {departement.nom}'
    })

@login_required
@departement_required
def departement_detail(request, pk):
    """Détails d'un département"""
    departement = get_object_or_404(Etablissement, pk=pk)
    if not request.user.peut_acceder_departement(departement):
        messages.error(request, "Vous n'avez pas accès à ce département.")
        return redirect('departement_list')
    
    context = {
        'departement': departement,
        'utilisateurs': departement.utilisateurs.all(),
        'vehicules': Vehicule.objects.filter(etablissement=departement),
        'courses': Course.objects.filter(etablissement=departement),
        'can_edit': request.user.role in ['admin', 'dispatch']
    }
    return render(request, 'core/departement/detail.html', context)

@login_required
def course_list(request):
    """Liste des courses filtrée par département"""
    departement_id = request.GET.get('departement')
    if departement_id:
        departement = get_object_or_404(Etablissement, pk=departement_id)
        if not request.user.peut_acceder_departement(departement):
            messages.error(request, "Vous n'avez pas accès à ce département.")
            return redirect('course_list')
        courses = Course.objects.filter(etablissement=departement)
    else:
        courses = Course.objects.filter(
            etablissement__in=request.user.get_departements_accessibles()
        )
    
    departements = request.user.get_departements_accessibles()
    return render(request, 'core/course/list.html', {
        'courses': courses,
        'departements': departements,
        'departement_selected': departement_id
    })

@login_required
@user_passes_test(lambda u: u.role == 'admin')
def user_change_departement(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk)
    etablissements = Etablissement.objects.all()
    if request.method == 'POST':
        new_departement_id = request.POST.get('departement')
        password = request.POST.get('departement_password')
        if not DEPARTEMENT_ACCESS_PASSWORD or password != DEPARTEMENT_ACCESS_PASSWORD:
            messages.error(request, "Mot de passe incorrect." if DEPARTEMENT_ACCESS_PASSWORD else "DEPARTEMENT_ACCESS_PASSWORD non configuré.")
        elif not new_departement_id:
            messages.error(request, "Veuillez sélectionner un département.")
        else:
            new_departement = get_object_or_404(Etablissement, pk=new_departement_id)
            user.etablissement = new_departement
            user.save()
            messages.success(request, f"Département de {user.get_full_name()} changé avec succès.")
            return redirect('user_list')
    return render(request, 'core/user_change_departement.html', {
        'user_obj': user,
        'etablissements': etablissements
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def user_list_excel(request):
    """Exporter la liste des utilisateurs en Excel"""
    # Récupérer les utilisateurs selon l'établissement
    if request.user.is_superuser:
        users = Utilisateur.objects.all()
    else:
        users = Utilisateur.objects.filter(etablissement=request.user.etablissement)
    
    # Préparer les données pour l'export
    data = []
    for user in users:
        data.append({
            'Nom d\'utilisateur': user.username,
            'Nom complet': user.get_full_name(),
            'Email': user.email,
            'Rôle': user.get_role_display(),
            'Possède permis': 'Oui' if user.possede_permis else 'Non',
            'N° permis': user.numero_permis or '',
            'Expiration permis': user.date_expiration_permis.strftime('%d/%m/%Y') if user.date_expiration_permis else '',
            'Statut': 'Actif' if user.is_active else 'Inactif',
            'Établissement': user.etablissement.nom if user.etablissement else 'Non assigné'
        })
    
    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Export Excel de la liste des utilisateurs",
    )
    
    # Générer le fichier Excel
    return export_to_excel(
        "Liste des Utilisateurs",
        data,
        f"liste_utilisateurs_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    )

@login_required
@user_passes_test(is_admin_or_superuser)
def user_list_pdf(request):
    """Vue pour générer un PDF de la liste des utilisateurs (réservée aux administrateurs)"""
    if request.user.is_superuser:
        users = Utilisateur.objects.all().order_by('username')
        departement_nom = "TOUS DÉPARTEMENTS"
    else:
        users = Utilisateur.objects.filter(etablissement=request.user.etablissement).order_by('username')
        departement_nom = request.user.etablissement.nom if request.user.etablissement else "Non assigné"

    # Tracer l'action
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Exportation PDF de la liste des utilisateurs",
    )

    logo_path = os.path.join('static', 'images', 'logo_minexx.png')
    context = {
        'users': users,
        'date_generation': timezone.now().strftime('%d/%m/%Y %H:%M'),
        'logo_path': logo_path,
        'departement_nom': departement_nom
    }
    pdf = render_to_pdf('core/pdf/user_list_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"liste_utilisateurs_{timezone.now().strftime('%Y%m%d')}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Une erreur s'est produite lors de la génération du PDF.")

@login_required
@user_passes_test(is_admin_or_superuser)
def vehicule_list_excel(request):
    """Vue pour exporter la liste des véhicules en Excel"""
    if request.user.is_superuser:
        vehicules = Vehicule.objects.all().order_by('immatriculation')
    else:
        vehicules = Vehicule.objects.filter(etablissement=request.user.etablissement).order_by('immatriculation')

    # Création du classeur Excel
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Véhicules')

    # En-têtes
    headers = [
        'Immatriculation', 'Marque', 'Modèle', 'Couleur',
        'Numéro de châssis', 'Numéro de moteur', 'Carte rose',
        'Pneu AG', 'Pneu AD', 'Pneu ARG', 'Pneu ARD', 'Pneu secours',
        'Km début', 'Km actuel',
        'Date assurance', 'Date contrôle technique', 'Date vignette', 'Date stationnement',
    ]
    for col_num, header in enumerate(headers):
        ws.write(0, col_num, header)

    # Données
    for row_num, v in enumerate(vehicules, start=1):
        ws.write(row_num, 0, v.immatriculation)
        ws.write(row_num, 1, v.marque)
        ws.write(row_num, 2, v.modele)
        ws.write(row_num, 3, v.couleur)
        ws.write(row_num, 4, v.numero_chassis or '')
        ws.write(row_num, 5, v.numero_moteur or '')
        ws.write(row_num, 6, v.numero_carte_rose or '')
        ws.write(row_num, 7, v.numero_pneu_avant_gauche or '')
        ws.write(row_num, 8, v.numero_pneu_avant_droit or '')
        ws.write(row_num, 9, v.numero_pneu_arriere_gauche or '')
        ws.write(row_num, 10, v.numero_pneu_arriere_droit or '')
        ws.write(row_num, 11, v.numero_pneu_secours or '')
        ws.write(row_num, 12, v.kilometrage_debut if v.kilometrage_debut is not None else '')
        ws.write(row_num, 13, v.kilometrage_actuel if v.kilometrage_actuel is not None else '')
        ws.write(row_num, 14, v.date_expiration_assurance.strftime('%d/%m/%Y') if v.date_expiration_assurance else '')
        ws.write(row_num, 15, v.date_expiration_controle_technique.strftime('%d/%m/%Y') if v.date_expiration_controle_technique else '')
        ws.write(row_num, 16, v.date_expiration_vignette.strftime('%d/%m/%Y') if v.date_expiration_vignette else '')
        ws.write(row_num, 17, v.date_expiration_stationnement.strftime('%d/%m/%Y') if v.date_expiration_stationnement else '')

    # Préparer la réponse
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="vehicules.xls"'
    wb.save(response)
    return response

@login_required
@user_passes_test(is_admin_or_superuser)
def course_create(request):
    """Vue pour créer une nouvelle course (réservée aux administrateurs)"""
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, user=request.user, createur=request.user)
        if form.is_valid():
            course = form.save(commit=False)
            if course.vehicule and course.vehicule.etablissement:
                course.etablissement = course.vehicule.etablissement
            else:
                course.etablissement = request.user.etablissement
            
            # Mise à jour du kilométrage du véhicule avec le kilométrage de fin de mission
            if course.kilometrage_fin is not None and course.vehicule and course.vehicule.kilometrage_actuel < course.kilometrage_fin:
                course.vehicule.kilometrage_actuel = course.kilometrage_fin
                course.vehicule.save(update_fields=["kilometrage_actuel"])
                messages.info(request, f"Le kilométrage du véhicule {course.vehicule.immatriculation} a été mis à jour à {course.vehicule.kilometrage_actuel} km suite à la mission.")

            course.save()
            
            # Tracer l'action
            ActionTraceur.objects.create(
                utilisateur=request.user,
                action=f"Création de la course {course.id}",
                details=f"Destination: {course.destination}, Date souhaitée: {course.date_souhaitee}"
            )
            
            messages.success(request, f"La course {course.id} a été créée avec succès.")
            return redirect('course_list')
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Erreur dans le champ {field}: {error}")
    else:
        initial = {}
        vehicule_id = request.GET.get('vehicule_id') # Vérifier si un ID de véhicule est passé dans l'URL
        if vehicule_id:
            try:
                vehicule = Vehicule.objects.get(pk=vehicule_id)
                # Utiliser la fonction pour obtenir le dernier kilométrage connu
                initial['kilometrage_debut'] = get_latest_vehicle_kilometrage(vehicule)
                initial['vehicule'] = vehicule_id # Pré-remplir le champ véhicule
            except Vehicule.DoesNotExist:
                messages.warning(request, "Le véhicule spécifié n'existe pas.")
        
        form = CourseForm(user=request.user, createur=request.user, initial=initial)
    
    return render(request, 'core/course_form.html', {'form': form, 'title': 'Créer une course', 'mode': 'create'})

@login_required
@require_POST
def send_message(request):
    """
    Envoie un message à un utilisateur.
    
    Args:
        request: La requête HTTP contenant recipient_id et content
        
    Returns:
        JsonResponse: Réponse JSON indiquant le succès ou l'échec de l'envoi
    """
    try:
        # Récupération des données de la requête
        recipient_id = request.POST.get('recipient_id')
        content = (request.POST.get('content') or '').strip()
        
        # Validation des données
        if not recipient_id or not content:
            return JsonResponse(
                {'error': 'Les champs destinataire et contenu sont obligatoires.'}, 
                status=400
            )
            
        if len(content) > 1000:  # Limite arbitraire de 1000 caractères
            return JsonResponse(
                {'error': 'Le message ne peut pas dépasser 1000 caractères.'}, 
                status=400
            )
        
        # Récupération du destinataire
        User = get_user_model()
        try:
            recipient = User.objects.get(id=recipient_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse(
                {'error': 'Destinataire introuvable ou inactif.'}, 
                status=404
            )
        
        # Création et enregistrement du message
        message = Message.objects.create(
            sender=request.user, 
            recipient=recipient, 
            content=content
        )
        
        # Journalisation pour le débogage
        print(f"Message envoyé de {request.user} à {recipient} : {content[:50]}...")
        
        return JsonResponse({
            'success': True, 
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat()
        })
        
    except Exception as e:
        # Journalisation de l'erreur
        print(f"Erreur lors de l'envoi du message : {str(e)}")
        return JsonResponse(
            {'error': 'Une erreur est survenue lors de l\'envoi du message.'}, 
            status=500
        )

@login_required
@require_GET
def get_messages(request):
    correspondent_id = request.GET.get('correspondent_id')
    if not correspondent_id:
        return JsonResponse({'error': 'Correspondant manquant.'}, status=400)
    User = get_user_model()
    try:
        correspondent = User.objects.get(id=correspondent_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Correspondant introuvable.'}, status=404)
    messages = Message.objects.filter(
        (models.Q(sender=request.user) & models.Q(recipient=correspondent)) |
        (models.Q(sender=correspondent) & models.Q(recipient=request.user)) |
        (models.Q(sender__isnull=True, recipient=request.user, is_system_message=True))  # Inclure les messages système
    ).order_by('timestamp')
    
    messages_data = []
    for m in messages:
        # Gestion de l'expéditeur pour les messages système
        sender_name = 'Système' if m.is_system_message else (m.sender.get_full_name() or m.sender.username)
        
        # Gestion du destinataire
        recipient_name = m.recipient.get_full_name() or m.recipient.username
        
        # Déterminer si le message a été envoyé par l'utilisateur courant
        sent_by_me = m.sender == request.user if m.sender else False
        
        # Statut de lecture (uniquement pour les messages envoyés par l'utilisateur)
        read_status = ''
        if m.sender == request.user:
            read_status = 'lu' if m.is_read else 'non lu'
            
        messages_data.append({
            'id': m.id,
            'sender': sender_name,
            'recipient': recipient_name,
            'content': m.content,
            'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M'),
            'is_read': m.is_read,
            'sent_by_me': sent_by_me,
            'read_status': read_status,
            'is_system_message': m.is_system_message
        })
    # Marquer comme lus les messages reçus non lus
    Message.objects.filter(sender=correspondent, recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'messages': messages_data})

@login_required
@require_GET
def get_users(request):
    User = get_user_model()
    users = User.objects.exclude(id=request.user.id)
    users_data = []
    
    # Ajouter l'utilisateur système pour les messages système
    system_user = get_system_user()
    if system_user:
        unread_system = Message.objects.filter(
            sender=system_user, 
            recipient=request.user, 
            is_read=False,
            is_system_message=True
        ).count()
        
        users_data.append({
            'id': system_user.id,
            'name': 'Système',
            'role': 'Système',
            'unread_count': unread_system,
            'is_system': True
        })
    
    # Ajouter les autres utilisateurs
    for u in users:
        unread_count = Message.objects.filter(
            sender=u, 
            recipient=request.user, 
            is_read=False
        ).count()
        
        users_data.append({
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'role': u.get_role_display() if hasattr(u, 'get_role_display') else '',
            'unread_count': unread_count,
            'is_system': False
        })
    return JsonResponse({'users': users_data})

@login_required
@require_GET
def get_unread_messages_status(request):
    unread = Message.objects.filter(recipient=request.user, is_read=False).order_by('-timestamp')
    count = unread.count()
    last_msg = unread.first()
    last_data = None
    if last_msg:
        content_full = last_msg.content or ''
        sender_name = 'Système' if last_msg.is_system_message else (
            (last_msg.sender.get_full_name() or last_msg.sender.username) if last_msg.sender else 'Système'
        )
        urgent_keywords = (
            'nouvelle demande', 'nouvelle course', 'nouvelle mission',
            'course assignée', 'mission assignée', 'a été validée', 'a été refusée',
        )
        content_lower = content_full.lower()
        is_urgent = bool(last_msg.is_system_message) or any(k in content_lower for k in urgent_keywords)
        last_data = {
            'id': last_msg.id,
            'sender': sender_name,
            'content': content_full[:60] + ('...' if len(content_full) > 60 else ''),
            'content_full': content_full[:280],
            'timestamp': last_msg.timestamp.strftime('%Y-%m-%d %H:%M'),
            'is_system': bool(last_msg.is_system_message),
            'urgent': is_urgent,
        }
    return JsonResponse({'unread_count': count, 'last_unread': last_data})


@login_required
@require_GET
def get_alert_events(request):
    """
    Poll des alertes sonnerie : nouvelles courses (dispatch), assignations (chauffeur),
    messages non lus. Compatible modèle client-bar (ring until ack).
    """
    from datetime import timedelta
    user = request.user
    alerts = []
    since = timezone.now() - timedelta(minutes=30)

    # Messages non lus récents
    unread_msgs = Message.objects.filter(
        recipient=user, is_read=False, timestamp__gte=since
    ).order_by('-timestamp')[:5]
    for msg in unread_msgs:
        content = msg.content or ''
        content_lower = content.lower()
        urgent = bool(msg.is_system_message) or any(
            k in content_lower for k in (
                'nouvelle demande', 'nouvelle course', 'nouvelle mission',
                'course assignée', 'mission assignée', 'mission planifiée',
                'a été validée', 'a été refusée', 'demande refusée',
            )
        )
        alerts.append({
            'id': f'msg-{msg.id}',
            'type': 'course' if urgent else 'chat',
            'title': 'Alerte course' if urgent else 'Nouveau message',
            'body': content[:160],
            'urgent': urgent,
            'url': '/',
        })

    # Dispatch / admin : demandes en attente récentes
    if user.role in ('dispatch', 'admin') or user.is_superuser:
        qs = Course.objects.filter(statut='en_attente', date_demande__gte=since)
        if getattr(user, 'etablissement_id', None) and not user.is_superuser and user.role != 'admin':
            qs = qs.filter(etablissement_id=user.etablissement_id)
        for course in qs.order_by('-date_demande')[:10]:
            alerts.append({
                'id': f'course-pending-{course.id}',
                'type': 'course_new',
                'title': f'Nouvelle demande #{course.id}',
                'body': f'{course.point_embarquement} → {course.destination}',
                'urgent': True,
                'url': f'/dispatch/demande/{course.id}/traiter/',
            })

    # Chauffeur : courses récemment validées / en cours
    if user.role == 'chauffeur':
        assigned_qs = Course.objects.filter(
            chauffeur=user,
            statut__in=('validee', 'en_cours'),
        ).filter(
            Q(date_validation__gte=since) | Q(date_validation__isnull=True, date_demande__gte=since)
        ).order_by('-date_validation', '-date_demande')[:10]
        for course in assigned_qs:
            alerts.append({
                'id': f'course-assigned-{course.id}',
                'type': 'course_assigned',
                'title': f'Course assignée #{course.id}',
                'body': f'{course.point_embarquement} → {course.destination}',
                'urgent': True,
                'url': '/chauffeur/',
            })

    # Demandeur (client) : validation récente de ses demandes
    if user.role == 'demandeur':
        for course in Course.objects.filter(
            demandeur=user,
            statut__in=('validee', 'en_cours'),
            date_validation__gte=since,
        ).order_by('-date_validation')[:10]:
            alerts.append({
                'id': f'course-validated-{course.id}',
                'type': 'course_client',
                'title': f'Demande validée #{course.id}',
                'body': f'{course.point_embarquement} → {course.destination}',
                'urgent': True,
                'url': f'/demandeur/demande/{course.id}/',
            })
        # Refus : couvert par messages système (is_system_message) ci-dessus

    # Dédupliquer par id
    seen = set()
    unique = []
    for a in alerts:
        if a['id'] in seen:
            continue
        seen.add(a['id'])
        unique.append(a)

    return JsonResponse({
        'alerts': unique,
        'has_urgent': any(a.get('urgent') for a in unique),
    })



def user_is_dispatch_or_admin(user):
    return user.is_authenticated and (user.role in ['dispatch', 'admin'] or user.is_superuser)

@login_required
@user_passes_test(user_is_dispatch_or_admin)
def vehicule_change_etablissement(request, vehicule_id):
    vehicule = get_object_or_404(Vehicule, id=vehicule_id)
    if request.method == 'POST':
        form = VehiculeChangeEtablissementForm(request.POST, instance=vehicule)
        if form.is_valid():
            form.save()
            return redirect('vehicule_detail', pk=vehicule.id)
    else:
        form = VehiculeChangeEtablissementForm(instance=vehicule)
    return render(request, 'core/vehicule_change_etablissement.html', {'form': form, 'vehicule': vehicule}) 

@login_required
def configuration_view(request):
    return render(request, 'core/configuration.html') 

# Vues pour la gestion des départements/établissements
@require_departement_password
@login_required
@admin_required
def departement_list(request):
    """Liste des départements/établissements"""
    etablissements = Etablissement.objects.all().order_by('type', 'nom')
    context = {
        'etablissements': etablissements,
        'title': 'Gestion des Départements'
    }
    return render(request, 'core/departement_list.html', context)

@require_departement_password
@login_required
@admin_required
def departement_create(request):
    """Création d'un nouveau département/établissement"""
    if request.method == 'POST':
        form = EtablissementForm(request.POST)
        if form.is_valid():
            etablissement = form.save()
            messages.success(request, f'Département "{etablissement.nom}" créé avec succès.')
            return redirect('departement_list')
    else:
        form = EtablissementForm()
    
    context = {
        'form': form,
        'title': 'Créer un Département',
        'action': 'Créer'
    }
    return render(request, 'core/departement_form.html', context)

@require_departement_password
@login_required
@admin_required
def departement_detail(request, pk):
    """Détails d'un département/établissement"""
    etablissement = get_object_or_404(Etablissement, pk=pk)
    context = {
        'etablissement': etablissement,
        'title': f'Détails - {etablissement.nom}'
    }
    return render(request, 'core/departement_detail.html', context)

@require_departement_password
@login_required
@admin_required
def departement_edit(request, pk):
    """Modification d'un département/établissement"""
    etablissement = get_object_or_404(Etablissement, pk=pk)
    if request.method == 'POST':
        form = EtablissementForm(request.POST, instance=etablissement)
        if form.is_valid():
            form.save()
            messages.success(request, f'Département "{etablissement.nom}" modifié avec succès.')
            return redirect('departement_list')
    else:
        form = EtablissementForm(instance=etablissement)
    
    context = {
        'form': form,
        'etablissement': etablissement,
        'title': f'Modifier - {etablissement.nom}',
        'action': 'Modifier'
    }
    return render(request, 'core/departement_form.html', context)

@require_departement_password
@login_required
@admin_required
def departement_delete(request, pk):
    """Suppression d'un département/établissement"""
    etablissement = get_object_or_404(Etablissement, pk=pk)
    
    if request.method == 'POST':
        nom_etablissement = etablissement.nom
        
        # Vérifier s'il y a des utilisateurs associés
        utilisateurs_associes = etablissement.utilisateurs.count()
        
        if utilisateurs_associes > 0:
            messages.error(request, f'Impossible de supprimer le département "{nom_etablissement}". Il y a {utilisateurs_associes} utilisateur(s) associé(s).')
            return redirect('departement_list')
        
        # Vérifier s'il y a des départements enfants
        enfants_count = etablissement.enfants.count()
        if enfants_count > 0:
            messages.error(request, f'Impossible de supprimer le département "{nom_etablissement}". Il y a {enfants_count} département(s) enfant(s).')
            return redirect('departement_list')
        
        # Supprimer le département
        etablissement.delete()
        messages.success(request, f'Département "{nom_etablissement}" supprimé avec succès.')
        return redirect('departement_list')
    
    context = {
        'etablissement': etablissement,
        'title': f'Supprimer - {etablissement.nom}',
        'utilisateurs_associes': etablissement.utilisateurs.count(),
        'vehicules_associes': 0,  # Temporairement désactivé
        'enfants_count': etablissement.enfants.count()
    }
    return render(request, 'core/departement_delete.html', context)

def test_view(request):
    """Vue de test simple pour diagnostiquer les erreurs"""
    try:
        # Test de base de données
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_ok = cursor.fetchone()[0] == 1
    except Exception as e:
        db_ok = False
        db_error = str(e)
    
    # Test des modèles
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_count = User.objects.count()
        models_ok = True
    except Exception as e:
        models_ok = False
        models_error = str(e)
    
    context = {
        'db_ok': db_ok,
        'models_ok': models_ok,
        'db_error': locals().get('db_error', ''),
        'models_error': locals().get('models_error', ''),
        'user_count': locals().get('user_count', 0),
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
    }
    
    return render(request, 'core/test.html', context) 
