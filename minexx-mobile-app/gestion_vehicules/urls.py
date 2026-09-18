"""
URL configuration for gestion_vehicules project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('demandeur/', include('demandeur.urls')),
    path('dispatch/', include('dispatch.urls')),
    path('chauffeur/', include('chauffeur.urls')),
    path('securite/', include('securite.urls')),
    path('entretien/', include('entretien.urls')),
    path('ravitaillement/', include('ravitaillement.urls')),
    path('suivi/', include('suivi.urls')),
    path('rapport/', include('rapport.urls')),
    path('notifications/', include('notifications.urls')),
    # path('chat/', include('chat.urls')),  # Module chat désactivé car non présent
    
    # API REST pour l'application mobile
    path('api/', include('core.api_urls')),  # Inclure les URLs API avec le préfixe /api/
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
