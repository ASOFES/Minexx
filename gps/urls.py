from django.urls import path
from . import views
from . import api

app_name = 'gps'

urlpatterns = [
    path('', views.live_map, name='live_map'),
    path('live/', views.live_map, name='live'),
    path('historique/', views.historique, name='historique'),
    path('mission/<int:course_id>/', views.mission_detail, name='mission_detail'),
    path('api/live/', views.api_live_missions, name='api_live'),
    path('api/mission/<int:course_id>/positions/', views.api_mission_positions, name='api_mission_positions'),
    path('api/mission/<int:course_id>/ping/', views.web_ping, name='web_ping'),
    # Mobile / token API (aussi monté sous /api/ via core.urls)
    path('api/token/mission/<int:course_id>/positions/', api.api_chauffeur_gps_positions, name='api_token_positions'),
    path('api/token/mission/<int:course_id>/track/', api.api_mission_gps_track, name='api_token_track'),
]
