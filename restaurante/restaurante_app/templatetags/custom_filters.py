from django import template

register = template.Library()

@register.filter
def punto_mil(value):
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        return value