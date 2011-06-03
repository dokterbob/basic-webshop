import logging

logger = logging.getLogger(__name__)


from django.conf import settings

from django.db import models
from django.utils.translation import get_language, ugettext_lazy as _

from django.contrib.auth.models import UserManager, User

from shopkit.core.managers import ActiveItemManager

from shopkit.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase, UserCustomerBase, \
                                OrderStateChangeBase

from shopkit.core.basemodels import NamedItemBase, ActiveItemInShopBase, \
                                    OrderedItemBase, DatedItemBase, \
                                    PublishDateItemBase

from shopkit.category.advanced.models import CategorizedItemBase, \
                                                        MPTTCategoryBase
from shopkit.price.simple.models import PricedItemBase
from shopkit.variations.models import \
    OrderedProductVariationBase, VariationCartItemMixin, \
    VariationOrderItemMixin

from shopkit.images.models import OrderedProductImageBase, \
                                             ImagesProductMixin
from shopkit.stock.advanced.models import \
    StockedCartItemMixin, StockedCartMixin, \
    StockedOrderItemMixin, StockedOrderMixin, \
    StockedItemMixin

from shopkit.related.models import RelatedProductsMixin
from shopkit.brands.models import BrandBase, BrandedProductMixin

from shopkit.discounts.advanced.models import \
    DiscountBase, ManyProductDiscountMixin, DateRangeDiscountMixin, \
    ManyCategoryDiscountMixin, LimitedUseDiscountMixin, CouponDiscountMixin, \
    OrderDiscountAmountMixin, ItemDiscountAmountMixin, \
    OrderDiscountPercentageMixin, ItemDiscountPercentageMixin, \
    DiscountedOrderMixin, DiscountedOrderItemMixin, DiscountCouponMixin, \
    DiscountedCartMixin, DiscountedCartItemMixin, AccountedDiscountedItemMixin

from shopkit.shipping.advanced.models import \
    ShippedOrderMixin, ShippedOrderItemMixin, ShippableCustomerMixin, \
    ShippedCartMixin, ShippedCartItemMixin, \
    ShippingMethodBase, OrderShippingMethodMixin, MinimumOrderAmountShippingMixin

from multilingual_model.models import MultilingualModel, \
                                      MultilingualTranslation

from tinymce import models as tinymce_models

from sorl.thumbnail import ImageField

from basic_webshop.basemodels import *

from countries.fields import CountryField

from docdata.models import PaymentCluster

# Silly optimizations for SQLite
from django.db import connection
cursor = connection.cursor()
if cursor.db.vendor == 'sqlite':
    logger.debug('Enabling PRAGMA optimizations for SQLite')
    cursor.execute('PRAGMA temp_store=MEMORY;')
    cursor.execute('PRAGMA synchronous=OFF;')

# Signal handling
from docdata.signals import payment_status_changed

from shopkit.core.signals import order_state_change
from basic_webshop.listeners import OrderPaidConfirm, \
    OrderPaidStatusChange, OrderClosedNotPaidStatusChange, \
    OrderPaidEmail, OrderFailedEmail, OrderRejectedEmail, OrderShippedEmail, \
    CustomerRegistrationEmail

from registration.signals import user_registered


payment_status_changed.connect(OrderPaidStatusChange.as_listener(), weak=False)
payment_status_changed.connect(OrderClosedNotPaidStatusChange.as_listener(), weak=False)
order_state_change.connect(OrderPaidConfirm.as_listener(), weak=False)
order_state_change.connect(OrderPaidEmail.as_listener(), weak=False)
order_state_change.connect(OrderFailedEmail.as_listener(), weak=False)
order_state_change.connect(OrderRejectedEmail.as_listener(), weak=False)
order_state_change.connect(OrderShippedEmail.as_listener(), weak=False)

user_registered.connect(CustomerRegistrationEmail.as_listener(), weak=False)


class ShippingMethod(NamedItemBase,
                     OrderShippingMethodMixin,
                     MinimumOrderAmountShippingMixin,
                     CountriesShippingMixin,
                     ShippingMethodBase):
    """ Shipping method """
    pass


class Address(CustomerAddressBase):
    postal_address = models.CharField(_('address'), max_length=50)
    postal_address2 = models.CharField(_('address 2'), blank=True, max_length=50)
    zip_code = models.CharField(_('zip code'), max_length=50)
    city = models.CharField(_('city'), max_length=50)
    country = CountryField(verbose_name=_('country'))
    phone_number = models.CharField(_('phone number'), max_length=50, blank=True)

    class Meta:
        ordering = ('-id', )

    def __unicode__(self):
        return self.addressee

    def formatted(self):
        """ Return the address formatted for shipping. """
        data = [self.addressee, self.postal_address, ]
        if self.postal_address2:
            data.append(self.postal_address2)

        data += [self.zip_code, self.city, unicode(self.country)]

        return "\n".join(data)


class Customer(BilledCustomerMixin, ShippableCustomerMixin, UserCustomerBase):
    """ Basic webshop customer. """
    objects = UserManager()

    company = models.CharField(_('company'), blank=True, max_length=50)

    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
    )
    gender = models.CharField(_('gender'), max_length=1, choices=GENDER_CHOICES)

    language = models.CharField(_('language'), max_length=5,
                                default=get_language, choices=settings.LANGUAGES)

    birthday = models.DateField(_('birthday'), null=True)

    shipping_address = models.ForeignKey(Address, null=True,
                                         related_name='shippable_customer')

    def get_address(self):
        """ Get 'the first and best' address from the customer. """

        if self.shipping_address:
            return self.shipping_address

        logger.warning(u'No shipping address set for customer %s, '+
                       u'returning last address used.', self)

        try:
            return self.address_set.all()[0]
        except IndexError:
            pass


ARTICLE_NUMBER_LENGTH = getattr(settings, 'SHOPKIT_ARTICLE_NUMBER_LENGTH')
class ArticleNumberMixin(models.Model):
    """
    Item with a required article number, `article_number`, which is
    represented by a CharField and indexed.
    """

    class Meta:
        abstract = True

    article_number = models.CharField(_('article number'),
                                      db_index=True,
                                      max_length=ARTICLE_NUMBER_LENGTH)


class Brand(AutoUniqueSlugMixin, NamedItemTranslationMixin, MultilingualModel, \
            BrandBase, OrderedItemBase, UniqueSlugItemBase, ):
    """ Brand in the webshop """

    class Meta:
        ordering = ('sort_order', )

    logo = ImageField(verbose_name=_('logo'),
                       upload_to='brand_logos')

    @models.permalink
    def get_absolute_url(self):
        return 'brand_detail', None, \
            {'slug': self.slug}


class BrandTranslation(MultilingualTranslation, NamedItemBase):
    class Meta(MultilingualTranslation.Meta, NamedItemBase.Meta):
        unique_together = (('language_code', 'parent',), )

    parent = models.ForeignKey(Brand, related_name='translations')

    # TinyMCE HTML fields
    # TODO: Make sure we use a custom widget with limited possibilities here
    # (We don't want users to use images and tables here, ideally.)
    description = tinymce_models.HTMLField(_('description'), blank=False)

    def save(self):
        super(BrandTranslation, self).save()

        self.parent.update_slug()


class BrandImage(models.Model):
    """
    Image for a brand. This is not a subclass of a NamedItemBase since it
    it's name is not an obligatory field: it's value is automatically set
    based on the name of the product.
    """

    name = models.CharField(max_length=255, blank=True,
                            verbose_name=_('name'))
    """ Name of this item. """
    brand = models.ForeignKey(Brand)
    image = ImageField(verbose_name=_('image'),
                       upload_to='brand_images')

    def __unicode__(self):
        """ Returns the item's name. """

        return self.name

    def save(self):
        """ Set the name of this image based on the name of the brand. """

        count = self.__class__.objects.filter(brand=self.brand).count()
        if not self.name:
            self.name = "%s - %d" % (self.brand.name, count+1)

        super(BrandImage, self).save()

class Product(MultilingualModel, ActiveItemInShopBase, ProductBase, \
              CategorizedItemBase, OrderedItemBase, PricedItemBase, \
              DatedItemBase, ImagesProductMixin, StockedItemMixin, \
              RelatedProductsMixin, BrandedProductMixin, UniqueSlugItemBase, \
              NamedItemTranslationMixin, ArticleNumberMixin, \
              AutoUniqueSlugMixin, PublishDateItemBase):
    """
    Basic product model.

    TODO: the stock can be kept for both variations as well as
    for variations. When the stock is specified for variations, this
    overrides the stock for the product. We should make note of this in the
    Admin interface.
    """
    objects = models.Manager()
    in_shop = ActiveItemManager()

    unit = models.CharField(_('unit'), blank=True, max_length=80,
                            help_text=_('Unit in which a specific article is \
                            sold, eg. \'100 ml\' or \'0.75 g\'.'))

    alternates = models.ManyToManyField('self', null=True, blank=True,
                                     symmetrical=True,
                                     verbose_name=_('variations'))

    class Meta(MultilingualModel.Meta, ActiveItemInShopBase.Meta, \
               ProductBase.Meta, CategorizedItemBase.Meta, \
               OrderedItemBase.Meta):
        """ Should'nt this stuff happen automatically? ;) """

        pass

    @models.permalink
    def get_absolute_url(self):
        return 'product_detail', None, \
            {'slug': self.slug}

    def display_name(self):
        return self
    display_name.short_description = _('name')

    def is_available(self, quantity=1):
        """ Make sure we also check for variations. """
        variations = self.productvariation_set.all()
        if variations.exists():
            for variation in variations:
                if variation.is_available(quantity):
                    return True

        return super(Product, self).is_available(quantity)

    def __unicode__(self):
        product_name = super(Product, self).__unicode__()
        brand_name = self.brand.__unicode__()

        return u'%s %s' % (brand_name, product_name)


###  Rating models
class ProductRating(DatedItemBase, models.Model):
    """ Customer product rating where the customer can give a small description
    and rating 1-5 """

    class Meta:
        ordering = ('-date_added', )

    # Automatically set fields
    product = models.ForeignKey(Product, editable=False)
    user = models.ForeignKey(User, editable=False)
    language = models.CharField(_('language'), max_length=5, editable=False,
                                default=get_language)

    RATING_CHOICES = \
        ((0, 0),
         (1, 1),
         (2, 2),
         (3, 3),
         (4, 4),
         (5, 5),)
    # User controlled fields
    rating = models.PositiveSmallIntegerField(_('rating'),
                                              choices=RATING_CHOICES)
    description = models.TextField(_('review'))

    def __unicode__(self):
        return _(u'%(rating)d for %(product)s on %(date)s') % \
            {'rating': self.rating,
             'product': self.product,
             'date': self.date_added.date()}

    def get_absolute_url(self):
        """ Return the product URL. """
        return '%s#' % self.product.get_absolute_url()


class ProductTranslation(MultilingualTranslation, NamedItemBase):
    class Meta(MultilingualTranslation.Meta, NamedItemBase.Meta):
        unique_together = (('language_code', 'parent',), )

    parent = models.ForeignKey(Product, related_name='translations')

    # TinyMCE HTML fields
    # TODO: Make sure we use a custom widget with limited possibilities here
    # (We don't want users to use images and tables here, ideally.)
    description = tinymce_models.HTMLField(_('description'), blank=False)
    manual = tinymce_models.HTMLField(_('manual'), blank=True)
    ingredients = tinymce_models.HTMLField(_('ingredients'), blank=True)
    media = tinymce_models.HTMLField(_('media'), blank=True)

    def save(self):
        super(ProductTranslation, self).save()

        self.parent.update_slug()


class ProductVariation(MultilingualModel, OrderedProductVariationBase, \
                       StockedItemMixin, NonUniqueSlugItemBase):
    class Meta(MultilingualModel.Meta, OrderedProductVariationBase.Meta):
        unique_together = (('product', 'slug',),
                           ('product', 'sort_order'),)

    def __unicode__(self):
        return self.slug

    image = models.ForeignKey('ProductImage', verbose_name=_('image'),
                              blank=True, null=True)


class ProductVariationTranslation(MultilingualTranslation, NamedItemBase):
    class Meta(MultilingualTranslation.Meta, NamedItemBase.Meta):
        unique_together = (('language_code', 'parent',), )

    parent = models.ForeignKey(ProductVariation, related_name='translations',
                               verbose_name=_('variation'))
    product = models.ForeignKey(Product)


class ProductImage(OrderedProductImageBase):
    """
    Image for a product. This is not a subclass of a NamedItemBase since it
    it's name is not an obligatory field: it's value is automatically set
    based on the name of the product.
    """

    name = models.CharField(max_length=255, blank=True,
                            verbose_name=_('name'))
    """ Name of this item. """

    def __unicode__(self):
        """ Returns the item's name. """

        return self.name

    def save(self):
        """ Set the name of this image based on the name of the product. """

        count = self.__class__.objects.filter(product=self.product).count()
        if not self.name:
            self.name = u"%s %s - %d" % (self.product.brand.name,
                                         self.product.name,
                                         count+1)

        super(ProductImage, self).save()


class ProductMedia(NamedItemBase):
    class Meta(NamedItemBase.Meta):
        verbose_name = _('media')
        verbose_name_plural = verbose_name

    product = models.ForeignKey(Product)
    mediafile = models.FileField(upload_to='product_media', verbose_name='media')
    """ TODO: Make sure only PDF files and JPEG files - of reasonable size - make it into this one. """

    def get_absolute_url(self):
        return self.mediafile.url


class Cart(ShippedCartMixin,
           StockedCartMixin,
           DiscountCouponMixin,
           DiscountedCartMixin,
           CartBase):
    """ Basic shopping cart model. """

    def add_item(self, product, quantity=1, **kwargs):
        """ Make sure we store the variation, if applicable. """

        cartitem = super(Cart, self).add_item(product, quantity, **kwargs)

        assert not cartitem.product.productvariation_set.exists() \
             or 'variation' in kwargs, \
             'Product has variations but none specified here.'

        return cartitem

    def __unicode__(self):
        if self.pk and self.customer:
            return u'%d for %s' % (self.pk, self.customer)

        if self.pk:
            return unicode(self.pk)

        if self.customer:
            return unicode(self.customer)


class CartItem(ShippedCartItemMixin,
               StockedCartItemMixin,
               DiscountedCartItemMixin,
               VariationCartItemMixin,
               CartItemBase):
    """
    Item in a shopping cart.
    """

    def get_stocked_item(self):
        """ Return the relevant item for which the stock is kept. """
        if self.variation:
            return self.variation

        return self.product


class OrderStateChange(OrderStateChangeBase):
    """ Basic order state change. """
    #note = models.CharField(blank=True, max_length=255)


class Order(ShippedOrderMixin,
            StockedOrderMixin,
            DiscountedOrderMixin,
            DiscountCouponMixin, AccountedDiscountedItemMixin,
            NumberedOrderBase,
            OrderBase):
    """ Basic order model. """

    def __unicode__(self):
        return self.order_number

    def get_formatted_address(self):
        """ Formatted shipping address. """
        return self.shipping_address.formatted_address()
    get_formatted_address.short_description = _('address')

    def get_formatted_discounts(self):
        """ Formatted discounts. """
        if self.discounts.exists():
            return "\n".join(self.discounts.all())
    get_formatted_discounts.short_description = _('discounts')

    @models.permalink
    def get_absolute_url(self):
        """ Order overview URL. """

        return ('order_detail', (), {'slug': self.order_number})

    def generate_invoice_number(self):
        """
        Generate consequent invoice numbers.
        """

        assert not self.invoice_number, 'Invoice number already generated.'

        # We might not have been saved
        if self.date_added:
            date = self.date_added.date()
        else:
            from datetime import date
            date = date.today()

        # Query the highest invoice number
        qs = self.__class__.objects.filter(invoice_number__isnull=False)
        max_query = qs.aggregate(models.Max('invoice_number'))
        max_number = max_query['invoice_number__max']

        # Make sure we're an cast into int
        if max_number:
            max_number = int(max_number)

        # Get the starting number from the settings file
        from django.conf import settings
        start_number = getattr(settings, 'SHOPKIT_INVOICE_NUMBER_START', 1)

        # When start > max: return start
        # Otherwise, return max
        if start_number > max_number:
            return '%d%d' % (date.year, start_number)

        return max_number + 1

    def generate_order_number(self):
        """
        Generate order numbers according to:
        cosYYYYMMDDNNN
        """
        assert not self.invoice_number, 'Invoice number already generated.'

        # We might not have been saved
        if self.date_added:
            date = self.date_added.date()
        else:
            from datetime import date
            date = date.today()

        datestr = date.isoformat().replace('-','')

        order_qs = self.__class__.objects.all()
        order_qs = order_qs.filter(date_added__year=date.year)
        order_qs = order_qs.filter(date_added__month=date.month)
        order_qs = order_qs.filter(date_added__day=date.day)

        try:
            # Get today's latest order number
            latest_order = order_qs.order_by('-order_number')[0]

            # Take last three digits
            order_number = latest_order.order_number[-3:]

            logger.debug('Current latest order number: %s', order_number)

            # Convert to int and add one
            number = int(order_number) + 1

        except IndexError:
            number = 1

        order_number = 'cos%s%03d' % (datestr, number)
        logger.debug('Generated order number: %s', order_number)

        assert not Order.objects.filter(order_number=order_number).exists(), \
            'Order number not unique'

        return order_number

    def update(self):
        """
        Update discounts and shipping costs.

        Note: we might want to integrate this functionality right into
        the shipping/discounts code. Should be more elegant.
        """
        assert self.pk, 'Order should be saved before updating'

        self.update_shipping()
        self.update_discount()
        # self.save()

    @classmethod
    def from_cart(self, cart):
        """ Set coupon code and shipping address """
        order = super(Order, self).from_cart(cart)
        order.coupon_code = cart.coupon_code

        # Get default shipping address from customer
        assert cart.customer
        address = cart.customer.get_address()
        # assert address
        order.shipping_address = address

        return order

    notes = models.TextField(_('notes'), blank=True,
                             help_text=_('Optional notes regarding this order.'))

    payment_cluster = models.OneToOneField(PaymentCluster, null=True,
                                         verbose_name=_('payment'),
                                         editable=False)

class OrderItem(ShippedOrderItemMixin,
                StockedOrderItemMixin,
                DiscountedOrderItemMixin,
                AccountedDiscountedItemMixin,
                VariationOrderItemMixin,
                OrderItemBase, ):
                #PricedItemBase):
    """
    Order items should have:

    * From Product:
      1. slug
      2. name
      3. description
    * From Variation:
      1. variation_slug
      2. variation_name
    * From Cart:
      1. quantity
      2. price

    """

    def get_stocked_item(self):
        """ Return the relevant item for which the stock is kept. """
        if self.variation:
            return self.variation

        return self.product


class Category(MPTTCategoryBase, MultilingualModel, NonUniqueSlugItemBase, \
               AutoUniqueSlugMixin, ActiveItemInShopBase, OrderedItemBase, \
               NamedItemTranslationMixin):
    """ Basic category model. """

    @classmethod
    def get_main_categories(cls):
        """ Only show active categories """
        main_categories = super(Category, cls).get_main_categories()

        main_categories = main_categories.filter(active=True)

        return main_categories

    def get_subcategories(self):
        """ Only show active subcategories """
        subcategories = super(Category, self).get_subcategories()

        subcategories = subcategories.filter(active=True)

        return subcategories

    highlight_image = ImageField(verbose_name=_('highlight image'),
                                 upload_to='category_highlight',
                                 blank=True, null=True)
    highlight_title = models.CharField(verbose_name=_('highlight title'),
                                      blank=True, max_length=100)
    highlight_link = models.CharField(verbose_name=_('hightlight link'),
                                     blank=True, max_length=256)
    highlight_text = models.TextField(verbose_name=('highlight text'),
                                      blank=True)

    def highlight_html(self):
        """
        HTML to show for the category highlight part. This is displayed in the
        admin as well as on the website and....
        TODO: !SHOULD USE PROPER SCALING!
        """
        if self.pk:
            if self.highlight_image:
                return u'<a href="%s"><img src="%s" alt="%s" /></a>' % \
                    (self.highlight_link, self.highlight_image.url, self.highlight_text)
            else:
                return 'No hightlight has been defined for this category.'

        return ''
    highlight_html.allow_tags = True
    highlight_html.short_description = ''


    class Meta(MPTTCategoryBase.Meta, NamedItemBase.Meta, OrderedItemBase.Meta):
        unique_together = ('parent', 'slug')

    def is_unique_slug(self, slug):
        return not self.__class__.objects.filter(slug=slug, parent=self.parent).exists()

    def display_name(self):
        return self
    display_name.short_description = _('name')

    @models.permalink
    def get_absolute_url(self):
        level = self.get_level()

        if level == 0:
            return 'category_detail', None, \
                {'category_slug': self.slug}
        if level == 1:
            return 'subcategory_detail', None, \
                {'category_slug': self.parent.slug,
                 'subcategory_slug': self.slug}
        else:
            return 'subsubcategory_detail', None, \
                {'category_slug': self.parent.parent.slug,
                 'subcategory_slug': self.parent.slug,
                 'subsubcategory_slug': self.slug}


class CategoryTranslation(NamedItemBase, MultilingualTranslation):
    class Meta(MultilingualTranslation.Meta, NamedItemBase.Meta):
        unique_together = (('language_code', 'parent',), )

    parent = models.ForeignKey(Category, related_name='translations')

    def save(self):
        super(CategoryTranslation, self).save()

        self.parent.update_slug()


class CategoryFeaturedProduct(models.Model):
    """ A product which is featured in a particular category in a
        particular order.
    """

    class Meta:
        verbose_name = _('featured product')
        verbose_name_plural = _('featured products')

    category = models.ForeignKey(Category, related_name='featured_products')
    product = models.ForeignKey(Product)
    featured_order = models.PositiveSmallIntegerField(_('featured order'),
                                        blank=True, null=True)
    """ The order in which featured items are ordered when displayed. """

    def __unicode__(self):
        return _(u'Featured product \'%s\'') % unicode(self.product)


class Discount(NamedItemBase, ManyCategoryDiscountMixin, CouponDiscountMixin, \
               LimitedUseDiscountMixin, ManyProductDiscountMixin, \
               DateRangeDiscountMixin, OrderDiscountAmountMixin, \
               ItemDiscountAmountMixin, OrderDiscountPercentageMixin, \
               ItemDiscountPercentageMixin, DiscountBase):
    def __unicode__(self):
        if self.name:
            return self.name

        return unicode(self.pk)
