import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    
    def ready(self):
        """
        Méthode appelée au chargement de l'application Django.
        Permet de démarrer le planificateur de tâches et de charger les signaux.
        """
        # Ne pas charger pendant les tests ou lors des commandes de gestion
        is_testing = getattr(settings, 'TESTING', False)
        is_management_command = self._is_management_command()
        
        if is_testing or is_management_command:
            logger.info(f"Mode test ou commande de gestion - Planificateur non démarré (TESTING={is_testing}, is_management={is_management_command})")
            return
            
        try:
            # Importer et configurer les signaux
            from . import signals
            signals.setup_signals()
            logger.info("Signaux de notification chargés")
            
            # Démarrer le planificateur
            from .scheduler import start_scheduler
            logger.info("Démarrage du planificateur de tâches...")
            start_scheduler()
            logger.info("Planificateur de tâches démarré avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des notifications: {e}", exc_info=True)
    
    def _is_management_command(self):
        """
        Vérifie si l'application est en cours d'exécution via une commande de gestion.
        """
        import sys
        return len(sys.argv) > 1 and sys.argv[1] in [
            'runserver', 'migrate', 'makemigrations', 'collectstatic', 'test'
        ]
