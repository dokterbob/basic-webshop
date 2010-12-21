from django.db import models
from django.utils.translation import ugettext_lazy as _

from webshop.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase, UserCustomerBase
                                
from webshop.core.basemodels import NamedItemBase

from webshop.extensions.category.advanced.models import CategoryBase, \
                                                        CategorizedItemBase
from webshop.extensions.price.advanced.models import PriceBase, \
                                                     QuantifiedPriceMixin, \
                                                     ProductPriceMixin
from webshop.extensions.variations.models import OrderedProductVariationBase


class Customer(UserCustomerBase):
    """ Basic webshop customer. """
    pass


class Product(ProductBase, CategorizedItemBase, NamedItemBase):
    """ Basic product model. 
    
    >>> c = Category(name='Fruit', slug='fruit')
    >>> c.save()
    >>> p = Product(category=c, name='Banana', slug='banana', price="15.00")
    >>> p.description = 'A nice piece of fruit for the whole family to enjoy.'
    >>> p.save()
    >>> c.product_set.all()
    [<Product: Banana>]
    
    """
       
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=False)
    display_price = models.ForeignKey('Price', null=True, blank=True,
                                      related_name='display_price_product',
                                      help_text=_('Price displayed as \
                                              default for this product.'))

    @models.permalink
    def get_absolute_url(self):
        return 'product_detail', None, \
            {'category_slug': self.category.slug,
             'slug': self.slug}


class ProductVariation(OrderedProductVariationBase, 
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
    

class CartItem(CartItemBase):
    """ Item in a shopping cart. """
    
    pass


class Order(OrderBase):
    """ Basic order model. """
    
    pass


class OrderItem(OrderItemBase):
    """ Item in an order. """
    
    pass


class Category(CategoryBase, NamedItemBase):
    """ Basic category model. """
    
    slug = models.SlugField(unique=True)
    
    def get_products(self):
        """ Get all active products for the current category. """
        return Product.in_shop.filter(category_set=self)
    
    @models.permalink
    def get_absolute_url(self):
        return 'category_detail', None, \
            {'slug': self.slug}


