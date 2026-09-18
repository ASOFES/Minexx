# Configuration Firebase pour le Backend Django

## 1. Installation des dépendances

```bash
pip install firebase-admin
```

## 2. Configuration Firebase Admin SDK

### 2.1 Télécharger la clé de service
1. Aller sur [Firebase Console](https://console.firebase.google.com/)
2. Sélectionner le projet `minexx-mobile-app`
3. Aller dans Paramètres > Comptes de service
4. Cliquer sur "Générer une nouvelle clé privée"
5. Télécharger le fichier JSON

### 2.2 Placer le fichier dans le projet
```bash
# Placer le fichier dans le dossier du projet Django
mv ~/Downloads/minexx-mobile-app-firebase-adminsdk-xxxxx.json ./firebase-service-account.json
```

### 2.3 Configuration dans settings.py
```python
# settings.py

import firebase_admin
from firebase_admin import credentials

# Configuration Firebase
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'firebase-service-account.json')
FIREBASE_DATABASE_URL = 'https://minexx-mobile-app-default-rtdb.firebaseio.com'

# Initialiser Firebase Admin SDK
if os.path.exists(FIREBASE_CREDENTIALS_PATH):
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DATABASE_URL
    })
```

## 3. Service de notifications Firebase

### 3.1 Créer le service
```python
# notifications/services.py

from firebase_admin import messaging
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class FirebaseNotificationService:
    @staticmethod
    def send_notification_to_user(user_id, title, body, data=None):
        """Envoyer une notification à un utilisateur spécifique"""
        try:
            # Récupérer le token FCM de l'utilisateur
            user = User.objects.get(id=user_id)
            if not user.fcm_token:
                logger.warning(f"Utilisateur {user_id} n'a pas de token FCM")
                return False
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=user.fcm_token,
            )
            
            response = messaging.send(message)
            logger.info(f"Notification envoyée à {user_id}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
            return False
    
    @staticmethod
    def send_notification_to_topic(topic, title, body, data=None):
        """Envoyer une notification à un topic"""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                topic=topic,
            )
            
            response = messaging.send(message)
            logger.info(f"Notification envoyée au topic {topic}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification au topic: {e}")
            return False
    
    @staticmethod
    def send_notification_to_role(role, title, body, data=None):
        """Envoyer une notification à tous les utilisateurs d'un rôle"""
        topic = f"role_{role}"
        return FirebaseNotificationService.send_notification_to_topic(topic, title, body, data)
    
    @staticmethod
    def send_notification_to_all(title, body, data=None):
        """Envoyer une notification à tous les utilisateurs"""
        return FirebaseNotificationService.send_notification_to_topic("general", title, body, data)
```

## 4. Modèle utilisateur avec token FCM

### 4.1 Ajouter le champ FCM token
```python
# core/models.py

class User(AbstractUser):
    # ... autres champs existants ...
    fcm_token = models.CharField(max_length=500, blank=True, null=True)
    fcm_token_updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # ... configuration existante ...
        pass
```

### 4.2 Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

## 5. API pour gérer les tokens FCM

### 5.1 Vue pour mettre à jour le token
```python
# core/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token(request):
    """Mettre à jour le token FCM de l'utilisateur"""
    try:
        token = request.data.get('fcm_token')
        if not token:
            return Response(
                {'error': 'Token FCM requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        request.user.fcm_token = token
        request.user.save()
        
        return Response({'message': 'Token FCM mis à jour'})
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

### 5.2 URL
```python
# core/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ... autres URLs ...
    path('api/update-fcm-token/', views.update_fcm_token, name='update_fcm_token'),
]
```

## 6. Exemples d'utilisation

### 6.1 Notification lors d'une nouvelle mission
```python
# chauffeur/views.py

from notifications.services import FirebaseNotificationService

def create_mission(request):
    # ... logique de création de mission ...
    
    # Envoyer notification au chauffeur assigné
    if mission.chauffeur:
        FirebaseNotificationService.send_notification_to_user(
            user_id=mission.chauffeur.id,
            title="Nouvelle mission assignée",
            body=f"Mission #{mission.id} vers {mission.destination}",
            data={
                'mission_id': str(mission.id),
                'type': 'new_mission'
            }
        )
```

### 6.2 Notification lors d'un changement de statut
```python
# chauffeur/views.py

def update_mission_status(request, mission_id):
    # ... logique de mise à jour ...
    
    # Notifier le dispatcher
    FirebaseNotificationService.send_notification_to_role(
        role='dispatch',
        title="Statut de mission mis à jour",
        body=f"Mission #{mission.id}: {mission.statut}",
        data={
            'mission_id': str(mission.id),
            'status': mission.statut,
            'type': 'status_update'
        }
    )
```

## 7. Gestion des erreurs et nettoyage

### 7.1 Nettoyer les tokens invalides
```python
# notifications/management/commands/cleanup_fcm_tokens.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User

class Command(BaseCommand):
    help = 'Nettoyer les tokens FCM anciens'
    
    def handle(self, *args, **options):
        # Supprimer les tokens plus anciens que 30 jours
        cutoff_date = timezone.now() - timedelta(days=30)
        
        users_to_clean = User.objects.filter(
            fcm_token_updated_at__lt=cutoff_date,
            fcm_token__isnull=False
        )
        
        count = users_to_clean.count()
        users_to_clean.update(fcm_token=None)
        
        self.stdout.write(
            self.style.SUCCESS(f'{count} tokens FCM nettoyés')
        )
```

## 8. Tests

### 8.1 Test d'envoi de notification
```python
# notifications/tests.py

from django.test import TestCase
from notifications.services import FirebaseNotificationService

class FirebaseNotificationServiceTest(TestCase):
    def test_send_notification_to_topic(self):
        """Test d'envoi de notification à un topic"""
        result = FirebaseNotificationService.send_notification_to_topic(
            topic="test_topic",
            title="Test",
            body="Test notification"
        )
        self.assertTrue(result)
```

## 9. Monitoring et logs

### 9.1 Configuration des logs
```python
# settings.py

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/firebase_notifications.log',
        },
    },
    'loggers': {
        'notifications.services': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 10. Sécurité

### 10.1 Vérification des permissions
- Toujours vérifier que l'utilisateur a le droit d'envoyer des notifications
- Valider le contenu des notifications avant envoi
- Limiter le nombre de notifications par utilisateur

### 10.2 Rate limiting
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='10/m', method='POST')
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token(request):
    # ... logique existante ...
```

## 11. Déploiement

### 11.1 Variables d'environnement
```bash
# .env
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-service-account.json
FIREBASE_DATABASE_URL=https://minexx-mobile-app-default-rtdb.firebaseio.com
```

### 11.2 Docker
```dockerfile
# Dockerfile
COPY firebase-service-account.json /app/firebase-service-account.json
ENV FIREBASE_CREDENTIALS_PATH=/app/firebase-service-account.json
```

Cette configuration permet d'intégrer complètement Firebase dans le backend Django pour gérer les notifications push de l'application mobile MINEXX.
