from django import template
import string

register = template.Library()

def firstletter(brand):
    for c in brand.upper():
        if c in string.ascii_uppercase:
            return c

    # TODO: Should this be silently ignored?
    raise Exception("No letters in the alphabet found")

def brand_alphabetize(object_list):
    r_list = []
    for char in string.ascii_uppercase:
        r_objects = []
        for object in object_list:
            if firstletter(str(object)) == char:
                r_objects.append(object)

        if r_objects:
            r_list.append((char, r_objects))
            
    return {
        'list': r_list
    }

register.inclusion_tag('basic_webshop/brand_alphabetize.html')(brand_alphabetize)

