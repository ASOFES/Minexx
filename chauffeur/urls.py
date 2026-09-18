from django.urls import path
from . import views

app_name = 'chauffeur'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('mission/<int:mission_id>/', views.detail_mission, name='detail_mission'),
    path('mission/<int:mission_id>/demarrer/', views.demarrer_mission, name='demarrer_mission'),
    path('mission/<int:mission_id>/terminer/', views.terminer_mission, name='terminer_mission'),
    path('mission/<int:mission_id>/pdf/', views.mission_pdf, name='mission_pdf'),
    path('missions/pdf/', views.missions_pdf, name='missions_pdf'),
    path('missions/excel/', views.missions_excel, name='missions_excel'),
    path('mission/<int:mission_id>/excel/', views.mission_excel, name='mission_excel'),
    path('api/vehicule/kilometrage/', views.get_vehicule_kilometrage, name='get_vehicule_kilometrage'),
    path('rapport/pdf/', views.rapport_chauffeur_pdf, name='rapport_chauffeur_pdf'),
    path('rapport/excel/', views.rapport_chauffeur_excel, name='rapport_chauffeur_excel'),
    path('rapport/', views.rapport_chauffeur, name='rapport_chauffeur'),
    # URLs pour les rapports demandeur
    path('rapport-demandeur/', views.rapport_demandeur, name='rapport_demandeur'),
    path('rapport-demandeur/pdf/', views.rapport_demandeur_pdf, name='rapport_demandeur_pdf'),
    path('rapport-demandeur/excel/', views.rapport_demandeur_excel, name='rapport_demandeur_excel'),
    path('rapport-missions-par-demandeur/', views.rapport_missions_par_demandeur, name='rapport_missions_par_demandeur'),
]
