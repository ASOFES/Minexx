from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
# from twilio.rest import Client  # Commenté pour le déploiement
import json
from pywebpush import webpush, WebPushException
from .models import PushSubscription

def notify_user(user, message, level=messages.INFO, extra_tags='', subject=None, email_template=None, **kwargs):
    """
    Send a notification to a user.
    
    Args:
        user: The user to notify
        message: The message to display
        level: Message level (e.g., messages.INFO, messages.SUCCESS, etc.)
        extra_tags: Extra tags to add to the message
        subject: Email subject (if sending email)
        email_template: Email template to use (if sending email)
        **kwargs: Additional context for the email template
    """
    # Store message in the Django messages framework
    if hasattr(user, '_message_set'):
        user._message_set.create(message=message, level=level, extra_tags=extra_tags)
    
    # Send email if email is provided and settings allow it
    if user.email and hasattr(settings, 'SEND_EMAILS') and settings.SEND_EMAILS and subject:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
            html_message=email_template.format(message=message, **kwargs) if email_template else None
        )

def send_sms(phone_number, message):
    """
    Envoie un SMS via l'API Twilio.
    
    Args:
        phone_number (str): Numéro de téléphone du destinataire (format international: +243XXXXXXXXX)
        message (str): Contenu du message à envoyer
        
    Returns:
        bool: True si l'envoi a réussi, False sinon
    """
    # Fonction commentée pour le déploiement - Twilio non disponible
    return False
    
    # import logging
    # logger = logging.getLogger('notifications')
    
    # # Vérifier que le numéro de téléphone est valide
    # if not phone_number or not isinstance(phone_number, str) or not phone_number.strip():
    #     logger.error("Numéro de téléphone invalide pour l'envoi de SMS")
    #     return False
        
    # # Nettoyer le numéro de téléphone (supprimer les espaces et caractères spéciaux)
    # phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # # Vérifier que le message n'est pas vide
    # if not message or not message.strip():
    #     logger.error("Le message SMS ne peut pas être vide")
    #     return False
        
    # # Vérifier que les identifiants Twilio sont configurés
    # if not all([
    #     hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID,
    #     hasattr(settings, 'TWILIO_AUTH_TOKEN') and settings.TWILIO_AUTH_TOKEN,
    #     hasattr(settings, 'TWILIO_PHONE_NUMBER') and settings.TWILIO_PHONE_NUMBER
    # ]):
    #     logger.error("Configuration Twilio incomplète. Vérifiez les variables d'environnement.")
    #     return False
    
    # try:
    #     # Initialiser le client Twilio
    #     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
    #     # Envoyer le SMS
    #     response = client.messages.create(
    #         body=message,
    #         from_=settings.TWILIO_PHONE_NUMBER,
    #         to=phone_number
    #     )
        
    #         # Journaliser le succès
    #         logger.info(f"SMS envoyé avec succès à {phone_number}. SID: {response.sid}")
    #         return True
        
    # except Exception as e:
    #     # Journaliser l'erreur
    #     error_msg = f"Erreur lors de l'envoi du SMS à {phone_number}: {str(e)}"
    #     logger.error(error_msg, exc_info=True)
    #         return False

def send_whatsapp(phone_number, message):
    """
    Envoie un message WhatsApp via l'API Twilio.
    
    Args:
        phone_number (str): Numéro de téléphone du destinataire (format international: +243XXXXXXXXX)
        message (str): Contenu du message à envoyer
        
    Returns:
        bool: True si l'envoi a réussi, False sinon
    """
    # Fonction commentée pour le déploiement - Twilio non disponible
    return False
    
    # import logging
    # logger = logging.getLogger('notifications')
    
    # # Vérifier que le numéro de téléphone est valide
    # if not phone_number or not isinstance(phone_number, str) or not phone_number.strip():
    #     logger.error("Numéro de téléphone invalide pour l'envoi de WhatsApp")
    #     return False
        
    # # Nettoyer le numéro de téléphone (supprimer les espaces et caractères spéciaux)
    # phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # # Vérifier que le message n'est pas vide
    # if not message or not message.strip():
    #     logger.error("Le message WhatsApp ne peut pas être vide")
    #     return False
        
    # # Vérifier que les identifiants Twilio sont configurés
    # if not all([
    #     hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID,
    #     hasattr(settings, 'TWILIO_AUTH_TOKEN') and settings.TWILIO_AUTH_TOKEN,
    #     hasattr(settings, 'TWILIO_WHATSAPP_NUMBER') and settings.TWILIO_WHATSAPP_NUMBER
    # ]):
    #     logger.error("Configuration Twilio WhatsApp incomplète. Vérifiez les variables d'environnement.")
    #     return False
    
    # try:
    #     # Initialiser le client Twilio
    #     client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
    #     # Formater les numéros pour WhatsApp
    #     from_whatsapp = f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}"
    #     to_whatsapp = f"whatsapp:{phone_number}"
        
    #     # Envoyer le message WhatsApp
    #     response = client.messages.create(
    #         body=message,
    #         from_=from_whatsapp,
    #         to=to_whatsapp
    #     )
        
    #         # Journaliser le succès
    #         logger.info(f"Message WhatsApp envoyé avec succès à {phone_number}. SID: {response.sid}")
    #         return True
        
    # except Exception as e:
    #     # Journaliser l'erreur
    #     error_msg = f"Erreur lors de l'envoi du message WhatsApp à {phone_number}: {str(e)}"
    #     logger.error(error_msg, exc_info=True)
    #         return False

def notify_course_participants(participants, message, **kwargs):
    """
    Send a notification to multiple course participants.
    
    Args:
        participants: A queryset of users to notify
        message: The message to send
        **kwargs: Additional arguments to pass to notify_user
    """
    for participant in participants:
        notify_user(participant, message, **kwargs)

def notify_multiple_users(users, message, **kwargs):
    """
    Send a notification to multiple users.
    
    Args:
        users: A queryset or list of users to notify
        message: The message to send
        **kwargs: Additional arguments to pass to notify_user
    """
    for user in users:
        notify_user(user, message, **kwargs)

def send_test_push_notification(user, title="Test notification", body="Ceci est un test de notification push.", url="/"):
    try:
        sub = PushSubscription.objects.get(user=user)
        subscription_info = sub.subscription_info
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/static/images/logo_minexx.png",
            "url": url
        })
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": "mailto:admin@asofes.com"}
        )
        return True
    except PushSubscription.DoesNotExist:
        return False
    except WebPushException as ex:
        print(f"Erreur WebPush: {ex}")
        return False
