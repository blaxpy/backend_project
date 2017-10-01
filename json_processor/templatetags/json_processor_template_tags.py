from django import template

register = template.Library()


@register.filter
def to_double_quotes(value):
    return repr(value).replace("'", '"')
