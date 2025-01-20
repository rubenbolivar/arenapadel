from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filter to get an item from a dictionary using a key
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
