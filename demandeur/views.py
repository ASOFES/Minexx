from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from core.models import Course, ActionTraceur, Utilisateur, Message
from .forms import DemandeForm
from notifications.utils import notify_user, send_sms, send_whatsapp
import datetime
from django.http import HttpResponse
from django.template.loader import get_template, render_to_string
# from weasyprint import HTML  # Temporairement commenté pour le déploiement
import openpyxl
from openpyxl.styles import Font
import os
import base64
from django.contrib.staticfiles import finders
from django.core.mail import send_mail
import xlwt
from django.views.decorators.http import require_POST

@login_required
def dashboard(request):
    """Vue pour le tableau de bord du demandeur de missions"""
    # Récupérer les demandes de l'utilisateur connecté
    if request.user.role == 'admin' or request.user.is_superuser:
        # Pour les admins et superusers, montrer toutes les demandes où ils sont demandeur OU de leur établissement
        demandes = Course.objects.filter(
            Q(demandeur=request.user) | Q(etablissement=request.user.etablissement)
        ).order_by('-date_demande')
    else:
        # Pour les demandeurs normaux, montrer seulement leurs demandes
        demandes = Course.objects.filter(demandeur=request.user).order_by('-date_demande')
    
    # Filtres
    statut = request.GET.get('statut')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if statut:
        demandes = demandes.filter(statut=statut)
    
    if date_debut:
        date_debut = datetime.datetime.strptime(date_debut, '%Y-%m-%d').date()
        demandes = demandes.filter(date_demande__date__gte=date_debut)
    
    if date_fin:
        date_fin = datetime.datetime.strptime(date_fin, '%Y-%m-%d').date()
        demandes = demandes.filter(date_demande__date__lte=date_fin)
    
    # Pagination
    paginator = Paginator(demandes, 12)  # 12 demandes par page
    page_number = request.GET.get('page')
    demandes_page = paginator.get_page(page_number)
    
    # Statistiques
    if request.user.role == 'admin' or request.user.is_superuser:
        stats = {
            'total': Course.objects.count(),
            'en_attente': Course.objects.filter(statut='en_attente', demandeur__etablissement=request.user.etablissement).count() if not request.user.is_superuser else Course.objects.filter(statut='en_attente').count(),
            'validees': Course.objects.filter(statut='validee').count(),
            'refusees': Course.objects.filter(statut='refusee').count(),
        }
    else:
        stats = {
            'total': Course.objects.filter(demandeur=request.user).count(),
            'en_attente': Course.objects.filter(demandeur=request.user, statut='en_attente').count(),
            'validees': Course.objects.filter(demandeur=request.user, statut='validee').count(),
            'refusees': Course.objects.filter(demandeur=request.user, statut='refusee').count(),
        }
    
    context = {
        'demandes_page': demandes_page,
        'stats': stats,
        'user': request.user,
    }
    
    return render(request, 'demandeur/dashboard.html', context)

@login_required
def nouvelle_demande(request):
    """Vue pour créer une nouvelle demande de mission"""
    if request.method == 'POST':
        form = DemandeForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.demandeur = request.user
            demande.statut = 'en_attente'
            demande.etablissement = request.user.etablissement
            demande.save()
            
            # Créer une entrée dans l'historique des actions
            ActionTraceur.objects.create(
                utilisateur=request.user,
                action="Création de demande de mission",
                details=f"Demande #{demande.id} - {demande.point_embarquement} → {demande.destination}"
            )
            
            # Récupérer les administrateurs et les dispatchers
            admins_dispatchers = Utilisateur.objects.filter(
                Q(role='admin') | Q(role='dispatch'),
                is_active=True
            ).distinct()
            
            # Message de notification
            notification_title = f"Nouvelle demande de course #{demande.id}"
            notification_message = f"{request.user.get_full_name()} a créé une nouvelle demande de course de {demande.point_embarquement} à {demande.destination}."
            
            # Envoi des notifications à chaque admin/dispatcher
            for user in admins_dispatchers:
                # Notification interne
                notify_user(
                    user,
                    notification_title,
                    notification_message,
                    notification_type='all',
                    course=demande
                )
                
                # Envoi SMS/WhatsApp (désactivé pour le moment)
                if user.telephone:
                    send_sms(user.telephone, notification_message)
                    send_whatsapp(user.telephone, notification_message)
            
            # Récupérer l'utilisateur système pour les messages système (jamais de superuser auto)
            system_user, _created = Utilisateur.objects.get_or_create(
                username='system',
                defaults={
                    'email': 'system@minexx.local',
                    'role': 'admin',
                    'is_staff': False,
                    'is_superuser': False,
                    'first_name': 'Système',
                    'last_name': 'MINEXX',
                }
            )
            if _created:
                system_user.set_unusable_password()
                system_user.save(update_fields=['password'])
            
            # Créer un message pour chaque admin/dispatcher
            for user in admins_dispatchers:
                chat_message = f"""🚗 Nouvelle demande de course #{demande.id}
- 👤 Demandeur: {demande.demandeur.get_full_name()}
- 📅 Date souhaitée: {demande.date_souhaitee.strftime('%d/%m/%Y à %H:%M') if demande.date_souhaitee else 'Non spécifiée'}
- 🚩 Départ: {demande.point_embarquement}
- 🏁 Destination: {demande.destination}
- 👥 Nombre de passagers: {demande.nombre_passagers}
- 📝 Statut: En attente de validation"""
                
                # Créer le message dans le chat interne
                Message.objects.create(
                    sender=system_user,  # Utiliser l'utilisateur système comme expéditeur
                    recipient=user,
                    content=chat_message,
                    is_read=False,
                    is_system_message=True,
                )
            
            messages.success(request, 'Votre demande de mission a été créée avec succès et est en attente de validation.')
            return redirect('demandeur:detail_demande', demande.id)
    else:
        form = DemandeForm()
    
    return render(request, 'demandeur/nouvelle_demande.html', {'form': form})

@login_required
def detail_demande(request, demande_id):
    """Vue pour afficher les détails d'une demande de mission"""
    # Pour les admins et superusers, permettre l'accès à toutes les demandes
    if request.user.role == 'admin' or request.user.is_superuser:
        demande = get_object_or_404(Course, id=demande_id)
    else:
        demande = get_object_or_404(Course, id=demande_id, demandeur=request.user)
    
    # Récupérer l'historique des actions liées à cette demande
    historique = ActionTraceur.objects.filter(
        Q(details__icontains=f"Demande #{demande.id}") |
        Q(details__icontains=f"Course {demande.id}")
    ).order_by('-date_action')
    
    context = {
        'demande': demande,
        'historique': historique,
    }
    
    return render(request, 'demandeur/detail_demande.html', context)

@login_required
def modifier_demande(request, demande_id):
    """Vue pour modifier une demande de mission"""
    # Pour les admins et superusers, permettre l'accès à toutes les demandes
    if request.user.role == 'admin' or request.user.is_superuser:
        demande = get_object_or_404(Course, id=demande_id, statut='en_attente')
    else:
        demande = get_object_or_404(Course, id=demande_id, demandeur=request.user, statut='en_attente')
    
    if request.method == 'POST':
        form = DemandeForm(request.POST, instance=demande)
        if form.is_valid():
            form.save()
            
            # Créer une entrée dans l'historique des actions
            ActionTraceur.objects.create(
                utilisateur=request.user,
                action="Modification de demande de mission",
                details=f"Demande #{demande.id} - {demande.point_embarquement} → {demande.destination}"
            )
            
            messages.success(request, 'Votre demande de mission a été modifiée avec succès.')
            return redirect('demandeur:detail_demande', demande.id)
    else:
        form = DemandeForm(instance=demande)
    
    return render(request, 'demandeur/nouvelle_demande.html', {'form': form, 'demande': demande})

@login_required
def annuler_demande(request, demande_id):
    """Vue pour annuler une demande de mission"""
    # Pour les admins et superusers, permettre l'accès à toutes les demandes
    if request.user.role == 'admin' or request.user.is_superuser:
        demande = get_object_or_404(Course, id=demande_id, statut='en_attente')
    else:
        demande = get_object_or_404(Course, id=demande_id, demandeur=request.user, statut='en_attente')
    
    demande.statut = 'annulee'
    demande.save()
    
    # Créer une entrée dans l'historique des actions
    ActionTraceur.objects.create(
        utilisateur=request.user,
        action="Annulation de demande de mission",
        details=f"Demande #{demande.id} - {demande.point_embarquement} → {demande.destination}"
    )
    
    messages.success(request, 'Votre demande de mission a été annulée avec succès.')
    return redirect('demandeur:dashboard')

@login_required
def demande_pdf(request, demande_id):
    demande = get_object_or_404(Course, id=demande_id)
    template = get_template('demandeur/demande_pdf.html')
    html = template.render({
        'demande': demande,
        'request': request,
        'now': timezone.now()
    })

    pdf_bytes = HTML(string=html).write_pdf()
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="demande_{demande_id}.pdf"'
    return response

@login_required
def demande_excel(request, demande_id):
    demande = get_object_or_404(Course, id=demande_id)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Demande {demande.id}"

    # En-têtes
    ws['A1'] = "Champ"
    ws['B1'] = "Valeur"
    ws['A1'].font = ws['B1'].font = Font(bold=True)

    # Données
    data = [
        ("ID", demande.id),
        ("Date de demande", demande.date_demande.strftime("%d/%m/%Y %H:%M") if demande.date_demande else ""),
        ("Date souhaitée", demande.date_souhaitee.strftime("%d/%m/%Y %H:%M") if demande.date_souhaitee else ""),
        ("Demandeur", demande.demandeur.get_full_name() if demande.demandeur else ""),
        ("Département du demandeur", demande.demandeur.etablissement.nom if demande.demandeur and demande.demandeur.etablissement else "-"),
        ("Téléphone demandeur", demande.demandeur.telephone if demande.demandeur and demande.demandeur.telephone else "-"),
        ("Destination", demande.destination),
        ("Point d'embarquement", demande.point_embarquement),
        ("Motif", demande.motif),
        ("Nombre de passagers", demande.nombre_passagers),
        ("Statut", demande.get_statut_display()),
        ("Chauffeur", demande.chauffeur.get_full_name() if demande.chauffeur else "Non assigné"),
        ("Département du véhicule", demande.vehicule.etablissement.nom if demande.vehicule and demande.vehicule.etablissement else "-"),
        ("Véhicule", demande.vehicule.immatriculation if demande.vehicule else "Non assigné"),
        ("Marque véhicule", demande.vehicule.marque if demande.vehicule else "-"),
        ("Modèle véhicule", demande.vehicule.modele if demande.vehicule else "-"),
        ("Numéro de châssis", demande.vehicule.numero_chassis if demande.vehicule else "-"),
        ("Numéro de moteur", demande.vehicule.numero_moteur if demande.vehicule else "-"),
        ("Carte rose", demande.vehicule.numero_carte_rose if demande.vehicule else "-"),
        ("Km début véhicule", demande.vehicule.kilometrage_debut if demande.vehicule and demande.vehicule.kilometrage_debut is not None else "-"),
        ("Pneus", demande.vehicule.pneus_resume() if demande.vehicule else "-"),
        ("Kilométrage départ", demande.kilometrage_depart if demande.kilometrage_depart else "-"),
        ("Kilométrage fin", demande.kilometrage_fin if demande.kilometrage_fin else "-"),
        ("Distance parcourue", demande.distance_parcourue if demande.distance_parcourue else "-"),
        ("Date départ", demande.date_depart.strftime("%d/%m/%Y %H:%M") if demande.date_depart else ""),
        ("Date fin", demande.date_fin.strftime("%d/%m/%Y %H:%M") if demande.date_fin else ""),
        ("Dispatcher", demande.dispatcher.get_full_name() if demande.dispatcher else "-"),
        ("Date validation", demande.date_validation.strftime("%d/%m/%Y %H:%M") if demande.date_validation else ""),
    ]
    for i, (champ, valeur) in enumerate(data, start=2):
        ws[f'A{i}'] = champ
        ws[f'B{i}'] = valeur

    # Génération de la réponse
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=demande_{demande.id}.xlsx'
    wb.save(response)
    return response

@login_required
def demandes_pdf(request):
    # Récupérer les demandes selon le rôle
    if request.user.role == 'admin' or request.user.is_superuser:
        demandes = Course.objects.filter(etablissement=request.user.etablissement).order_by('-date_demande')
    else:
        demandes = Course.objects.filter(demandeur=request.user, etablissement=request.user.etablissement).order_by('-date_demande')

    # Utiliser finders pour localiser le logo dans les fichiers statiques
    logo_path = finders.find('images/logo_mamo.png')
    logo_data_uri = ''
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as image_file:
            logo_data_uri = "data:image/png;base64," + base64.b64encode(image_file.read()).decode('utf-8')

    template = get_template('demandeur/demandes_pdf.html')
    html = template.render({
        'demandes': demandes, 
        'user': request.user, 
        'logo_data_uri': logo_data_uri,
        'now': timezone.now(),
        'request': request
    })

    # Générer le PDF directement en mémoire
    pdf_bytes = HTML(string=html).write_pdf()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'filename="demandes.pdf"'
    return response

@login_required
def demandes_excel(request):
    # Récupérer les demandes selon le rôle
    if request.user.role == 'admin' or request.user.is_superuser:
        demandes = Course.objects.filter(etablissement=request.user.etablissement).order_by('-date_demande')
    else:
        demandes = Course.objects.filter(demandeur=request.user, etablissement=request.user.etablissement).order_by('-date_demande')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Demandes"

    # En-têtes
    headers = [
        "ID", "Date de demande", "Date souhaitée", "Demandeur", "Département du demandeur", "Téléphone demandeur",
        "Destination", "Point d'embarquement", "Motif", "Nombre de passagers", "Statut", "Chauffeur",
        "Département du véhicule", "Véhicule", "Marque véhicule", "Modèle véhicule",
        "Numéro de châssis", "Numéro de moteur", "Carte rose", "Km début véhicule", "Pneus",
        "Kilométrage départ", "Kilométrage fin", "Distance parcourue", "Date départ", "Date fin",
        "Dispatcher", "Date validation",
    ]
    for col, header in enumerate(headers, start=1):
        ws.cell(row=1, column=col, value=header).font = Font(bold=True)

    # Données
    for row, demande in enumerate(demandes, start=2):
        ws.cell(row=row, column=1, value=demande.id)
        ws.cell(row=row, column=2, value=demande.date_demande.strftime("%d/%m/%Y %H:%M") if demande.date_demande else "")
        ws.cell(row=row, column=3, value=demande.date_souhaitee.strftime("%d/%m/%Y %H:%M") if demande.date_souhaitee else "")
        ws.cell(row=row, column=4, value=demande.demandeur.get_full_name() if demande.demandeur else "")
        ws.cell(row=row, column=5, value=demande.demandeur.etablissement.nom if demande.demandeur and demande.demandeur.etablissement else "-")
        ws.cell(row=row, column=6, value=demande.demandeur.telephone if demande.demandeur and demande.demandeur.telephone else "-")
        ws.cell(row=row, column=7, value=demande.destination)
        ws.cell(row=row, column=8, value=demande.point_embarquement)
        ws.cell(row=row, column=9, value=demande.motif)
        ws.cell(row=row, column=10, value=demande.nombre_passagers)
        ws.cell(row=row, column=11, value=demande.get_statut_display())
        ws.cell(row=row, column=12, value=demande.chauffeur.get_full_name() if demande.chauffeur else "Non assigné")
        ws.cell(row=row, column=13, value=demande.vehicule.etablissement.nom if demande.vehicule and demande.vehicule.etablissement else "-")
        ws.cell(row=row, column=14, value=demande.vehicule.immatriculation if demande.vehicule else "Non assigné")
        ws.cell(row=row, column=15, value=demande.vehicule.marque if demande.vehicule else "-")
        ws.cell(row=row, column=16, value=demande.vehicule.modele if demande.vehicule else "-")
        ws.cell(row=row, column=17, value=demande.vehicule.numero_chassis if demande.vehicule else "-")
        ws.cell(row=row, column=18, value=demande.vehicule.numero_moteur if demande.vehicule else "-")
        ws.cell(row=row, column=19, value=demande.vehicule.numero_carte_rose if demande.vehicule else "-")
        ws.cell(row=row, column=20, value=demande.vehicule.kilometrage_debut if demande.vehicule and demande.vehicule.kilometrage_debut is not None else "-")
        ws.cell(row=row, column=21, value=demande.vehicule.pneus_resume() if demande.vehicule else "-")
        ws.cell(row=row, column=22, value=demande.kilometrage_depart if demande.kilometrage_depart else "-")
        ws.cell(row=row, column=23, value=demande.kilometrage_fin if demande.kilometrage_fin else "-")
        ws.cell(row=row, column=24, value=demande.distance_parcourue if demande.distance_parcourue else "-")
        ws.cell(row=row, column=25, value=demande.date_depart.strftime("%d/%m/%Y %H:%M") if demande.date_depart else "")
        ws.cell(row=row, column=26, value=demande.date_fin.strftime("%d/%m/%Y %H:%M") if demande.date_fin else "")
        ws.cell(row=row, column=27, value=demande.dispatcher.get_full_name() if demande.dispatcher else "-")
        ws.cell(row=row, column=28, value=demande.date_validation.strftime("%d/%m/%Y %H:%M") if demande.date_validation else "")

    # Génération de la réponse
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=demandes.xlsx'
    wb.save(response)
    return response

@login_required
@require_POST
def notifier_chauffeurs(request):
    chauffeurs = Utilisateur.objects.filter(role='chauffeur', is_active=True)
    emails = [c.email for c in chauffeurs if c.email]
    # Notification interne (message Django)
    for c in chauffeurs:
        # Ici, tu peux créer un objet Message ou Notification si tu as un modèle dédié
        pass
    # Notification externe (email)
    if emails:
        send_mail(
            'Notification MAMO',
            'Vous avez une nouvelle notification sur la plateforme MAMO.',
            'no-reply@mamo.com',
            emails,
            fail_silently=True
        )
    messages.success(request, "Tous les chauffeurs ont été notifiés (interne et email si disponible).")
    return redirect('demandeur:dashboard')

@login_required
def export_courses_jour_pdf(request):
    today = timezone.localdate()
    courses = Course.objects.filter(date_souhaitee__date=today)
    
    # Préparer le contexte avec les données nécessaires
    context = {
        'courses': courses, 
        'date': today,
        'now': timezone.now(),
        'user': request.user
    }
    
    # Utiliser render_to_pdf qui inclut automatiquement le logo
    from core.utils import render_to_pdf
    return render_to_pdf('demandeur/courses_jour_pdf.html', context, f'courses_{today}.pdf')

@login_required
def export_courses_jour_excel(request):
    today = timezone.localdate()
    courses = Course.objects.filter(date_souhaitee__date=today)
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="courses_{today}.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Courses du jour')
    row_num = 0
    columns = ['ID', 'Demandeur', 'Départ', 'Destination', 'Chauffeur', 'Véhicule', 'Statut', 'Date souhaitée']
    for col_num, column_title in enumerate(columns):
        ws.write(row_num, col_num, column_title)
    for course in courses:
        row_num += 1
        ws.write(row_num, 0, course.id)
        ws.write(row_num, 1, str(course.demandeur))
        ws.write(row_num, 2, course.point_embarquement)
        ws.write(row_num, 3, course.destination)
        ws.write(row_num, 4, str(course.chauffeur) if course.chauffeur else '-')
        ws.write(row_num, 5, str(course.vehicule) if course.vehicule else '-')
        ws.write(row_num, 6, course.get_statut_display())
        ws.write(row_num, 7, course.date_souhaitee.strftime('%d/%m/%Y %H:%M') if course.date_souhaitee else '-')
    wb.save(response)
    return response
