import logging

logger = logging.getLogger(__name__)


class InlineButtonsAdminMixin(object):
    class Media:
        js = ('basic_webshop/js/inlinebuttons.js',)


class LimitedAdminInlineMixin(object):
    @staticmethod
    def limit_inline_choices(formset, field, empty=False, **filters):
        assert formset.form.base_fields.has_key(field)

        qs = formset.form.base_fields[field].queryset
        if empty:
            logger.debug('Limiting the queryset to none')
            formset.form.base_fields[field].queryset = qs.none()
        else:
            qs = qs.filter(**filters)
            logger.debug('Limiting queryset for formset to: %s', qs)
        
            formset.form.base_fields[field].queryset = qs

