from django.db import models
from django.utils.translation import ugettext_lazy as _

from webshop.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase, UserCustomerBase, \
                                OrderStateChangeBase
                                
from webshop.core.basemodels import NamedItemBase

from webshop.extensions.category.advanced.models import NestedCategoryBase, \
                                                        CategorizedItemBase
from webshop.extensions.price.advanced.models import PriceBase, \
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


class Product(MultilingualModel, ProductBase, CategorizedItemBase, \
              ImagesProductMixin):
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
    display_price = models.ForeignKey('Price', null=True, blank=True,
                                      related_name='display_price_product',
                                      help_text=_('Price displayed as \
                                              default for this product.'))

    @models.permalink
    def get_absolute_url(self):
        return 'product_detail', None, \
            {'category_slug': self.category.slug,
             'slug': self.slug}


    def __unicode__(self):
        name = self.name
        
        if not name:
                name = u''
        
        return name


class ProductTranslation(MultilingualTranslation, NamedItemBase):
    parent = models.ForeignKey(Product, related_name='translations')
    description = models.TextField(blank=False)


class ProductVariation(MultilingualModel, OrderedProductVariationBase):
    """
    TODO: Fix sortorder bug here. The sortorder default fucks up...
    """
    class Meta(MultilingualModel.Meta, OrderedProductVariationBase.Meta):
        unique_together = (('product', 'slug',), )
    
    slug = models.SlugField()
    
    def __unicode__(self):
        return self.slug


class ProductVariationTranslation(MultilingualTranslation, NamedItemBase):
    class Meta(MultilingualTranslation.Meta, NamedItemBase.Meta):
        unique_together = (('language_code', 'parent',), )

    parent = models.ForeignKey(ProductVariation, related_name='translations')
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
    """ Item in a shopping cart. """
    
    pass


class OrderStateChange(OrderStateChangeBase):
    """ Basic order state change. """
    
    pass


class Order(OrderBase):
    """ Basic order model. """
    
    pass


class OrderItem(OrderItemBase):
    """ Item in an order. """
    
    pass


class Category(MultilingualModel, NestedCategoryBase):
    """ Basic category model. """
    
    class Meta(NestedCategoryBase.Meta, NamedItemBase.Meta):
        unique_together = ('parent', 'slug')
        
    slug = models.SlugField()
    
    @models.permalink
    def get_absolute_url(self):
        return 'category_detail', None, \
            {'slug': self.slug}
    
    def __unicode__(self):
        name = self.name
        
        if not name:
                name = u''
        
        return name


class CategoryTranslation(NamedItemBase, MultilingualTranslation):
    parent = models.ForeignKey(Category, related_name='translations')

