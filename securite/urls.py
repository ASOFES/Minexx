from django.urls import path
from . import views

app_name = 'securite'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nouvelle-checklist/', views.nouvelle_checklist, name='nouvelle_checklist'),
    path('checklist/<int:checklist_id>/', views.detail_checklist, name='detail_checklist'),
    path('checklist/<int:checklist_id>/pdf/', views.pdf_checklist, name='pdf_checklist'),
    path('signaler-incident/', views.signaler_incident, name='signaler_incident'),
    path('incidents/<int:incident_id>/', views.detail_incident, name='detail_incident'),
    path('incidents/<int:incident_id>/modifier/', views.modifier_incident, name='modifier_incident'),
    path('incidents/<int:incident_id>/traiter/', views.marquer_incident_traite, name='marquer_incident_traite'),
    path('incidents/<int:incident_id>/cloturer/', views.cloturer_incident, name='cloturer_incident'),
    path('export-excel/', views.export_checklists_excel, name='export_excel'),
    path('export-pdf/', views.export_checklists_pdf, name='export_pdf'),
    path('corriger-kilometrage/', views.corriger_kilometrage, name='corriger_kilometrage'),
    path('get-kilometrage-vehicule/', views.get_kilometrage_vehicule, name='get_kilometrage_vehicule'),
    path('historique/corrections-km/', views.historique_corrections_km, name='historique_corrections_km'),
    path('historique/corrections-km/pdf/', views.historique_corrections_km_pdf, name='historique_corrections_km_pdf'),
    path('historique/corrections-km/excel/', views.historique_corrections_km_excel, name='historique_corrections_km_excel'),
]
