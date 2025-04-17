from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to get an item from a dictionary using a key
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key, key)

@register.filter(name='split')
def split(value, delimiter):
    """
    Template filter to split a string by a delimiter
    Usage: {{ string|split:"," }}
    """
    return value.split(delimiter)

@register.filter(name='trim')
def trim(value):
    """
    Template filter to trim whitespace from a string
    Usage: {{ string|trim }}
    """
    return value.strip() if value else value
