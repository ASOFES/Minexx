from django.urls import path
from . import api

# URLs de l'API REST pour l'application mobile
api_urlpatterns = [
    # Authentification
    path('login/', api.api_login, name='api_login'),
    path('verify-token/', api.api_verify_token, name='api_verify_token'),

    # Chauffeur
    path('chauffeur/missions/', api.api_chauffeur_missions, name='api_chauffeur_missions'),
    path('chauffeur/missions/<int:course_id>/demarrer/', api.api_chauffeur_demarrer, name='api_chauffeur_demarrer'),
    path('chauffeur/missions/<int:course_id>/terminer/', api.api_chauffeur_terminer, name='api_chauffeur_terminer'),

    # Demandeur
    path('demandeur/demandes/', api.api_demandeur_demandes_list, name='api_demandeur_demandes_list'),
    path('demandeur/demandes/create/', api.api_demandeur_demandes_create, name='api_demandeur_demandes_create'),

    # Dispatcher
    path('dispatch/demandes/', api.api_dispatch_demandes_list, name='api_dispatch_demandes_list'),
    path('dispatch/demandes/<int:course_id>/assigner/', api.api_dispatch_assigner, name='api_dispatch_assigner'),
]
