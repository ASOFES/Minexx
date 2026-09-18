from django.shortcuts import redirect
from django.utils import timezone
from django.urls import reverse
from .models import ApplicationControl

class ApplicationAccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Toujours autoriser les fichiers statiques/media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
        # Autoriser inconditionnellement toute requête vers /application-control/password
        if '/application-control/password' in request.path:
            return self.get_response(request)
        # Autoriser explicitement l'accès à /application-blocked/
        if '/application-blocked' in request.path:
            return self.get_response(request)
        # Autoriser l'accès à /application-control/ si la session spéciale est présente
        if '/application-control/' in request.path and request.session.get('admin_control_authenticated'):
            return self.get_response(request)
        # Si l'application est bloquée
        try:
            control = ApplicationControl.objects.get(pk=1)
        except ApplicationControl.DoesNotExist:
            return self.get_response(request)
        now = timezone.now()
        is_blocked = (not control.is_open) or (control.end_datetime and now > control.end_datetime) or (control.start_datetime and now < control.start_datetime)
        if is_blocked:
            request.session['block_message'] = control.message
            return redirect('application_blocked')
        # Si non bloqué, fonctionnement normal
        return self.get_response(request) 