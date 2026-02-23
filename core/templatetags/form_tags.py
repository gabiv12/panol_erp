from django import template

register = template.Library()

@register.filter
def add_class(field, css):
    if not hasattr(field, "as_widget"):
        return field
    return field.as_widget(attrs={"class": css})
