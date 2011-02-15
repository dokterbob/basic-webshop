import logging
logger = logging.getLogger(__name__)

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.core.urlresolvers import reverse

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

    fieldsets = (
        (None, {'fields': ('language_code', 'name', 'description')}),
        ('Optional', {
            'fields': ('manual', 'ingredients', 'media', ),
            'classes': ('collapse',),}),
    )

    @staticmethod
    def get_tinymce_widget(field, obj=None):
        """ Return the appropriate TinyMCE widget. """

        if obj and field == 'media':
            link_list_url = reverse('admin:basic_webshop_product_media_link_list',
                                     args=(obj.pk, ))
            return \
               TinyMCE(mce_attrs={'external_link_list_url': link_list_url})
        else:
            return \
               TinyMCE()

    def get_formset(self, request, obj=None, **kwargs):
        """ Override the form widget for the content field with a TinyMCE
            field which uses a dynamically assigned image list. """

        formset = super(ProductTranslationInline, self).get_formset(request, obj=None, **kwargs)

        formset.form.base_fields['media'].widget = self.get_tinymce_widget('media', obj)

        return formset


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1


from django.conf.urls.defaults import patterns, url

from simplesite.utils import ExtendibleModelAdminMixin

from tinymce.widgets import TinyMCE
from tinymce.views import render_to_image_list, render_to_link_list

class ProductAdmin(InlineButtonsAdminMixin, ImagesProductAdminMixin, \
                   ExtendibleModelAdminMixin, admin.ModelAdmin):
    """ Model admin for products. """

    fieldsets = (
        ('Required fields', {'fields':
                    ('categories', 'stock', 'price')}),
        ('Publication attributes', {
            'fields': ('active', 'date_publish', 'sort_order', ),
            'classes': ('collapse',),}),
        ('Optional metadata', {'fields':
                    ('related', 'brand', 'unit')}),
        # ('Dates', {'fields':
        #             ('date_added', 'date_modified', 'date_publish')}),

    )

    save_as = True
    readonly_fields = ('date_added', 'date_modified', )
    date_hierarchy = 'date_added'
    inlines = (ProductTranslationInline,
               ProductMediaInline,
               ProductImageInline,
               ImageProductVariationInline,
               ProductVariationTranslationInline,
              )
    filter_horizontal = ('categories', 'related')
    
    list_display = ('display_name', 'default_image', 'admin_categories', \
                    'sort_order', 'active', )
    # list_display_links = ('name', )
    list_filter = ('active', 'date_publish', \
                   'brand', 'categories')
    list_editable = ('sort_order', 'active')
    search_fields = ('slug', 'translations__name', \
                     'categories__translations__name', 'categories__slug',
                     'brand__translations__name', 'brand__slug')

    max_categories_display = 2
    def admin_categories(self, obj):
        """ TODO: Move this over to django-webshop's extension. """
        categories = obj.categories.all()
        categories_count = categories.count()
        
        def category_link(obj):
            return u'<a href="../category/%d/">%s</a>' % \
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

    def get_media_link_list(self, request, object_id):
        """ Get the media available for linking to. """
        obj = self._getobj(request, object_id)
        
        product_media = obj.productmedia_set.all()
        link_list = []
        for media in product_media:
            link_list.append((media.name, media.mediafile.url))
                
        return render_to_link_list(link_list)

    def get_urls(self):
        urls = super(ProductAdmin, self).get_urls()
        
        my_urls = patterns('',
            url(r'^(.+)/media_link_list.js$', 
                self._wrap(self.get_media_link_list), 
                name=self._view_name('media_link_list')),
        )

        return my_urls + urls

admin.site.register(Product, ProductAdmin)


class CategoryTranslationInlineInline(TranslationInline):
    model = CategoryTranslation


class CategoryFeaturedInline(LimitedAdminInlineMixin, admin.TabularInline):
    model = CategoryFeaturedProduct
    extra =  1
    fields = ('featured_order', 'product')

    def get_formset(self, request, obj=None, **kwargs):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        formset = \
            super(CategoryFeaturedInline, self).get_formset(request, obj=None, **kwargs)

        if obj:
            self.limit_inline_choices(formset, 'product', categories=obj)
        else:
            self.limit_inline_choices(formset, 'product', empty=True)

        return formset


from mptt.admin import MPTTModelAdmin
class CategoryAdmin(MPTTModelAdmin):
    """ Model admin for categories. """

    save_as = True
    fields = ('parent', 'slug', 'active', 'sort_order')
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (CategoryTranslationInlineInline, CategoryFeaturedInline, )
    list_filter = ('active', 'parent', )
    list_editable = ('sort_order', 'active')
    list_display = ('admin_name',  'admin_products', \
                    'sort_order', 'active')
    search_fields = ('slug', 'translations__name', )
    mptt_indent_field = 'admin_name'

    def admin_name(self, obj):
        return obj.name
    admin_name.short_description = _('name')
    
    max_products_display = 2
    def admin_products(self, obj):
        products = obj.product_set.all()
        products_count = products.count()
        products_inactive_count = products.filter(active=False).count()
        
        if not products_count:
            value = _('No products')
        elif products_count == 1:
            value = u'<a href="../product/?categories__id__exact=%d">1 product</a>' \
                % (obj.pk, )
        else:
            value = u'<a href="../product/?categories__id__exact=%d">%d products</a>' \
                % (obj.pk, products_count)
        
        if products_inactive_count:
            value += u' <a href="">(%d inactive)</a>' % \
                (obj.pk, products_inactive_count)
        
        value += u'&nbsp;|&nbsp;<a href="../product/add/?categories=%d">Add</a>' \
            % (obj.pk, )
        
        return value
        
    admin_products.allow_tags = True
    admin_products.short_description = _('products')
   
admin.site.register(Category, CategoryAdmin)


class DiscountAdmin(admin.ModelAdmin):
    """ Model admin for discounts. """

    save_as = True
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
