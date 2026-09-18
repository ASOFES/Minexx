from django import template

register = template.Library()

@register.filter
def in_list(value, arg):
    """Vérifie si une valeur est dans une liste de chaînes séparées par des virgules"""
    return value in arg.split(',') 