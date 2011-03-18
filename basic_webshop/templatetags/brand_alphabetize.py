from django import template
import string

register = template.Library()

# TODO: Deal with brands which don't start with A-Z.
def brand_alphabetize(object_list):
    r_list = []
    for char in string.ascii_uppercase:
        r_objects = []
        for object in object_list:
            if str(object)[0].upper() == char:
                r_objects.append(object)

        if r_objects:
            r_list.append((char, r_objects))
            
    return {
        'list': r_list
    }

# Register the custom tag as an inclusion tag with takes_context=True.
register.inclusion_tag('basic_webshop/brand_alphabetize.html')(brand_alphabetize)

