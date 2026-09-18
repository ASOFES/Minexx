from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Soustrait l'argument de la valeur."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return ""

@register.simple_tag(takes_context=True)
def url_replace(context, field, value):
    """
    Remplace ou ajoute un paramètre GET dans l'URL, utile pour la pagination avec filtres.
    """
    query = context['request'].GET.copy()
    query[field] = value
    return query.urlencode()
