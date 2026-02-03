from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using key"""
    if dictionary is None:
        return None
    # Convert key to string to handle both string and integer keys
    key = str(key)
    return dictionary.get(key, None)
