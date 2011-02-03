import logging
logger = logging.getLogger(__name__)

from django.utils.translation import ugettext_lazy as _

from django.contrib import admin

from basic_webshop.models import *
from webshop.extensions.variations.admin import ProductVariationInline, \
                                                VariationInlineMixin
from webshop.extensions.images.admin import ProductImageInline, \
                                            ImagesProductMixin

from multilingual_model.admin import TranslationInline

from sorl.thumbnail.admin import AdminInlineImageMixin


class BrandTranslationInline(TranslationInline):
    model = BrandTranslation


class BrandAdmin(AdminInlineImageMixin, admin.ModelAdmin):
    """ Model admin for brands """
    inlines = (BrandTranslationInline, )

admin.site.register(Brand, BrandAdmin)


class ProductVariationTranslationInline(VariationInlineMixin, admin.TabularInline):
    """ 
    TODO:
    1) Limit selection of parents to the variations related to the current product
    2) Limit selection of image to the images related to the current product
    """
    model = ProductVariationTranslation


class ProductTranslationInline(TranslationInline):
    model = ProductTranslation


class ProductAdmin(admin.ModelAdmin, ImagesProductMixin):
    """ Model admin for products. """
    
    fields = ('slug', 'active', 'date_added', 'date_modified', 'categories', \
              'sort_order', 'price', 'stock', 'related', 'brand')
    readonly_fields = ('date_added', 'date_modified', )
    date_hierarchy = 'date_added'
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (ProductTranslationInline,
               ProductImageInline,
               ProductVariationInline,
               ProductVariationTranslationInline,
              )
    filter_horizontal = ('categories', 'related')
    
    list_display = ('display_name', 'default_image', 'admin_categories', 'sort_order', 'active', )
    # list_display_links = ('name', )
    list_filter = ('categories', 'active', 'date_added', 'date_modified', \
                   'stock','brand')
    list_editable = ('sort_order', 'active')
    search_fields = ('slug', 'translations__name', \
                     'categories__translations__name', 'categories__slug')

    max_categories_display = 2
    def admin_categories(self, obj):
        """ TODO: Move this over to django-webshop's extension. """
        categories = obj.categories.all()
        categories_count = categories.count()
        
        def category_link(obj):
            return u'<a href="../category/?category__id__exact=%d">%s</a>' % \
                (obj.pk, obj)
            
        if categories_count == 0:
            return _('None')
        else:
            category_list = category_link(categories[0])
            
            for category in categories[1:self.max_categories_display]:
                category_list += u', %s' % category_link(category)
            
            if categories_count > self.max_categories_display:
                category_list += u', ...'
            
            return category_list
    admin_categories.allow_tags = True
    admin_categories.short_description = _('categories')

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
    search_fields = ('slug', 'translations__name', )


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
