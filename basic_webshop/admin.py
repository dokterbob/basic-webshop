import logging
logger = logging.getLogger(__name__)

from django.utils.translation import ugettext_lazy as _

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
    
    fields = ('slug', 'active', 'categories', 'display_price', 'sort_order')
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

    fields = ('parent', 'slug', 'active', 'sort_order')
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (CategoryTranslationInlineInline, )
    list_filter = ('active', 'parent', )
    list_editable = ('sort_order', 'active')
    list_display = ('display_name',  'admin_parent', 'admin_products', \
                    'sort_order', 'active')

    def admin_parent(self, obj):
        """ TODO: Move this over to django-webshop's extension. """
        if obj.parent:
            return u'<a href="?parent__id__exact=%d">%s</a>' % \
                (obj.parent.pk, obj.parent)
        else:
            return _('None')
    admin_parent.allow_tags = True
    admin_parent.short_description = _('parent')
    
    max_products_display = 2
    def admin_products(self, obj):
        """ TODO: Move this over to django-webshop's extension. """
        products = obj.product_set.all()
        products_count = products.count()
        if products_count == 0:
            return _('None')
        else:
            product_list = unicode(products[0])
            
            for product in products[1:self.max_products_display]:
                product_list += u', %s' % product
            
            if products_count > self.max_products_display:
                product_list += u', ...'
                        
            return u'<a href="../product/?categories__id__exact=%d">%s</a>' % \
                (obj.pk, product_list)
    admin_products.allow_tags = True
    admin_products.short_description = _('products')
   
admin.site.register(Category, CategoryAdmin)
