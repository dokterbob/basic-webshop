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
    
    list_display = ('default_image', 'name')
    # list_display_links = ('name', )
    
    def name(self, obj):
        return u'<a href="%d/">%s</a>' % \
            (obj.pk, obj.name)
    name.allow_tags = True


admin.site.register(Product, ProductAdmin)


class CategoryTranslationInlineInline(TranslationInline):
    model = CategoryTranslation


class CategoryAdmin(admin.ModelAdmin):
    """ Model admin for categories. """

    fields = ('parent', 'slug')
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (CategoryTranslationInlineInline, )

admin.site.register(Category, CategoryAdmin)
