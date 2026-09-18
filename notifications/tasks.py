from django.utils import timezone
from datetime import timedelta
from .models import DocumentNotification, EntretienNotification, PermisNotification, Notification
from core.models import Vehicule, Message, Utilisateur
from django.db.models import Q


def check_documents_and_send_notifications():
    """
    Vérifie les documents de bord, permis chauffeurs et entretiens, et envoie des notifications.
    """
    try:
        today = timezone.now().date()
        system_user = get_system_user()

        if not system_user:
            error_msg = "Aucun utilisateur système trouvé pour envoyer les notifications"
            print(error_msg)
            return False, error_msg

        check_documents(today, system_user)
        check_permis(today, system_user)
        check_entretiens(today, system_user)

        return True, "Vérification des documents, permis et entretiens terminée avec succès"

    except Exception as e:
        error_msg = f"Erreur lors de la vérification des documents et entretiens: {e}"
        print(error_msg)
        return False, error_msg


def get_system_user():
    """Récupère l'utilisateur système pour les notifications."""
    try:
        system_user = Utilisateur.objects.filter(username='system').first()

        if not system_user:
            system_user = Utilisateur.objects.filter(is_superuser=True).first()

            if not system_user:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                system_user = User.objects.create_user(
                    username='system',
                    email='system@example.com',
                    password=User.objects.make_random_password(),
                    is_active=False
                )
                system_user.save()

        return system_user

    except Exception as e:
        print(f"Erreur lors de la récupération/création de l'utilisateur système: {e}")
        return None


def check_documents(today, system_user):
    """Vérifie les documents de bord et envoie des notifications si nécessaire."""
    try:
        for vehicule in Vehicule.objects.all():
            try:
                if vehicule.date_expiration_assurance:
                    jours_restants = (vehicule.date_expiration_assurance - today).days
                    if jours_restants <= 30:
                        send_document_notification(
                            vehicule=vehicule,
                            document_type='assurance',
                            date_expiration=vehicule.date_expiration_assurance,
                            jours_restants=jours_restants,
                            system_user=system_user
                        )

                if vehicule.date_expiration_controle_technique:
                    jours_restants = (vehicule.date_expiration_controle_technique - today).days
                    if jours_restants <= 30:
                        send_document_notification(
                            vehicule=vehicule,
                            document_type='contrôle technique',
                            date_expiration=vehicule.date_expiration_controle_technique,
                            jours_restants=jours_restants,
                            system_user=system_user
                        )

                if vehicule.date_expiration_vignette:
                    jours_restants = (vehicule.date_expiration_vignette - today).days
                    if jours_restants <= 30:
                        send_document_notification(
                            vehicule=vehicule,
                            document_type='vignette',
                            date_expiration=vehicule.date_expiration_vignette,
                            jours_restants=jours_restants,
                            system_user=system_user
                        )

            except Exception as e:
                print(f"Erreur lors de la vérification des documents pour le véhicule {vehicule.immatriculation}: {e}")
                continue

    except Exception as e:
        print(f"Erreur critique lors de la vérification des documents: {e}")
        raise


def check_permis(today, system_user):
    """Alerte 1 mois (30 jours) avant l'expiration du permis des chauffeurs."""
    chauffeurs = Utilisateur.objects.filter(
        role='chauffeur',
        is_active=True,
        possede_permis=True,
        date_expiration_permis__isnull=False,
    )
    for chauffeur in chauffeurs:
        try:
            jours_restants = (chauffeur.date_expiration_permis - today).days
            if jours_restants <= 30:
                send_permis_notification(
                    chauffeur=chauffeur,
                    date_expiration=chauffeur.date_expiration_permis,
                    jours_restants=jours_restants,
                    system_user=system_user,
                )
        except Exception as e:
            print(f"Erreur permis pour {chauffeur.username}: {e}")
            continue


def send_permis_notification(chauffeur, date_expiration, jours_restants, system_user):
    """Notifie le chauffeur et les admins de l'expiration du permis."""
    recent = PermisNotification.objects.filter(
        chauffeur=chauffeur,
        date_creation__gte=timezone.now() - timedelta(days=7),
    ).exists()
    if recent:
        print(f"Notification permis récente déjà envoyée pour {chauffeur.username}")
        return False

    nom = chauffeur.get_full_name() or chauffeur.username
    numero = chauffeur.numero_permis or '—'
    if jours_restants <= 0:
        message = (
            f"Le permis de conduire de {nom} (n° {numero}) "
            f"a expiré le {date_expiration.strftime('%d/%m/%Y')}."
        )
    else:
        message = (
            f"Le permis de conduire de {nom} (n° {numero}) "
            f"expire dans {jours_restants} jour(s) "
            f"(le {date_expiration.strftime('%d/%m/%Y')})."
        )

    recipients = list(
        Utilisateur.objects.filter(Q(is_superuser=True) | Q(role='admin')).distinct()
    )
    if chauffeur.etablissement_id:
        etab_admins = Utilisateur.objects.filter(
            role='admin',
            etablissement_id=chauffeur.etablissement_id,
            is_active=True,
        )
        for admin in etab_admins:
            if admin not in recipients:
                recipients.append(admin)
    if chauffeur not in recipients:
        recipients.append(chauffeur)

    for user in recipients:
        try:
            Message.objects.create(
                sender=system_user,
                recipient=user,
                content=message,
                is_system_message=True,
            )
            Notification.objects.create(user=user, message=message[:255])
        except Exception as e:
            print(f"Erreur envoi notif permis à {user.username}: {e}")

    PermisNotification.objects.create(
        chauffeur=chauffeur,
        date_expiration=date_expiration,
        is_active=True,
    )
    print(f"Notification permis enregistrée pour {chauffeur.username}")
    return True


def check_entretiens(today, system_user):
    """Vérifie les véhicules nécessitant un entretien et envoie des notifications."""
    try:
        for vehicule in Vehicule.objects.all():
            try:
                if vehicule.kilometrage_actuel is None or vehicule.kilometrage_dernier_entretien is None:
                    print(f"Données manquantes pour le véhicule {vehicule.immatriculation}: kilométrage actuel ou dernier entretien non renseigné")
                    continue

                kilometres_parcourus = vehicule.kilometrage_actuel - vehicule.kilometrage_dernier_entretien
                kilometres_restants = max(0, 4500 - kilometres_parcourus)

                if kilometres_parcourus >= 4500 or kilometres_restants <= 500:
                    print(f"Envoi d'une notification d'entretien pour le véhicule {vehicule.immatriculation} - {kilometres_parcourus} km parcourus")
                    send_entretien_notification(
                        vehicule=vehicule,
                        kilometres_parcourus=kilometres_parcourus,
                        kilometres_restants=kilometres_restants,
                        system_user=system_user
                    )

            except Exception as e:
                print(f"Erreur lors de la vérification de l'entretien pour le véhicule {vehicule.immatriculation}: {e}")
                continue

    except Exception as e:
        print(f"Erreur critique lors de la vérification des entretiens: {e}")
        raise


def send_document_notification(vehicule, document_type, date_expiration, jours_restants, system_user):
    """Envoie une notification pour un document sur le point d'expirer ou ayant expiré."""
    try:
        recent_notification = DocumentNotification.objects.filter(
            vehicule=vehicule,
            document_type=document_type,
            date_creation__gte=timezone.now() - timedelta(days=7)
        ).exists()

        if not recent_notification:
            message = f"Le document {document_type} du véhicule {vehicule.immatriculation} "
            if jours_restants <= 0:
                message += f"a expiré le {date_expiration.strftime('%d/%m/%Y')}"
            else:
                message += f"expire dans {jours_restants} jour(s) (le {date_expiration.strftime('%d/%m/%Y')})"

            admin_users = Utilisateur.objects.filter(Q(is_superuser=True) | Q(role='admin'))

            if not admin_users.exists():
                print("Aucun administrateur trouvé pour l'envoi des notifications")
                return False

            for user in admin_users.distinct():
                try:
                    Message.objects.create(
                        sender=system_user,
                        recipient=user,
                        content=message,
                        is_system_message=True
                    )
                    print(f"Notification envoyée à {user.username}: {message}")
                except Exception as e:
                    print(f"Erreur lors de l'envoi de la notification à {user.username}: {e}")

            try:
                DocumentNotification.objects.create(
                    vehicule=vehicule,
                    document_type=document_type,
                    date_expiration=date_expiration,
                    is_active=True
                )
                print(f"Notification enregistrée pour le véhicule {vehicule.immatriculation}, document: {document_type}")
                return True

            except Exception as e:
                print(f"Erreur lors de l'enregistrement de la notification: {e}")
                return False
        else:
            print(f"Une notification récente existe déjà pour ce document ({document_type}) du véhicule {vehicule.immatriculation}")
            return False

    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification pour le document {document_type} du véhicule {vehicule.immatriculation}: {e}")
        return False


def send_entretien_notification(vehicule, kilometres_parcourus, kilometres_restants, system_user):
    """Envoie une notification pour un entretien nécessaire."""
    try:
        recent_notification = EntretienNotification.objects.filter(
            vehicule=vehicule,
            date_creation__gte=timezone.now() - timedelta(days=7)
        ).exists()

        if not recent_notification:
            message = f"Le véhicule {vehicule.immatriculation} a parcouru {kilometres_parcourus} km "
            if kilometres_parcourus >= 4500:
                message += f"et a dépassé l'intervalle d'entretien de {kilometres_parcourus - 4500} km"
            else:
                message += f"et nécessitera un entretien dans {kilometres_restants} km"

            admin_users = Utilisateur.objects.filter(Q(is_superuser=True) | Q(role='admin'))

            if not admin_users.exists():
                print("Aucun administrateur trouvé pour l'envoi des notifications d'entretien")
                return False

            for user in admin_users.distinct():
                try:
                    Message.objects.create(
                        sender=system_user,
                        recipient=user,
                        content=message,
                        is_system_message=True
                    )
                    print(f"Notification d'entretien envoyée à {user.username}: {message}")
                except Exception as e:
                    print(f"Erreur lors de l'envoi de la notification d'entretien à {user.username}: {e}")

            try:
                EntretienNotification.objects.create(
                    vehicule=vehicule,
                    kilometrage_actuel=vehicule.kilometrage_actuel or 0,
                    kilometrage_prochain=(vehicule.kilometrage_dernier_entretien or 0) + 4500,
                    is_active=True
                )
                print(f"Notification d'entretien enregistrée pour le véhicule {vehicule.immatriculation}")
                return True

            except Exception as e:
                print(f"Erreur lors de l'enregistrement de la notification d'entretien: {e}")
                return False

        else:
            print(f"Une notification d'entretien récente existe déjà pour le véhicule {vehicule.immatriculation}")
            return False

    except Exception as e:
        print(f"Erreur lors de l'envoi de la notification d'entretien pour le véhicule {vehicule.immatriculation}: {e}")
        return False
