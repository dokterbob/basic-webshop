from webshop.core.models import ProductBase, CartBase, OrderBase
from webshop.core.basemodels import NamedItemBase

from webshop.extensions.category.simple.models import CategoryBase, \
                                                      CategorizedProductBase

from django.db import models


class Product(CategorizedProductBase, NamedItemBase):
    """ Basic product model. """
    
    class Meta(CategorizedProductBase.Meta):
        unique_together = ('category', 'slug')
        
    slug = models.SlugField()

class Cart(CartBase):
    """ Basic shopping cart model. """
    
    pass

class Order(OrderBase):
    """ Basic order model. """
    
    pass

class Category(CategoryBase, NamedItemBase):
    """ Basic category model. """
    
    slug = models.SlugField(unique=True)

