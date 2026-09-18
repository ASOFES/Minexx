from django import template
import inspect

register = template.Library()

@register.filter
def get_methods(obj):
    """Retourne la liste des méthodes disponibles sur un objet"""
    if obj is None:
        return []
    return [m[0] for m in inspect.getmembers(obj, inspect.ismethod) if not m[0].startswith('_')]

@register.filter
def pprint(obj):
    """Filtre pour afficher joliment un objet dans les templates"""
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    return pp.pformat(obj)

@register.filter
def get_attrs(obj):
    """Retourne un dictionnaire des attributs d'un objet"""
    if obj is None:
        return {}
    
    attrs = {}
    for attr in dir(obj):
        if not attr.startswith('_'):
            try:
                # Essayer d'accéder à l'attribut
                value = getattr(obj, attr)
                # Vérifier si c'est un appelable (méthode, fonction, etc.)
                if not callable(value):
                    attrs[attr] = value
            except AttributeError:
                # Ignorer les attributs qui génèrent des erreurs
                continue
    return attrs
