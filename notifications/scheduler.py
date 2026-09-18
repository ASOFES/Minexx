import logging
import time
from django.utils import timezone
from .tasks import check_documents_and_send_notifications
import threading

logger = logging.getLogger(__name__)

class SchedulerThread(threading.Thread):
    """
    Un thread simple pour exécuter la vérification périodique des documents et entretiens.
    """
    def __init__(self):
        super().__init__()
        self.running = False
        self.daemon = True  # Le thread s'arrêtera lorsque le thread principal s'arrête
        
    def run(self):
        self.running = True
        logger.info("Démarrage du planificateur de tâches...")
        
        while self.running:
            try:
                now = timezone.now()
                
                # Vérifier si c'est 8h00 du matin
                if now.hour == 8 and now.minute == 0:
                    logger.info("Exécution de la vérification des documents et entretiens...")
                    check_documents_and_send_notifications()
                    
                    # Attendre 1 minute pour éviter les exécutions multiples
                    time.sleep(60)
                
                # Vérifier toutes les minutes
                time.sleep(30)  # Vérifier deux fois par minute pour plus de précision
                
            except Exception as e:
                logger.error(f"Erreur dans le planificateur: {e}")
                time.sleep(60)  # En cas d'erreur, attendre 1 minute avant de réessayer
    
    def stop(self):
        self.running = False

# Variable globale pour le thread du planificateur
scheduler_thread = None

def start_scheduler():
    """
    Démarre le planificateur de tâches dans un thread séparé.
    """
    global scheduler_thread
    
    # Vérifier si le planificateur est déjà en cours d'exécution
    if scheduler_thread and scheduler_thread.is_alive():
        logger.info("Le planificateur est déjà en cours d'exécution")
        return
    
    try:
        # Créer et démarrer le thread du planificateur
        scheduler_thread = SchedulerThread()
        scheduler_thread.start()
        logger.info("Planificateur démarré avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du planificateur: {e}")

def stop_scheduler():
    """
    Arrête le planificateur de tâches.
    """
    global scheduler_thread
    
    if scheduler_thread:
        logger.info("Arrêt du planificateur de tâches...")
        scheduler_thread.stop()
        scheduler_thread.join(timeout=5)  # Attendre jusqu'à 5 secondes que le thread s'arrête
        logger.info("Planificateur arrêté")
    else:
        logger.info("Aucun planificateur en cours d'exécution")
