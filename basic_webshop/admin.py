from django.contrib import admin

from basic_webshop.models import *
from webshop.extensions.price.advanced.admin import PriceInline
from webshop.extensions.variations.admin import ProductVariationInline
from webshop.extensions.images.admin import ProductImageInline


class ProductAdmin(admin.ModelAdmin):
    """ Model admin for products. """
    
    fields = ('name', 'slug', 'active', 'categories', 'description', 'display_price')
    prepopulated_fields = {"slug": ("name",)}
    inlines = (ProductImageInline, ProductVariationInline, PriceInline, )
    filter_horizontal = ('categories', )

admin.site.register(Product, ProductAdmin)


class CategoryAdmin(admin.ModelAdmin):
    """ Model admin for categories. """

    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Category, CategoryAdmin)
