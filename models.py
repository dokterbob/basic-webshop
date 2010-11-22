from django.db import models


from webshop.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase
                                
from webshop.core.basemodels import NamedItemBase

from webshop.extensions.category.simple.models import CategoryBase, \
                                                      CategorizedItemBase
from webshop.extensions.price.simple.models import PricedItemBase

"""
>>> c = Category(name='Fruit', slug='fruit')
>>> c.save()
>>> p = Product(category=c, name='Banana', slug='banana', price="15.00")
>>> p.description = 'A nice piece of fruit for the whole family to enjoy.'
>>> p.save()
>>> c.product_set.all()
[<Product: Banana>]
"""
class Product(ProductBase, CategorizedItemBase, PricedItemBase, NamedItemBase):
    """ Basic product model. """
    
    class Meta:
        unique_together = ('category', 'slug')
   
    slug = models.SlugField()
    description = models.TextField(blank=False)

    @models.permalink
    def get_absolute_url(self):
        return 'product_detail', None, \
            {'category_slug': self.category.slug,
             'slug': self.slug}

class Cart(CartBase):
    """ Basic shopping cart model. """
    
    pass

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
        return Product.in_shop.filter(category=self)
    
    @models.permalink
    def get_absolute_url(self):
        return 'category_detail', None, \
            {'slug': self.slug}

