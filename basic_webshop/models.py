import logging

logger = logging.getLogger(__name__)

from django.db import models
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import UserManager

from webshop.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase, UserCustomerBase, \
                                OrderStateChangeBase

from webshop.core.basemodels import NamedItemBase, ActiveItemInShopBase, \
                                    OrderedItemBase, DatedItemBase, \
                                    PublishDateItemBase

from webshop.extensions.category.advanced.models import CategorizedItemBase, \
                                                        MPTTCategoryBase
from webshop.extensions.price.simple.models import PricedItemBase
from webshop.extensions.variations.models import OrderedProductVariationBase
from webshop.extensions.images.models import OrderedProductImageBase, \
                                             ImagesProductMixin
from webshop.extensions.stock.advanced.models import StockedCartItemMixin, \
                                                   StockedItemMixin
from webshop.extensions.related.models import RelatedProductsMixin
from webshop.extensions.brands.models import BrandBase, BrandedProductMixin

from webshop.extensions.discounts.advanced.models import \
    DiscountBase, ManyProductDiscountMixin, DateRangeDiscountMixin, \
    ManyCategoryDiscountMixin, LimitedUseDiscountMixin, CouponDiscountMixin, \
    OrderDiscountAmountMixin, ItemDiscountAmountMixin, \
    OrderDiscountPercentageMixin, ItemDiscountPercentageMixin, \
    DiscountedOrderMixin, DiscountedOrderItemMixin, DiscountCouponMixin, \
    DiscountedCartMixin, DiscountedCartItemMixin

from webshop.extensions.shipping.advanced.models import \
    ShippableOrderBase, ShippableOrderItemBase, ShippableCustomerMixin, \
    ShippingMethodBase, OrderShippingMethodMixin, MinimumOrderAmountShippingMixin


from multilingual_model.models import MultilingualModel, \
                                      MultilingualTranslation

from tinymce import models as tinymce_models

from sorl.thumbnail import ImageField

from basic_webshop.basemodels import *

from countries.fields import CountryField


class ShippingMethod(NamedItemBase,
                     OrderShippingMethodMixin,
                     MinimumOrderAmountShippingMixin,
                     CountriesShippingMixin,
                     ShippingMethodBase):
    """ Shipping method """
    pass


class Address(CustomerAddressBase):
    postal_address = models.CharField(_('address'), max_length=50)
    postal_address2 = models.CharField('', blank=True, max_length=50)
    zip_code = models.CharField(_('zip code'), max_length=50)
    city = models.CharField(_('city'), max_length=50)
    country = CountryField()
    telephone_number = models.CharField(_('phone number'), max_length=50)

class Customer(BilledCustomerMixin, ShippableCustomerMixin, UserCustomerBase):
    """ Basic webshop customer. """
    objects = UserManager()

    company = models.CharField(_('company'), blank=True, max_length=50)

    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
    )
    gender = models.CharField(_('gender'), max_length=1, choices=GENDER_CHOICES)

    # TODO: The reason birthday can be null is because the UserManager creates
    # and saves a new user (without a birthday) which violates the not NULL
    # constraint. The solution is to create a CustomerManager with UserManager
    # as superclass.
    #
    # Mathijs speaks: let's just make birthdays optional. :P
    birthday = models.DateField(_('birthday'), null=True)


ARTICLE_NUMBER_LENGTH = 11
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

    unit = models.CharField(_('unit'), blank=True, max_length=80,
                            help_text=_('Unit in which a specific article is \
                            sold, eg. \'100 ml\' or \'0.75 g\'.'))

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

class RatingField(models.IntegerField):
    def formfield(self, **kwargs):
        defaults = {'min_value': 1, 'max_value': 5}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)

class ProductRating(models.Model):
    """ Customer product rating where the customer can give a small description
    and rating 1-5 """

    rating = RatingField(blank=True)
    product = models.ForeignKey(Product)
    customer = models.ForeignKey(Customer)
    description = models.TextField(blank=False)

    # TODO: The language should be defined in a correct fashion.
    language = models.CharField(_('language'), blank=True, max_length=10)

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
            self.name = "%s %s - %d" % (self.product.brand.name,
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


class Cart(CartBase,
           DiscountedCartMixin,
           DiscountCouponMixin):
    """ Basic shopping cart model. """

    def add_item(self, product, quantity=1, **kwargs):
        """ Make sure we store the variation, if applicable. """

        cartitem = super(Cart, self).add_item(product, quantity, **kwargs)

        assert not cartitem.product.productvariation_set.exists() \
             or 'variation' in kwargs, \
             'Product has variations but none specified here.'

        return cartitem


class CartItem(CartItemBase,
               StockedCartItemMixin,
               DiscountedCartItemMixin):
    """
    Item in a shopping cart.
    """

    variation = models.ForeignKey(ProductVariation, null=True, blank=True,
                                  verbose_name=_('variation'))

    def get_stocked_item(self):
        """ Return the relevant item for which the stock is kept. """
        if self.variation:
            return self.variation

        return self.product


class OrderStateChange(OrderStateChangeBase):
    """ Basic order state change. """
    pass


class Order(#ShippedOrderMixin,
            DiscountedOrderMixin, DiscountCouponMixin,
            OrderBase):
    """ Basic order model. """

    notes = models.TextField(blank=True,
                             help_text=_('Optional notes regarding this order.'))


class OrderItem(ShippableOrderItemBase,
                DiscountedOrderItemMixin,
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

    variation = models.ForeignKey(ProductVariation, null=True, blank=True,
                                  verbose_name=_('variation'))


class Category(MPTTCategoryBase, MultilingualModel, NonUniqueSlugItemBase, \
               AutoUniqueSlugMixin, ActiveItemInShopBase, OrderedItemBase, \
               NamedItemTranslationMixin):
    """ Basic category model. """

    highlight_image = ImageField(verbose_name=_('highlight image'),
                                 upload_to='category_highlight',
                                 blank=True, null=True)
    highlight_title = models.CharField(verbose_name=_('highlight title'),
                                      blank=True, max_length=100)
    highlight_link = models.URLField(verbose_name=_('hightlight link'),
                                     blank=True, verify_exists=True)
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
        else:
            return 'subcategory_detail', None, \
                {'category_slug': self.parent.slug,
                 'subcategory_slug': self.slug}


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
        return _('Featured product \'%s\'') % unicode(self.product)


class Discount(NamedItemBase, ManyCategoryDiscountMixin, CouponDiscountMixin, \
               LimitedUseDiscountMixin, ManyProductDiscountMixin, \
               DateRangeDiscountMixin, OrderDiscountAmountMixin, \
               ItemDiscountAmountMixin, OrderDiscountPercentageMixin, \
               ItemDiscountPercentageMixin, DiscountBase):
    pass
