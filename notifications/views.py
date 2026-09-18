from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from core.models import Vehicule, Message, Utilisateur
from django.utils import timezone
from datetime import timedelta
from .models import DocumentNotification, EntretienNotification, PushSubscription, Notification
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views import View
import json
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

def get_system_user():
    """Récupère l'utilisateur système pour les notifications"""
    return Utilisateur.objects.filter(username='system').first() or Utilisateur.objects.filter(is_superuser=True).first()

def check_document_notifications():
    """Vérifie les documents expirés ou sur le point d'expirer"""
    notifications = []
    today = timezone.now().date()
    
    # Vérifier les documents expirés ou sur le point d'expirer
    for vehicule in Vehicule.objects.all():
        # Vérifier l'assurance
        if vehicule.date_expiration_assurance:
            jours_restants = (vehicule.date_expiration_assurance - today).days
            if jours_restants <= 30:  # Alerte 30 jours avant l'expiration
                notifications.append({
                    'vehicule': vehicule,
                    'type': 'assurance',
                    'date_expiration': vehicule.date_expiration_assurance,
                    'jours_restants': jours_restants,
                    'message': f"L'assurance du véhicule {vehicule.immatriculation} "
                              f"expire dans {jours_restants} jour(s)"
                })
        
        # Vérifier le contrôle technique
        if vehicule.date_expiration_controle_technique:
            jours_restants = (vehicule.date_expiration_controle_technique - today).days
            if jours_restants <= 30:  # Alerte 30 jours avant l'expiration
                notifications.append({
                    'vehicule': vehicule,
                    'type': 'controle_technique',
                    'date_expiration': vehicule.date_expiration_controle_technique,
                    'jours_restants': jours_restants,
                    'message': f"Le contrôle technique du véhicule {vehicule.immatriculation} "
                              f"expire dans {jours_restants} jour(s)"
                })
        
        # Vérifier la vignette
        if vehicule.date_expiration_vignette:
            jours_restants = (vehicule.date_expiration_vignette - today).days
            if jours_restants <= 30:  # Alerte 30 jours avant l'expiration
                notifications.append({
                    'vehicule': vehicule,
                    'type': 'vignette',
                    'date_expiration': vehicule.date_expiration_vignette,
                    'jours_restants': jours_restants,
                    'message': f"La vignette du véhicule {vehicule.immatriculation} "
                              f"expire dans {jours_restants} jour(s)"
                })
    
    return notifications

def check_entretien_notifications():
    """Vérifie les véhicules nécessitant un entretien"""
    notifications = []
    
    for vehicule in Vehicule.objects.all():
        if vehicule.kilometrage_actuel is None or vehicule.kilometrage_dernier_entretien is None:
            continue
            
        kilometres_parcourus = vehicule.kilometrage_actuel - vehicule.kilometrage_dernier_entretien
        kilometres_restants = max(0, 4500 - kilometres_parcourus)
        
        if kilometres_parcourus >= 4500:  # Entretien en retard
            notifications.append({
                'vehicule': vehicule,
                'type': 'entretien_en_retard',
                'kilometres_parcourus': kilometres_parcourus,
                'kilometres_restants': 0,
                'message': f"Le véhicule {vehicule.immatriculation} a dépassé de "
                          f"{kilometres_parcourus - 4500} km l'intervalle d'entretien"
            })
        elif kilometres_restants <= 500:  # Entretien proche
            notifications.append({
                'vehicule': vehicule,
                'type': 'entretien_proche',
                'kilometres_parcourus': kilometres_parcourus,
                'kilometres_restants': kilometres_restants,
                'message': f"Le véhicule {vehicule.immatriculation} nécessite un entretien "
                          f"dans {kilometres_restants} km"
            })
    
    return notifications

@login_required
def notification_status(request):
    """
    Vue pour vérifier le statut des notifications non lues et retourner les alertes métiers.
    """
    unread_count = 0
    notifications = []
    
    # Vérifier les notifications de documents
    doc_notifications = check_document_notifications()
    for notif in doc_notifications:
        if notif['jours_restants'] <= 30:  # Afficher uniquement les alertes à 30 jours ou moins
            notifications.append({
                'type': 'document',
                'subtype': notif['type'],
                'message': notif['message'],
                'vehicule': notif['vehicule'].immatriculation,
                'vehicule_id': notif['vehicule'].id,
                'date_expiration': notif['date_expiration'].isoformat(),
                'jours_restants': notif['jours_restants'],
                'priority': 'high' if notif['jours_restants'] <= 7 else 'medium',
                'url': f"/vehicules/{notif['vehicule'].id}/"
            })
            unread_count += 1
    
    # Vérifier les notifications d'entretien
    entretien_notifications = check_entretien_notifications()
    for notif in entretien_notifications:
        is_high_priority = notif['type'] == 'entretien_en_retard' or notif['kilometres_restants'] <= 100
        
        notifications.append({
            'type': 'entretien',
            'subtype': notif['type'],
            'message': notif['message'],
            'vehicule': notif['vehicule'].immatriculation,
            'vehicule_id': notif['vehicule'].id,
            'kilometres_parcourus': notif['kilometres_parcourus'],
            'kilometres_restants': notif['kilometres_restants'],
            'priority': 'high' if is_high_priority else 'medium',
            'url': f"/vehicules/{notif['vehicule'].id}/entretien/"
        })
        unread_count += 1
    
    # Marquer les notifications comme lues si nécessaire
    if 'mark_as_read' in request.GET and request.GET.get('mark_as_read') == 'true':
        # Ici, vous pourriez marquer les notifications comme lues dans la base de données
        pass
    
    return JsonResponse({
        'unread_count': unread_count,
        'has_unread': unread_count > 0,
        'notifications': notifications
    })

def send_document_notification(vehicule, document_type, date_expiration, jours_restants):
    """Envoie une notification pour un document sur le point d'expirer"""
    system_user = get_system_user()
    if not system_user:
        return
    
    # Créer un message système
    message = f"Le document {document_type} du véhicule {vehicule.immatriculation} "
    if jours_restants <= 0:
        message += f"a expiré le {date_expiration.strftime('%d/%m/%Y')}"
    else:
        message += f"expire dans {jours_restants} jour(s) (le {date_expiration.strftime('%d/%m/%Y')})"
    
    # Envoyer aux administrateurs et aux utilisateurs concernés
    admin_users = Utilisateur.objects.filter(Q(is_superuser=True) | Q(role='admin'))
    for user in admin_users.distinct():
        Message.objects.create(
            sender=system_user,
            recipient=user,
            content=message,
            is_system_message=True
        )

def send_entretien_notification(vehicule, kilometres_parcourus):
    """Envoie une notification pour un entretien nécessaire"""
    system_user = get_system_user()
    if not system_user:
        return
    
    # Créer un message système
    message = f"Le véhicule {vehicule.immatriculation} a parcouru {kilometres_parcourus} km "
    if kilometres_parcourus >= 4500:
        message += f"et a dépassé l'intervalle d'entretien de {kilometres_parcourus - 4500} km"
    else:
        message += f"et nécessitera un entretien dans {4500 - kilometres_parcourus} km"
    
    # Envoyer aux administrateurs et aux utilisateurs concernés
    admin_users = Utilisateur.objects.filter(Q(is_superuser=True) | Q(role='admin'))
    for user in admin_users.distinct():
        Message.objects.create(
            sender=system_user,
            recipient=user,
            content=message,
            is_system_message=True
        )

@method_decorator(csrf_exempt, name='dispatch')
class SaveSubscriptionView(View):
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'auth required'}, status=403)
        data = json.loads(request.body)
        # On sauvegarde l'abonnement (endpoint unique par user)
        sub, created = PushSubscription.objects.update_or_create(
            user=request.user,
            defaults={'subscription_info': data}
        )
        return JsonResponse({'status': 'ok'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
    data = [
        {
            "id": n.id,
            "message": n.message,
            "created_at": n.created_at,
            "is_read": n.is_read,
        }
        for n in notifications
    ]
    return Response(data)
