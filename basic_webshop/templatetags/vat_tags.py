from decimal import Decimal

from django import template
from django.conf import settings

register = template.Library()

VAT_PERCENTAGE = getattr(settings, 'WEBSHOP_VAT_PERCENTAGE', 19)

vat_factor = VAT_PERCENTAGE/100.0


@register.filter
def vat_amount(value):
    """ Total amount of VAT for amount. """
    amount = float(value)
    return amount*vat_factor

@register.filter
def vat_inclusive(value):
    """ Amount inlcuding VAT. """
    amount = float(value)
    return value*(1+vat_factor)
    