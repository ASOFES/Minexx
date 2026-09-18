from django.urls import path
from . import views
from . import api

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/password/', views.profile_password_change, name='profile_password_change'),
    
    # Gestion des utilisateurs
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/password-reset/', views.user_password_reset, name='user_password_reset'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/change-departement/', views.user_change_departement, name='user_change_departement'),
    path('users/export/pdf/', views.user_list_pdf, name='user_list_pdf'),
    path('users/export/excel/', views.user_list_excel, name='user_list_excel'),
    
    # Gestion des véhicules
    path('vehicules/', views.vehicule_list, name='vehicule_list'),
    path('vehicules/create/', views.vehicule_create, name='vehicule_create'),
    path('vehicules/<int:pk>/', views.vehicule_detail, name='vehicule_detail'),
    path('vehicules/<int:pk>/edit/', views.vehicule_edit, name='vehicule_edit'),
    path('vehicules/<int:pk>/delete/', views.vehicule_delete, name='vehicule_delete'),
    
    # Export PDF des véhicules
    path('vehicules/export/pdf/', views.vehicule_list_pdf, name='vehicule_list_pdf'),
    path('vehicules/<int:pk>/export/pdf/', views.vehicule_detail_pdf, name='vehicule_detail_pdf'),
    path('vehicules/export/excel/', views.vehicule_list_excel, name='vehicule_list_excel'),
    path('etablissement/create/', views.create_etablissement, name='create_etablissement'),
    path('users/create/', views.create_user, name='create_user'),
    path('choose-etablissement/', views.choose_etablissement, name='choose_etablissement'),
    path('send-test-sms/', views.send_test_sms, name='send_test_sms'),
    path('send-test-sms-africastalking/', views.send_test_sms_africastalking, name='send_test_sms_africastalking'),
    # Contrôle de l'application
    path('application-control/password/', views.application_control_password, name='application_control_password'),
    path('application-control/', views.application_control, name='application_control'),
    path('application-blocked/', views.application_blocked, name='application_blocked'),
    path('application-control/logout/', views.application_control_logout, name='application_control_logout'),
    # Gestion des départements
    path('departements/', views.departement_list, name='departement_list'),
    path('departements/create/', views.departement_create, name='departement_create'),
    path('departements/<int:pk>/', views.departement_detail, name='departement_detail'),
    path('departements/<int:pk>/edit/', views.departement_edit, name='departement_edit'),
    path('departements/<int:pk>/delete/', views.departement_delete, name='departement_delete'),
    path('messagerie/send/', views.send_message, name='send_message'),
    path('messagerie/messages/', views.get_messages, name='get_messages'),
    path('messagerie/users/', views.get_users, name='get_users'),
    path('messagerie/unread_status/', views.get_unread_messages_status, name='get_unread_messages_status'),
    path('messagerie/alerts/', views.get_alert_events, name='get_alert_events'),
    path('vehicule/<int:vehicule_id>/changer-etablissement/', views.vehicule_change_etablissement, name='vehicule_change_etablissement'),
    path('configuration/', views.configuration_view, name='configuration'),
    path('test/', views.test_view, name='test'),
    path('set-language/', views.set_language, name='set_language'),
    
    # API endpoints pour les applications mobiles
    path('api/login/', api.api_login, name='api_login'),
    path('api/verify-token/', api.api_verify_token, name='api_verify_token'),
    path('api/chauffeur/missions/', api.api_chauffeur_missions, name='api_chauffeur_missions'),
    # Demandeur
    path('api/demandeur/demandes/', api.api_demandeur_demandes_list, name='api_demandeur_demandes_list'),
    path('api/demandeur/demandes/create/', api.api_demandeur_demandes_create, name='api_demandeur_demandes_create'),
    # Dispatcher
    path('api/dispatch/demandes/', api.api_dispatch_demandes_list, name='api_dispatch_demandes_list'),
    path('api/dispatch/demandes/<int:course_id>/assigner/', api.api_dispatch_assigner, name='api_dispatch_assigner'),
    # Chauffeur actions
    path('api/chauffeur/missions/<int:course_id>/demarrer/', api.api_chauffeur_demarrer, name='api_chauffeur_demarrer'),
    path('api/chauffeur/missions/<int:course_id>/terminer/', api.api_chauffeur_terminer, name='api_chauffeur_terminer'),
    path('api/chauffeur/missions/<int:course_id>/gps/', api.api_chauffeur_gps_proxy, name='api_chauffeur_gps'),
    path('api/chauffeur/missions/<int:course_id>/gps/track/', api.api_chauffeur_gps_track_proxy, name='api_chauffeur_gps_track'),
]
