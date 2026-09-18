from django.urls import path
from . import views

app_name = 'suivi'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('vehicules/', views.suivi_vehicules, name='suivi_vehicules'),
    path('vehicules/export/pdf/', views.export_vehicules_pdf, name='export_vehicules_pdf'),
    path('vehicules/export/excel/', views.export_vehicules_excel, name='export_vehicules_excel'),
    path('missions/', views.suivi_missions, name='suivi_missions'),
    path('missions/export/pdf/', views.export_missions_pdf, name='export_missions_pdf'),
    path('missions/export/excel/', views.export_missions_excel, name='export_missions_excel'),
    path('entretiens/', views.suivi_entretiens, name='suivi_entretiens'),
    path('entretiens/export/pdf/', views.export_entretiens_pdf, name='export_entretiens_pdf'),
    path('entretiens/export/excel/', views.export_entretiens_excel, name='export_entretiens_excel'),
    path('carburant/', views.suivi_carburant, name='suivi_carburant'),
    path('carburant/export/pdf/', views.export_carburant_pdf, name='export_carburant_pdf'),
    path('carburant/export/excel/', views.export_carburant_excel, name='export_carburant_excel'),
]
