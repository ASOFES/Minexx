INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Applications personnalisées
    'core',
    'securite',
    'demandeur',
    'dispatch',
    'chauffeur',
    'entretien',
    'ravitaillement',
    'rapport',
    'suivi',
    'notifications',

    # Applications tierces
    'crispy_forms',
    'corsheaders',
    'rest_framework',
]
