from django.template.defaulttags import register
from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name="compare")
def compare(a, b):
    return a == b
