from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()

@register.simple_tag(takes_context=True)
def generate_url(context, key, val):
    # XXX: This templatetag should be called after the request context has been fully processed.
    # XXX: i'm not sure if the arguments should be validated in any way.

    if 'request' in context:
        q = context['request'].GET.copy()
        q[key] = val

        return mark_safe('?%s' % (q.urlencode(), ))

    return mark_safe('')
