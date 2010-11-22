from django.contrib import admin

from basic_webshop.models import *


class ProductAdmin(admin.ModelAdmin):
    """ Model admin for products. """
    
    fields = ('name', 'slug', 'category', 'price', 'description')
    prepopulated_fields = {"slug": ("name",)}

    
admin.site.register(Product, ProductAdmin)


class CategoryAdmin(admin.ModelAdmin):
    """ Model admin for categories. """

    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Category, CategoryAdmin)
