from django.db import models


from webshop.core.models import ProductBase, CartBase, CartItemBase, \
                                OrderBase, OrderItemBase
                                
from webshop.core.basemodels import NamedItemBase

from webshop.extensions.category.simple.models import CategoryBase, \
                                                      CategorizedItemBase
from webshop.extensions.price.simple.models import PricedItemBase


class Product(CategorizedItemBase, PricedItemBase, NamedItemBase):
    """ Basic product model. """
    
    class Meta:
        unique_together = ('category', 'slug')
        
    slug = models.SlugField()

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

