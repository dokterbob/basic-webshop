from django.contrib import admin

from basic_webshop.models import *
from webshop.extensions.price.advanced.admin import PriceInline
from webshop.extensions.variations.admin import ProductVariationInline
from webshop.extensions.images.admin import ProductImageInline, ImagesProductMixin

from multilingual_model.admin import TranslationInline


class VariationInlineMixin(object):
    """ Make sure we can only select variations that relate to the current
        product. 
        
        This should be part of the django-webshop variations extension.
    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # TODO: Somehow figure out the current product

        if db_field.name == "variation":
            # If no instance is given, it makes sense to not be able to
            # select any of its variations.
            if self.instance:
                qs = Variation.objects.filter(product=self.instance)
            else:
                qs = Variation.objects.none()
            
            kwargs["queryset"] = qs
        
        return super(VariationPriceInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class VariationPriceInline(PriceInline, VariationInlineMixin):
    pass

class ProductVariationTranslationInline(admin.TabularInline, VariationInlineMixin):
    # TODO: Limit the selection of parents to those associated with the 
    # current product.
    model = ProductVariationTranslation
    extra = 0


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
