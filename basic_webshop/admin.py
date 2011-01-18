import logging
logger = logging.getLogger(__name__)

from django.contrib import admin

from basic_webshop.models import *
from webshop.extensions.price.advanced.admin import PriceInline
from webshop.extensions.variations.admin import ProductVariationInline, \
                                                VariationInlineMixin
from webshop.extensions.images.admin import ProductImageInline, \
                                            ImagesProductMixin

from multilingual_model.admin import TranslationInline




class VariationPriceInline(VariationInlineMixin, PriceInline):
    pass


class ProductVariationTranslationInline(VariationInlineMixin, admin.TabularInline):
    # TODO: Limit the selection of parents to those associated with the 
    # current product.
    model = ProductVariationTranslation


class ProductTranslationInline(TranslationInline):
    model = ProductTranslation


class ProductAdmin(admin.ModelAdmin, ImagesProductMixin):
    """ Model admin for products. """
    
    fields = ('slug', 'active', 'categories', 'display_price')
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (ProductTranslationInline,
               ProductImageInline,
               ProductVariationInline,
               ProductVariationTranslationInline,
               VariationPriceInline, )
    filter_horizontal = ('categories', )
    
    list_display = ('name', 'slug', 'default_image')
    # list_display_links = ('name', )
    
    def name(self, obj):
        return u'<a href="%d/">%s</a>' % \
            (obj.pk, obj)
    name.allow_tags = True
    
    def get_form(self, request, obj=None, **kwargs):
        """ Make sure we can only select a default price pertaining to the
            current Product.
        """
        form = super(ProductAdmin, self).get_form(request, obj=None, **kwargs)

        if obj:
            form.base_fields['display_price'].queryset = \
                form.base_fields['display_price'].queryset.filter(product=obj)

        return form

admin.site.register(Product, ProductAdmin)


class CategoryTranslationInlineInline(TranslationInline):
    model = CategoryTranslation


class CategoryAdmin(admin.ModelAdmin):
    """ Model admin for categories. """

    fields = ('parent', 'slug')
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (CategoryTranslationInlineInline, )

admin.site.register(Category, CategoryAdmin)
