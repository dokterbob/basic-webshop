from django.db import models
from django.utils.translation import ugettext_lazy as _

from webshop.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase, UserCustomerBase, \
                                OrderStateChangeBase
                                
from webshop.core.basemodels import NamedItemBase, ActiveItemInShopBase, \
                                    OrderedItemBase, DatedItemBase

from webshop.extensions.category.advanced.models import NestedCategoryBase, \
                                                        CategorizedItemBase
from webshop.extensions.price.advanced.models import PricedItemBase, \
                                                     PriceBase, \
                                                     QuantifiedPriceMixin, \
                                                     ProductPriceMixin
from webshop.extensions.variations.models import OrderedProductVariationBase
from webshop.extensions.images.models import OrderedProductImageBase, \
                                             ImagesProductMixin

from multilingual_model.models import MultilingualModel, \
                                      MultilingualTranslation


class Customer(UserCustomerBase):
    """ Basic webshop customer. """
    pass


class Product(MultilingualModel, ActiveItemInShopBase, ProductBase, \
              CategorizedItemBase, OrderedItemBase, ImagesProductMixin, \
              DatedItemBase):
    """ Basic product model. 
    
    >>> c = Category(name='Fruit', slug='fruit')
    >>> c.save()
    >>> p = Product(category=c, name='Banana', slug='banana', price="15.00")
    >>> p.description = 'A nice piece of fruit for the whole family to enjoy.'
    >>> p.save()
    >>> c.product_set.all()
    [<Product: Banana>]
    
    """

    class Meta(MultilingualModel.Meta, ActiveItemInShopBase.Meta, \
               ProductBase.Meta, CategorizedItemBase.Meta, \
               OrderedItemBase.Meta):
        """ Should'nt this stuff happen automatically? ;) """
        
        pass
    
    slug = models.SlugField(unique=True)
    display_price = models.ForeignKey('Price', null=True, blank=True,
                                      related_name='display_price_product',
                                      help_text=_('Price displayed as \
                                              default for this product.'))

    @models.permalink
    def get_absolute_url(self):
        return 'product_detail', None, \
            {'slug': self.slug}


    def __unicode__(self):
        return self.unicode_wrapper('name')

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
    description = models.TextField(blank=False)


class ProductVariation(MultilingualModel, OrderedProductVariationBase):
    class Meta(MultilingualModel.Meta, OrderedProductVariationBase.Meta):
        unique_together = (('product', 'slug',), 
                           ('product', 'sort_order'),)
    
    slug = models.SlugField()
    
    def __unicode__(self):
        return self.slug


class ProductVariationTranslation(MultilingualTranslation, NamedItemBase):
    class Meta(MultilingualTranslation.Meta, NamedItemBase.Meta):
        unique_together = (('language_code', 'parent',), )

    parent = models.ForeignKey(ProductVariation, related_name='translations',
                               verbose_name=_('variation'))
    product = models.ForeignKey(Product)


class ProductImage(OrderedProductImageBase,
                   NamedItemBase):
    pass


class Cart(CartBase):
    """ Basic shopping cart model. """
    
    pass


class Price(PriceBase, ProductPriceMixin, QuantifiedPriceMixin):
    """ Price valid for certain quantities. """

    class Meta(PriceBase.Meta):
        unique_together = (('product', 'variation', 'quantity'),)
    
    variation = models.ForeignKey(ProductVariation, null=True, blank=True,
                                  verbose_name=_('variation'))

    def __unicode__(self):
        """ Return the formatted value of the price. If a variation
            and/or a (minimum) quantity are specified, these are added
            to the representation.
        """
        
        price = super(Price, self).__unicode__()
        
        if self.variation:
            price += u' - %s' % self.variation
        
        if self.quantity:
            price += u' - per %d' % self.quantity
        
        return price


class CartItem(CartItemBase):
    """ 
    Item in a shopping cart. 
    """
    
    variation = models.ForeignKey(ProductVariation, null=True, blank=True,
                                  verbose_name=_('variation'))
    
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


class OrderItem(OrderItemBase, NamedItemBase, PricedItemBase):
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
    
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=False)


class NamedItemTranslationMixin(object):
    """ 
    Mixin for translated items with a name. 
    This makes sure that abstract base classes that rely on __unicode__
    will work with the translated __unicode__ name.
    
    Usage::
        class Banana(AbstractBaseClass, NamedItemTranslationMixin):
            ...
    
    """
    def __unicode__(self):
        return self.unicode_wrapper('name')


class Category(MultilingualModel, ActiveItemInShopBase, OrderedItemBase, 
               NestedCategoryBase, NamedItemTranslationMixin):
    """ Basic category model. """

    class Meta(NestedCategoryBase.Meta, NamedItemBase.Meta, OrderedItemBase.Meta):
        unique_together = ('parent', 'slug')
        
    slug = models.SlugField()
    
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

