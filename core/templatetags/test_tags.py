from django import template

register = template.Library()

@register.filter
def shout(value):
    return str(value).upper() + "!!!"
