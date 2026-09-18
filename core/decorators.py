from django.shortcuts import redirect, render
from django.contrib import messages
from functools import wraps

def demandeur_required(view_func):
    """Décorateur pour restreindre l'accès aux demandeurs uniquement"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role == 'demandeur' or request.user.role == 'admin' or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
            return redirect('login')
    return _wrapped_view

def dispatcher_required(view_func):
    """Décorateur pour restreindre l'accès aux dispatchers uniquement"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role == 'dispatch' or request.user.role == 'admin' or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
            return redirect('login')
    return _wrapped_view

def chauffeur_required(view_func):
    """Décorateur pour restreindre l'accès aux chauffeurs uniquement"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role == 'chauffeur' or request.user.role == 'admin' or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
            return redirect('login')
    return _wrapped_view

def securite_required(view_func):
    """Décorateur pour restreindre l'accès au personnel de sécurité uniquement"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role == 'securite' or request.user.role == 'admin' or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
            return redirect('login')
    return _wrapped_view

def admin_required(view_func):
    """Décorateur pour restreindre l'accès aux administrateurs uniquement"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role == 'admin' or request.user.is_staff or request.user.is_superuser):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
            return redirect('login')
    return _wrapped_view

def is_admin_or_dispatch_or_superuser(user):
    return user.is_authenticated and (user.role in ['admin', 'dispatch', 'chauffeur'] or user.is_superuser)

def departement_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        departement_id = kwargs.get('pk') or request.GET.get('departement')
        if departement_id:
            from .models import Etablissement
            try:
                departement = Etablissement.objects.get(pk=departement_id)
                if not request.user.peut_acceder_departement(departement):
                    messages.error(request, "Vous n'avez pas accès à ce département.")
                    return redirect('departement_list')
            except Etablissement.DoesNotExist:
                messages.error(request, "Département introuvable.")
                return redirect('departement_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def require_departement_password(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        import os
        expected = os.environ.get('DEPARTEMENT_ACCESS_PASSWORD', '').strip()
        # Admin / superuser : pas de verrou supplémentaire
        if request.user.is_authenticated and (
            request.user.is_superuser or getattr(request.user, 'role', None) == 'admin'
        ):
            request.session['departement_access_granted'] = True
            return view_func(request, *args, **kwargs)
        if not request.session.get('departement_access_granted', False):
            if request.method == 'POST' and 'departement_password' in request.POST:
                if expected and request.POST['departement_password'] == expected:
                    request.session['departement_access_granted'] = True
                    return redirect(request.path)
                else:
                    messages.error(
                        request,
                        "Mot de passe incorrect." if expected else "DEPARTEMENT_ACCESS_PASSWORD non configuré. Demandez à un administrateur."
                    )
            return render(request, 'core/departement/password.html')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
