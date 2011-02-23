import logging

logger = logging.getLogger(__name__)


class InlineButtonsAdminMixin(object):
    """ 
    Mixin which dynamically adds links to inline admins on the top right of
    the admin form.
    """
    class Media:
        js = ('js/inlinebuttons.js',)


class LimitedAdminInlineMixin(object):
    """
    InlineAdmin mixin limiting the selection of related items according to
    criteria which can depend on the current parent object being edited.

    A typical use case would be selecting a subset of related items from
    other inlines, ie. images, to have some relation to other inlines.

    Use as follows::

        class MyInline(LimitedAdminInlineMixin, admin.TabularInline):
            def get_filters(self, obj):
                return (('<field_name>', dict(<filters>)),)

    """

    @staticmethod
    def limit_inline_choices(formset, field, empty=False, **filters):
        """
        This function fetches the queryset with available choices for a given
        `field` and filters it based on the criteria specified in filters,
        unless `empty=True`. In this case, no choices will be made available.
        """
        assert formset.form.base_fields.has_key(field)

        qs = formset.form.base_fields[field].queryset
        if empty:
            logger.debug('Limiting the queryset to none')
            formset.form.base_fields[field].queryset = qs.none()
        else:
            qs = qs.filter(**filters)
            logger.debug('Limiting queryset for formset to: %s', qs)

            formset.form.base_fields[field].queryset = qs

    def get_formset(self, request, obj=None, **kwargs):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        formset = \
            super(LimitedAdminInlineMixin, self).get_formset(request,
                                                             obj,
                                                             **kwargs)

        for (field, filters) in self.get_filters(obj):
            if obj:
                self.limit_inline_choices(formset, field, **filters)
            else:
                self.limit_inline_choices(formset, field, empty=True)

        return formset

    def get_filters(self, obj):
        """
        Return filters for the specified fields. Filters should be in the
        following format::

            (('field_name', {'categories': obj}), ...)

        For this to work, we should either override `get_filters` in a
        subclass or define a `filters` property with the same syntax as this
        one.
        """
        return getattr(self, 'filters', ())


from sorl.thumbnail import get_thumbnail

from django.conf.urls.defaults import patterns, url

from tinymce.widgets import TinyMCE
from tinymce.views import render_to_image_list, render_to_link_list


class TinyMCEImageListMixin(object):
    """ 
    Example usage::
        related_image_field = 'image'
        related_image_size = '200x300'

        def get_related_images(cls, request, obj):
            return obj.brandimage_set.all()

    """
    related_image_size = None
    related_image_field = None
    related_images = None

    def get_related_images(self, request, obj):
        """
        Get related images for the specified object and request.
        """
        assert self.related_images, \
            'No related images property defined for the admin class. Please\
             provide one or directly override get_related_images.'

        return self.related_images

    def get_image_list(self, request, object_id):
        """ Get a list of available images for this page for TinyMCE to
            refer to. If the setting exists, scale the image to the default
            size specified in `related_image_size`.
        """

        assert self.related_image_field, \
            'No image field defined. Please define a property with the name \
             of the image field in the Admin class.'

        if not self.related_image_size:
            logger.info('No image size defined, not rendering thumbnails for \
                         TinyMCE image list.')

        obj = self._getobj(request, object_id)

        related_images = self.get_related_images(request, obj)

        image_list = []
        for obj in related_images:
            image = getattr(obj, self.related_image_field)
            if self.related_image_size:
                image = get_thumbnail(image, self.related_image_size)

            image_list.append((unicode(obj), image.url))

        return render_to_image_list(image_list)

    def get_urls(self):
        urls = super(TinyMCEImageListMixin, self).get_urls()

        my_urls = patterns('',
            url(r'^(.+)/image_list.js$',
                self._wrap(self.get_image_list),
                name=self._view_name('image_list')),
        )

        return my_urls + urls


class TinyMCELinkListMixin(object):
    """
    Example usage::

        def get_related_objects(self, request, obj):
            return obj.productmedia_set.all()

    """
    related_objects = None

    def get_related_objects(self, request, obj):
        """
        Get related objects for the specified object and request.
        """
        assert self.related_objects, \
            'No related objects property defined for the admin class. Please\
             provide one or directly override get_related_objects.'

        return self.related_objects

    def get_link_list(self, request, object_id):
        """ Get a list of available objects for this page for TinyMCE to
            refer to.
        """

        obj = self._getobj(request, object_id)

        related_objects = self.get_related_objects(request, obj)

        link_list = []
        for obj in related_objects:
            assert hasattr(obj, 'get_absolute_url'), \
                'Object has no URL get_absolute_url attribute for link list'

            url = obj.get_absolute_url()

            if url:
                link_list.append((unicode(obj), url))

        return render_to_link_list(link_list)

    def get_urls(self):
        urls = super(TinyMCELinkListMixin, self).get_urls()

        my_urls = patterns('',
            url(r'^(.+)/link_list.js$',
                self._wrap(self.get_link_list),
                name=self._view_name('link_list')),
        )

        return my_urls + urls


class TinyMCEAdminListMixin(object):
    """
    Example usage::

        class BrandTranslationInline(TinyMCEAdminListMixin, TranslationInline):
            model = BrandTranslation

            tinymce_fields = ('description', )

            def get_image_list_url(self, request, field, obj=None):
                if obj:
                    return reverse('admin:basic_webshop_brand_image_list', \
                                                 args=(obj.pk, ))
                else:
                    return None

    """
    get_image_list_url = lambda *args, **kwargs: None
    get_link_list_url = lambda *args, **kwargs: None
    tinymce_fields = ()

    def get_tinymce_widget(self, request, field, obj):
        """ Return the appropriate TinyMCE widget. """

        mce_attrs = {}

        if obj:
            link_list_url = self.get_link_list_url(request, field, obj)
            image_list_url = self.get_image_list_url(request, field, obj)
        else:
            link_list_url = self.get_link_list_url(request, field)
            image_list_url = self.get_image_list_url(request, field)

        if link_list_url:
            mce_attrs.update({'external_link_list_url': link_list_url})

        if image_list_url:
            mce_attrs.update({'external_image_list_url': image_list_url})

        return TinyMCE(mce_attrs=mce_attrs)

    def get_formset(self, request, obj=None, **kwargs):
        """ Override the form widget for the content field with a TinyMCE
            field which uses a dynamically assigned image list. """

        formset = super(TinyMCEAdminListMixin, self).get_formset(request,
                                                                 obj=None,
                                                                 **kwargs)

        for field in self.tinymce_fields:
            formset.form.base_fields[field].widget = \
                self.get_tinymce_widget(request, field, obj)

        return formset

