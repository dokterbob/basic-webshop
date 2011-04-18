from templatetag_sugar.register import tag
from templatetag_sugar.parser import *

from django import template
from django.utils.datastructures import SortedDict
import string

register = template.Library()

def firstletter(brand):
    for c in brand.upper():
        if c in string.ascii_uppercase:
            return c

    # give A if we cant find any letters.
    return 'A'

@tag(register, [Variable(), Constant("as"), Name(), Constant("and"), Name()])
def brand_alphabetize(context, brands, asvar1, asvar2):
    brands = list(brands)

    letter_brands = SortedDict()

    for brand in brands:
        first_letter = firstletter(brand.name)

        try:
            letter_brands[first_letter].append(brand)
        except KeyError:
            letter_brands[first_letter] = [brand, ]

    half = len(letter_brands) / 2
    context[asvar1] = letter_brands.items()[:half]
    context[asvar2] = letter_brands.items()[half:]
    
    return ""
