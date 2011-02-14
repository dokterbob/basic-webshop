import logging

logger = logging.getLogger(__name__)

from django.db import models
from django.utils.translation import ugettext_lazy as _

from webshop.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase, UserCustomerBase, \
                                OrderStateChangeBase

from webshop.core.basemodels import NamedItemBase, ActiveItemInShopBase, \
                                    OrderedItemBase, DatedItemBase, \
                                    PublishDateItemBase

from webshop.extensions.category.advanced.models import CategorizedItemBase
from webshop.extensions.price.simple.models import PricedItemBase
from webshop.extensions.variations.models import OrderedProductVariationBase
from webshop.extensions.images.models import OrderedProductImageBase, \
                                             ImagesProductMixin
from webshop.extensions.stock.advanced.models import StockedCartItemMixin, \
                                                   StockedItemMixin
from webshop.extensions.related.models import RelatedProductsMixin
from webshop.extensions.brands.models import BrandBase, BrandedProductMixin
from webshop.extensions.discounts.models import DiscountBase, \
                                                ManyProductDiscountMixin, \
                                                DateRangeDiscountMixin, \
                                                ManyCategoryDiscountMixin, \
                                                LimitedUseDiscountMixin, \
                                                CouponDiscountMixin

from multilingual_model.models import MultilingualModel, \
                                      MultilingualTranslation

from tinymce import models as tinymce_models

from sorl.thumbnail import ImageField

from basic_webshop.basemodels import *


class Customer(UserCustomerBase):
    """ Basic webshop customer. """
    pass


class Brand(AutoUniqueSlugMixin, NamedItemTranslationMixin, MultilingualModel, \
            BrandBase, OrderedItemBase, UniqueSlugItemBase, ):
    """ Brand in the webshop """

    logo = ImageField(verbose_name=_('logo'),
                       upload_to='brand_logos')


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


class Product(MultilingualModel, ActiveItemInShopBase, ProductBase, \
              CategorizedItemBase, OrderedItemBase, PricedItemBase, \
              DatedItemBase, ImagesProductMixin, StockedItemMixin, \
              RelatedProductsMixin, BrandedProductMixin, UniqueSlugItemBase, \
              NamedItemTranslationMixin, OrderedFeaturedProductMixin, \
              AutoUniqueSlugMixin, PublishDateItemBase):
    """
    Basic product model.

    >>> c = Category(name='Fruit', slug='fruit')
    >>> c.save()
    >>> p = Product(category=c, name='Banana', slug='banana', price="15.00")
    >>> p.description = 'A nice piece of fruit for the whole family to enjoy.'
    >>> p.save()
    >>> c.product_set.all()
    [<Product: Banana>]

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

    def get_price(self, *args, **kwargs):
        if self.display_price:
            price = self.display_price

        else:
            kwargscopy = kwargs.copy()
            kwargscopy.update({'product': self})
            price = Price.get_cheapest(**kwargscopy)

        return price.get_price(**kwargs)


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
            self.name = "%s - %d" % (self.product.name, count+1) 
        
        super(ProductImage, self).save()


class ProductMedia(NamedItemBase):
    class Meta(NamedItemBase.Meta):
        verbose_name = _('media')
        verbose_name_plural = verbose_name
    
    product = models.ForeignKey(Product)
    mediafile = models.FileField(upload_to='product_media', verbose_name='media')
    """ TODO: Make sure only PDF files and JPEG files - of reasonable size - make it into this one. """


class Cart(CartBase):
    """ Basic shopping cart model. """

    pass


class CartItem(CartItemBase, StockedCartItemMixin):
    """
    Item in a shopping cart.
    """

    variation = models.ForeignKey(ProductVariation, null=True, blank=True,
                                  verbose_name=_('variation'))

    def get_stocked_item(self):
        """ Return the relevant item for which the stock is kept. """
        if self.variation:
            return self.variation.is_available()

        return self.product.is_available()


    def addProduct(self, product, quantity=1, variation=None):
        """ Make sure we store the variation, if applicable. """

        cartitem = super(CartItem, self).addProduct(product, quantity)
        cartitem.variation = variation

        assert self.product.variation_set.exists() and variation, \
            'Product has variations but no variation specified here.'

class OrderStateChange(OrderStateChangeBase):
    """ Basic order state change. """

    pass


class Order(OrderBase):
    """ Basic order model. """

    pass


class OrderItem(OrderItemBase, UniqueSlugItemBase, NamedItemBase, PricedItemBase):
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
    """ TODO: Move variation up to the variations extension of django-webshop. """

    description = models.TextField(blank=False)


class Category(MPTTCategoryBase, MultilingualModel, NonUniqueSlugItemBase, \
               AutoUniqueSlugMixin, ActiveItemInShopBase, OrderedItemBase, \
               NamedItemTranslationMixin):
    """ Basic category model. """

    class Meta(NestedCategoryBase.Meta, NamedItemBase.Meta, OrderedItemBase.Meta):
        unique_together = ('parent', 'slug')

    def is_unique_slug(self, slug):
        return not self.__class__.objects.filter(slug=slug, parent=self.parent).exists()

    def display_name(self):
        return self
    display_name.short_description = _('name')

    @models.permalink
    def get_absolute_url(self):
        return 'category_detail', None, \
            {'slug': self.slug}


class CategoryTranslation(NamedItemBase, MultilingualTranslation):
    class Meta(MultilingualTranslation.Meta, NamedItemBase.Meta):
        unique_together = (('language_code', 'parent',), )

    parent = models.ForeignKey(Category, related_name='translations')

    def save(self):
        super(CategoryTranslation, self).save()

        self.parent.update_slug()


class Discount(NamedItemBase, ManyCategoryDiscountMixin, CouponDiscountMixin, \
               LimitedUseDiscountMixin, ManyProductDiscountMixin, \
               DateRangeDiscountMixin, DiscountBase):
    pass
