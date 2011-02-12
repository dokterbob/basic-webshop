import logging
logger = logging.getLogger(__name__)

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin

from webshop.extensions.variations.admin import ProductVariationInline, \
                                                VariationInlineMixin
from webshop.extensions.images.admin import ProductImageInline, \
                                            ImagesProductAdminMixin

from multilingual_model.admin import TranslationInline

from sorl.thumbnail.admin import AdminInlineImageMixin

from basic_webshop.models import *
from basic_webshop.baseadmin import *


class BrandTranslationInline(TranslationInline):
    model = BrandTranslation


class BrandAdmin(AdminInlineImageMixin, admin.ModelAdmin):
    """ Model admin for brands """
    inlines = (BrandTranslationInline, )

admin.site.register(Brand, BrandAdmin)

"""
TODO/bug:
    Overriode ProductVariationInline so that we can only select images
    associated with the current product.
""" 

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


class ImageProductVariationInline(LimitedAdminInlineMixin, ProductVariationInline):
    def get_formset(self, request, obj=None, **kwargs):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        formset = super(ImageProductVariationInline, self).get_formset(request, obj=None, **kwargs)
        
        if obj:
            self.limit_inline_choices(formset, 'image', product=obj)
        else:
            self.limit_inline_choices(formset, 'image', empty=True)

        return formset


class ProductVariationTranslationInline(LimitedAdminInlineMixin, admin.TabularInline):
    """ 
    TODO/bug:
        VariationInlineMixin should limit the variations we can select to those 
        associated with the current product, but this doesn't work.
    """
    model = ProductVariationTranslation

    def get_formset(self, request, obj=None, **kwargs):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        formset = super(ProductVariationTranslationInline, self).get_formset(request, obj=None, **kwargs)
        
        if obj:
            self.limit_inline_choices(formset, 'parent', product=obj)
        else:
            self.limit_inline_choices(formset, 'parent', empty=True)

        return formset


class ProductTranslationInline(TranslationInline):
    model = ProductTranslation


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1


class ProductAdmin(InlineButtonsAdminMixin, ImagesProductAdminMixin, admin.ModelAdmin):
    """ Model admin for products. """
    
    fields = ('slug', 'active', 'featured', 'date_added', 'date_modified', 'date_publish', 'categories', \
              'sort_order', 'price', 'stock', 'related', 'brand', 'unit')
    readonly_fields = ('date_added', 'date_modified', )
    date_hierarchy = 'date_added'
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (ProductTranslationInline,
               ProductMediaInline,
               ProductImageInline,
               ImageProductVariationInline,
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


class DiscountAdmin(admin.ModelAdmin):
    """ Model admin for discounts. """
    
    readonly_fields = ('used', )
    filter_horizontal = ('categories', 'products')
    list_filter = ('start_date', 'end_date', 'use_coupon')

    max_products_display = 2
    def admin_products(self, obj):
        """ TODO: Move this over to django-webshop's extension. """
        products = obj.products
        products_count = products.count()
        if products_count == 0:
            product_list = _('None')
        else:
            product_list = unicode(products[0])
            
            for product in products[1:self.max_products_display]:
                product_list += u', %s' % product
            
            if products_count > self.max_products_display:
                product_list += u', ...'
        
        return u'<a href="%d/">%s</a>' % (obj.pk, product_list)
    admin_products.allow_tags = True
    admin_products.short_description = _('products')


admin.site.register(Discount, DiscountAdmin)
