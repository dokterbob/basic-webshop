import logging
logger = logging.getLogger(__name__)

from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.core.urlresolvers import reverse

from webshop.core.utils.admin import LimitedAdminInlineMixin

from webshop.extensions.variations.admin import ProductVariationInline
from webshop.extensions.images.admin import ProductImageInline, \
                                            ImagesProductAdminMixin

from multilingual_model.admin import TranslationInline

from basic_webshop.models import *
from basic_webshop.baseadmin import *

from sorl.thumbnail.admin import AdminInlineImageMixin

from simplesite.settings import PAGEIMAGE_SIZE
from simplesite.utils import ExtendibleModelAdminMixin


class PricedItemAdminMixin(object):
    """ Admin mixin for priced items. """
    def get_price(self, obj):
        price = obj.get_price()
        return price
    get_price.short_description = _('price')


class OrderStateChangeInline(admin.TabularInline):
    model = OrderStateChange

    fields = ('date', 'state', )
    readonly_fields = ('date', 'state')

    extra = 0
    max_num = 0
    can_delete = False


class OrderItemInlineBase(admin.TabularInline):
    extra = 0

    readonly_fields = ('price', )

class OrderItemInline(admin.TabularInline, PricedItemAdminMixin):
    model = OrderItem

    fields = ('order_line', 'quantity', 'piece_price',
              'discount', 'get_price',)
    readonly_fields = ('get_price', )

    extra = 0


class OrderAdmin(admin.ModelAdmin, PricedItemAdminMixin):
   save_on_top = True
   inlines = (OrderItemInline, OrderStateChangeInline)
   readonly_fields = ('order_number', 'invoice_number',
                      'get_formatted_address', 'customer', 'get_invoice',
                      'coupon_code', 'get_price', 'get_total_discounts',)
   list_display = ('order_number', 'date_added', 'state', 'get_price',
                   'customer', 'get_invoice',
                   )
   list_filter = ('state', )
   date_hierarchy = 'date_added'
   fields = ('state', 'order_discount', 'order_shipping_costs', 'notes', ) + \
             readonly_fields
   search_fields = ('order_number', 'customer__first_name',
                    'customer__last_name', 'invoice_number')

   def get_total_discounts(self, obj):
       return obj.get_total_discounts()
   get_total_discounts.short_description = _('total discounts')

   def get_invoice(self, obj):
       if obj.confirmed:
           invoice_url = reverse('order_invoice', args=(obj.order_number,))

           return u'<a href="%s">%s</a>' % (invoice_url, obj.invoice_number)
   get_invoice.short_description = _('Invoice')
   get_invoice.allow_tags = True

admin.site.register(Order, OrderAdmin)


class ShippingMethodAdmin(admin.ModelAdmin):
    filter_horizontal = ('countries', )
    list_display = ('name', 'order_cost')
    list_filter = ('countries', )

admin.site.register(ShippingMethod, ShippingMethodAdmin)


class ProductRatingAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_added'
    list_filter = ('language', )
    list_display = ('date_added', 'product', 'rating', 'user')
    readonly_fields = ('user', 'product', 'date_added', 'language')
    search_fields = ('user__first_name', 'user__last_name',
                     'product__translations__name',
                     'product__brand__translations__name')

admin.site.register(ProductRating, ProductRatingAdmin)


class CustomerAddressInline(admin.StackedInline):
    model = Address
    extra = 1


class CustomerAdmin(admin.ModelAdmin):
    inlines = (CustomerAddressInline, )
    search_fields = ('first_name', 'last_name', 'username', 'company', )
    list_display = ('username', 'get_full_name', 'is_active', 'company',
                    'gender', 'language', 'birthday',
                    'last_login', 'date_joined')
    list_filter = ('is_active', 'gender', 'language', 'birthday')
    fields = ('username', 'last_login', 'date_joined', 'first_name',
              'last_name', 'email', 'is_active', 'company', 'gender',
              'birthday', 'language')
    readonly_fields = ('last_login', 'date_joined')

admin.site.register(Customer, CustomerAdmin)


# class AddressAdmin(admin.ModelAdmin):
#     pass
#
# admin.site.register(Address, AddressAdmin)


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
    model = ProductVariationTranslation

    def get_filters(self, obj):
        """
        Make sure we can only select variations that relate to the current
        item.
        """
        return (('parent', dict(product=obj)),)


class ProductTranslationInline(TinyMCEAdminListMixin, TranslationInline):
    model = ProductTranslation
    max_num = 2
    extra = 2

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
        (_('Required fields'), {'fields':
                    ('categories', 'stock', 'price')}),
        (_('Publication attributes'), {
            'fields': ('active', 'date_publish', 'sort_order', ),
            'classes': ('collapse',),}),
        (_('Optional metadata'), {'fields':
                    ('related', 'alternates', 
                     'brand', 'unit', 'article_number',)}),
        # ('Dates', {'fields':
        #             ('date_added', 'date_modified', 'date_publish')}),

    )

    save_as = True
    readonly_fields = ('date_added', 'date_modified', )
    list_per_page = 20
    inlines = (ProductTranslationInline,
               ProductMediaInline,
               ProductImageInline,
               #ImageProductVariationInline,
               #ProductVariationTranslationInline,
              )
    filter_horizontal = ('categories', 'related', 'alternates')

    list_display = ('display_name', 'default_image', 'admin_categories', \
                    'sort_order', 'stock', 'active', )
    # list_display_links = ('name', )
    list_filter = ('active', 'date_publish', \
                   'brand', 'categories')
    list_editable = ('sort_order', 'active', 'stock')
    search_fields = ('slug', 'translations__name', 'article_number',
                     'categories__translations__name', 'categories__slug',
                     'brand__translations__name', 'brand__slug', )

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
    fieldsets = ((None,
                  {'fields': ('parent', 'slug', 'active', 'sort_order')}),
                 ('Category highlight',
                  {'fields': ('highlight_image', 'highlight_title', 'highlight_link',
              'highlight_text', 'highlight_html')})
    )
    readonly_fields = ('highlight_html', )
    # prepopulated_fields = {"slug": ("name",)}
    inlines = (CategoryTranslationInlineInline, CategoryFeaturedInline, )
    list_filter = ('active', 'parent', )
    list_editable = ('sort_order', 'active')
    list_display = ('admin_name', 'active',  'admin_products', \
                    'sort_order')
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
            value += u' <a href="../product/?categories__id__exact=%d">(%d inactive)</a>' % \
                (obj.pk, products_inactive_count)

        value += u'&nbsp;|&nbsp;<a href="../product/add/?categories=%d">Add</a>' \
            % (obj.pk, )

        return value

    admin_products.allow_tags = True
    admin_products.short_description = _('products')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Override MPTT's default field in order to retain
        # backwards-compatible behaviour.
        superclass = super(admin.ModelAdmin, self)
        return superclass.formfield_for_foreignkey(db_field,
                                                   request,
                                                   **kwargs)


admin.site.register(Category, CategoryAdmin)


class DiscountAdmin(admin.ModelAdmin):
    """ Model admin for discounts. """

    save_as = True
    readonly_fields = ('used', )
    filter_horizontal = ('categories', 'products')
    list_filter = ('start_date', 'end_date', 'use_coupon')
    search_fields = ('name', )

    # Exclude product and category discounts
    # NOT ONLY are they slow, they're also buggy
    exclude = ('products', 'categories', )

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
