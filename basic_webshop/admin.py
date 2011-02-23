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

from basic_webshop.models import *
from basic_webshop.baseadmin import *

from sorl.thumbnail.admin import AdminInlineImageMixin
from sorl.thumbnail import get_thumbnail

from django.conf.urls.defaults import patterns, url

from simplesite.settings import PAGEIMAGE_SIZE
from simplesite.utils import ExtendibleModelAdminMixin

from tinymce.widgets import TinyMCE
from tinymce.views import render_to_image_list, render_to_link_list

from django.contrib.auth.admin import UserAdmin


class CustomerAdmin(admin.ModelAdmin):
    pass

admin.site.register(Customer, CustomerAdmin)


class BrandTranslationInline(TinyMCEAdminListMixin, TranslationInline):
    model = BrandTranslation

    tinymce_fields = ('description', )

    def get_image_list_url(self, request, field, obj=None):
        if obj:
            return reverse('admin:basic_webshop_brand_image_list', \
                                         args=(obj.pk, ))
        else:
            return None


class BrandImageInline(AdminInlineImageMixin, admin.TabularInline):
    model = BrandImage


class BrandAdmin(AdminInlineImageMixin, TinyMCEImageListMixin, \
                 ExtendibleModelAdminMixin, admin.ModelAdmin):
    """ Model admin for brands """

    inlines = (BrandTranslationInline, BrandImageInline)
    
    related_image_field = 'image'
    related_image_size = PAGEIMAGE_SIZE
    
    def get_related_images(cls, request, obj):
        return obj.brandimage_set.all()


admin.site.register(Brand, BrandAdmin)


class ImageProductVariationInline(LimitedAdminInlineMixin, ProductVariationInline):
    def get_filters(self, obj):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        return (('image', dict(product=obj)),)


class ProductVariationTranslationInline(LimitedAdminInlineMixin, admin.TabularInline):
    """
    TODO/bug:
        VariationInlineMixin should limit the variations we can select to those
        associated with the current product, but this doesn't work.
    """
    model = ProductVariationTranslation

    def get_filters(self, obj):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        return (('parent', dict(product=obj)),)


class ProductTranslationInline(TinyMCEAdminListMixin, TranslationInline):
    model = ProductTranslation

    fieldsets = (
        (None, {'fields': ('language_code', 'name', 'description')}),
        ('Optional', {
            'fields': ('manual', 'ingredients', 'media', ),
            'classes': ('collapse',),}),
    )
    
    tinymce_fields = ('media', )
    
    def get_link_list_url(self, request, field, obj=None):
        if obj:
            return reverse('admin:basic_webshop_product_link_list', \
                                         args=(obj.pk, ))
        else:
            return None


class ProductMediaInline(admin.TabularInline):
    model = ProductMedia
    extra = 1


class ProductAdmin(InlineButtonsAdminMixin, ImagesProductAdminMixin, \
                   TinyMCELinkListMixin, ExtendibleModelAdminMixin, \
                   admin.ModelAdmin):
    """ Model admin for products. """

    fieldsets = (
        ('Required fields', {'fields':
                    ('categories', 'stock', 'price')}),
        ('Publication attributes', {
            'fields': ('active', 'date_publish', 'sort_order', ),
            'classes': ('collapse',),}),
        ('Optional metadata', {'fields':
                    ('related', 'brand', 'unit', 'article_number',)}),
        # ('Dates', {'fields':
        #             ('date_added', 'date_modified', 'date_publish')}),

    )

    save_as = True
    readonly_fields = ('date_added', 'date_modified', )
    list_per_page = 20
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
    
    def get_related_objects(self, request, obj):
        return obj.productmedia_set.all()

admin.site.register(Product, ProductAdmin)


class CategoryTranslationInlineInline(TranslationInline):
    model = CategoryTranslation


class CategoryFeaturedInline(LimitedAdminInlineMixin, admin.TabularInline):
    model = CategoryFeaturedProduct
    extra =  1
    fields = ('featured_order', 'product')

    def get_filters(self, obj):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        return (('product', dict(categories=obj)),)


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
