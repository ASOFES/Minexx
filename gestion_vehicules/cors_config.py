# Configuration CORS pour l'application Flutter
# Ce fichier doit être importé dans settings.py

# Configuration CORS pour permettre les requêtes depuis l'app Flutter
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",      # Flutter web local
    "http://127.0.0.1:8080",     # Flutter web local
    "http://localhost:3000",      # Port alternatif
    "http://127.0.0.1:3000",     # Port alternatif
    "https://localhost:8080",     # HTTPS local
    "https://127.0.0.1:8080",    # HTTPS local
]

# Autoriser les credentials (cookies, headers d'authentification)
CORS_ALLOW_CREDENTIALS = True

# Headers autorisés
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Méthodes HTTP autorisées
CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Headers exposés dans la réponse
CORS_EXPOSE_HEADERS = [
    'content-type',
    'content-disposition',
]
