from django.urls import path
from . import views

app_name = 'securite'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nouvelle-checklist/', views.nouvelle_checklist, name='nouvelle_checklist'),
    path('checklist/<int:checklist_id>/', views.detail_checklist, name='detail_checklist'),
    path('checklist/<int:checklist_id>/pdf/', views.pdf_checklist, name='pdf_checklist'),
    path('signaler-incident/', views.signaler_incident, name='signaler_incident'),
    path('export-excel/', views.export_checklists_excel, name='export_excel'),
    path('export-pdf/', views.export_checklists_pdf, name='export_pdf'),
    path('corriger-kilometrage/', views.corriger_kilometrage, name='corriger_kilometrage'),
    path('get-kilometrage-vehicule/', views.get_kilometrage_vehicule, name='get_kilometrage_vehicule'),
    path('historique/corrections-km/', views.historique_corrections_km, name='historique_corrections_km'),
    path('historique/corrections-km/pdf/', views.historique_corrections_km_pdf, name='historique_corrections_km_pdf'),
    path('historique/corrections-km/excel/', views.historique_corrections_km_excel, name='historique_corrections_km_excel'),
]
