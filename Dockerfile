FROM python:3.11-slim

# Définir les variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBUG=False
ENV DJANGO_SETTINGS_MODULE=gestion_vehicules.settings
ENV TZ=Africa/Lubumbashi
# SECRET_KEY doit être fournie à l'exécution (jamais codée en dur dans l'image)

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
# Note: pas de wkhtmltopdf ici (souvent absent des images slim récentes) —
# les PDF utilisent xhtml2pdf en repli (voir core/pdf_utils.py).
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    g++ \
    tzdata \
    && ln -snf /usr/share/zoneinfo/Africa/Lubumbashi /etc/localtime \
    && echo Africa/Lubumbashi > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code de l'application
COPY . .

# Rendre le script de démarrage exécutable
RUN chmod +x start.sh

# Collecter les fichiers statiques (SECRET_KEY temporaire pour le build uniquement)
RUN SECRET_KEY=build-time-only-not-for-runtime python manage.py collectstatic --noinput

# Exposer le port
EXPOSE 8000

# Utiliser le script de démarrage
CMD ["./start.sh"] 