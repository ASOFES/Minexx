"""
Signaux pour l'application notifications.
Permet de gérer les actions liées aux modèles de notification.
"""
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import DocumentNotification, EntretienNotification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=DocumentNotification)
def document_notification_post_save(sender, instance, created, **kwargs):
    """
    Signal déclenché après l'enregistrement d'une notification de document.
    """
    if created:
        logger.info(f"Nouvelle notification de document créée pour le véhicule {instance.vehicule.immatriculation} - Type: {instance.document_type}")
    else:
        logger.info(f"Notification de document mise à jour pour le véhicule {instance.vehicule.immatriculation} - Type: {instance.document_type}")

@receiver(post_save, sender=EntretienNotification)
def entretien_notification_post_save(sender, instance, created, **kwargs):
    """
    Signal déclenché après l'enregistrement d'une notification d'entretien.
    """
    if created:
        logger.info(f"Nouvelle notification d'entretien créée pour le véhicule {instance.vehicule.immatriculation} - Kilométrage: {instance.kilometrage_actuel}")
    else:
        logger.info(f"Notification d'entretien mise à jour pour le véhicule {instance.vehicule.immatriculation}")

@receiver(pre_save, sender=DocumentNotification)
def document_notification_pre_save(sender, instance, **kwargs):
    """
    Signal déclenché avant l'enregistrement d'une notification de document.
    Permet de valider les données avant sauvegarde.
    """
    if not instance.pk:  # Nouvelle instance
        # Vérifier si une notification similaire existe déjà
        existing = DocumentNotification.objects.filter(
            vehicule=instance.vehicule,
            document_type=instance.document_type,
            is_active=True
        ).exclude(pk=instance.pk).exists()
        
        if existing:
            logger.warning(f"Une notification active existe déjà pour ce document ({instance.document_type}) et ce véhicule ({instance.vehicule.immatriculation})")

@receiver(pre_save, sender=EntretienNotification)
def entretien_notification_pre_save(sender, instance, **kwargs):
    """
    Signal déclenché avant l'enregistrement d'une notification d'entretien.
    Permet de valider les données avant sauvegarde.
    """
    if not instance.pk:  # Nouvelle instance
        # Vérifier si une notification similaire existe déjà
        existing = EntretienNotification.objects.filter(
            vehicule=instance.vehicule,
            is_active=True
        ).exclude(pk=instance.pk).exists()
        
        if existing:
            logger.warning(f"Une notification d'entretien active existe déjà pour ce véhicule ({instance.vehicule.immatriculation})")

@receiver(post_delete, sender=DocumentNotification)
def document_notification_post_delete(sender, instance, **kwargs):
    """
    Signal déclenché après la suppression d'une notification de document.
    """
    logger.info(f"Notification de document supprimée pour le véhicule {instance.vehicule.immatriculation} - Type: {instance.document_type}")

@receiver(post_delete, sender=EntretienNotification)
def entretien_notification_post_delete(sender, instance, **kwargs):
    """
    Signal déclenché après la suppression d'une notification d'entretien.
    """
    logger.info(f"Notification d'entretien supprimée pour le véhicule {instance.vehicule.immatriculation}")

# Fonction pour connecter les signaux
def setup_signals():
    """Connecte les signaux aux modèles"""
    # Les signaux sont déjà connectés via les décorateurs @receiver
    pass
