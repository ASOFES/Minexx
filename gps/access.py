from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404

from core.models import ActionTraceur, Course
from .models import GPSAccessLog


MANAGER_ROLES = {'admin', 'dispatch', 'consultant'}


def user_can_manage_gps(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.role == 'admin':
        return True
    return user.role in MANAGER_ROLES


def user_can_view_course_gps(user, course):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.role == 'admin':
        return True
    if user.role == 'chauffeur' and course.chauffeur_id == user.id:
        return True
    if user.role == 'demandeur' and course.demandeur_id == user.id:
        return True
    if user.role in MANAGER_ROLES:
        if not user.etablissement_id:
            return False
        return (
            course.etablissement_id == user.etablissement_id
            or (course.vehicule_id and course.vehicule.etablissement_id == user.etablissement_id)
            or (course.demandeur_id and course.demandeur.etablissement_id == user.etablissement_id)
        )
    return False


def courses_queryset_for_user(user):
    qs = Course.objects.select_related('chauffeur', 'vehicule', 'demandeur', 'etablissement')
    if user.is_superuser or user.role == 'admin':
        if user.etablissement_id and not user.is_superuser:
            return qs.filter(
                Q(etablissement=user.etablissement)
                | Q(vehicule__etablissement=user.etablissement)
                | Q(demandeur__etablissement=user.etablissement)
            ).distinct()
        return qs
    if user.role == 'chauffeur':
        return qs.filter(chauffeur=user)
    if user.role == 'demandeur':
        return qs.filter(demandeur=user)
    if user.role in MANAGER_ROLES and user.etablissement_id:
        return qs.filter(
            Q(etablissement=user.etablissement)
            | Q(vehicule__etablissement=user.etablissement)
            | Q(demandeur__etablissement=user.etablissement)
        ).distinct()
    return qs.none()


def log_gps_access(user, action, course=None, details=''):
    GPSAccessLog.objects.create(
        utilisateur=user,
        course=course,
        action=action,
        details=details or '',
    )
    ActionTraceur.objects.create(
        utilisateur=user,
        action=f'GPS: {action}',
        details=details or (f'Mission #{course.id}' if course else ''),
    )


def gps_manager_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not user_can_manage_gps(request.user):
            raise PermissionDenied('Accès réservé aux gestionnaires.')
        return view_func(request, *args, **kwargs)
    return _wrapped


def get_course_for_gps_view(request, course_id):
    course = get_object_or_404(
        Course.objects.select_related('chauffeur', 'vehicule', 'demandeur', 'etablissement'),
        pk=course_id,
    )
    if not user_can_view_course_gps(request.user, course):
        raise PermissionDenied('Accès GPS non autorisé pour cette mission.')
    return course
