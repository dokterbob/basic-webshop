from webshop.core.models import ProductBase, CartBase, OrderBase

from webshop.extensions.category.simple.models import CategoryBase, \
                                                      CategorizedProductBase

from django.db import models


class Product(CategorizedProductBase):
    """ Basic product model. """

    pass

class Cart(CartBase):
    """ Basic shopping cart model. """
    
    pass

class Order(OrderBase):
    """ Basic order model. """
    
    pass

class Category(CategoryBase):
    """ Basic category model. """
    
    pass

