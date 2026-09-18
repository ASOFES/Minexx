from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import Course, Utilisateur

logger = logging.getLogger(__name__)


def send_sms_notification(phone_number, message):
    """Log SMS (intégration fournisseur à brancher si besoin)."""
    logger.info(f"SMS envoyé à {phone_number}: {message}")


@receiver(post_save, sender=Course)
def check_maintenance_and_notify(sender, instance, created, **kwargs):
    if not instance.vehicule or instance.kilometrage_fin is None:
        return

    vehicule = instance.vehicule

    # Le km centralisé ne peut que progresser
    if instance.kilometrage_fin > (vehicule.kilometrage_actuel or 0):
        vehicule.kilometrage_actuel = instance.kilometrage_fin
        vehicule.save(update_fields=['kilometrage_actuel'])

    distance_depuis_dernier_entretien = (
        (vehicule.kilometrage_actuel or 0) - (vehicule.kilometrage_dernier_entretien or 0)
    )

    SEUIL_KM_ENTRETIEN = 4200
    if distance_depuis_dernier_entretien < SEUIL_KM_ENTRETIEN:
        return

    subject = f"Alerte Entretien Véhicule: {vehicule.immatriculation}"
    message = (
        f"Le véhicule {vehicule.immatriculation} ({vehicule.marque} {vehicule.modele}) "
        f"a parcouru {distance_depuis_dernier_entretien} km depuis le dernier entretien "
        f"({vehicule.kilometrage_dernier_entretien} km). "
        f"Un entretien est recommandé. Kilométrage actuel: {vehicule.kilometrage_actuel} km."
    )

    recipients_emails = []
    recipients_phone_numbers = []

    for admin in Utilisateur.objects.filter(role='admin', is_active=True):
        if admin.email:
            recipients_emails.append(admin.email)
        if admin.telephone:
            recipients_phone_numbers.append(admin.telephone)

    if vehicule.etablissement:
        for dispatcher in Utilisateur.objects.filter(
            role='dispatch',
            etablissement=vehicule.etablissement,
            is_active=True,
        ):
            if dispatcher.email and dispatcher.email not in recipients_emails:
                recipients_emails.append(dispatcher.email)
            if dispatcher.telephone and dispatcher.telephone not in recipients_phone_numbers:
                recipients_phone_numbers.append(dispatcher.telephone)

    if recipients_emails:
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipients_emails,
                fail_silently=False,
            )
            logger.info(f"Email de notification d'entretien envoyé à: {recipients_emails}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'entretien: {e}")

    for phone in recipients_phone_numbers:
        send_sms_notification(phone, message)

    # Ne PAS réinitialiser kilometrage_dernier_entretien ici :
    # seule une maintenance TERMINÉE met à jour cette référence.
    logger.info(
        f"Alerte entretien pour {vehicule.immatriculation}: "
        f"{distance_depuis_dernier_entretien} km depuis le dernier entretien."
    )
