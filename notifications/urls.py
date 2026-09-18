from django.urls import path
from . import views
from .views import SaveSubscriptionView, user_notifications

app_name = 'notifications'

urlpatterns = [
    # URL pour vérifier le statut des notifications
    path('status/', views.notification_status, name='status'),
    path('save_subscription/', SaveSubscriptionView.as_view(), name='save_subscription'),
    path('api/notifications/', user_notifications, name='user_notifications'),
    # Vous pouvez ajouter d'autres URLs personnalisées ici si nécessaire
]
