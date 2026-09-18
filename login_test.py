import os
import requests
from bs4 import BeautifulSoup

# Configuration via variables d'environnement
LOGIN_URL = os.environ.get('LOGIN_URL', 'http://127.0.0.1:8000/login/')
USERNAME = os.environ.get('TEST_USERNAME')
PASSWORD = os.environ.get('TEST_PASSWORD')

if not USERNAME or not PASSWORD:
    print('Définir TEST_USERNAME et TEST_PASSWORD')
    exit(1)

# Démarrer une session
session = requests.Session()

# 1. Récupérer le formulaire de login pour obtenir le token CSRF
response = session.get(LOGIN_URL)
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
if not csrf_token:
    print('Impossible de trouver le token CSRF. Vérifiez le formulaire de login.')
    exit(1)
csrf_token = csrf_token['value']

# 2. Préparer les données du formulaire
login_data = {
    'username': USERNAME,
    'password': PASSWORD,
    'csrfmiddlewaretoken': csrf_token,
}

headers = {
    'Referer': LOGIN_URL
}

# 3. Envoyer la requête POST pour se connecter
login_response = session.post(LOGIN_URL, data=login_data, headers=headers)

# 4. Vérifier si la connexion a réussi
if 'Déconnexion' in login_response.text or 'logout' in login_response.text:
    print('Connexion réussie !')
else:
    print('Échec de la connexion. Vérifiez les identifiants ou le formulaire.') 