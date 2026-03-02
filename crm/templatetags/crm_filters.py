"""Custom template filters for SERVIAC CRM"""
from django import template

register = template.Library()


@register.filter
def abs_value(value):
    """Returns absolute value of a number"""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.filter
def divide(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (TypeError, ValueError):
        return 0
