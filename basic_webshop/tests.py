from decimal import Decimal

from django.test import TestCase

from webshop.core.tests import CoreTestMixin
from webshop.extensions.category.simple.tests import CategoryTestMixin

class SimpleTest(CategoryTestMixin, CoreTestMixin, TestCase):
    def make_test_category(self):
        """ Return a test category. """
        
        c = self.category_class(name='Test', slug='test')
        
        return c
    
    def make_test_product(self):
        """ Return a test product. """
        
        c = self.make_test_category()
        c.save()
        
        p = self.product_class(name='Banana', 
                               slug='banana', 
                               category=c, 
                               price="15.00")
        p.description = 'A nice piece of fruit for the whole family to enjoy.'
        
        return p
    
    def test_product_properties(self):
        p = self.make_test_product()
        p.save()
        
        p = self.product_class.objects.get(pk=p.pk)
        self.assertEqual(p.name, 'Banana')
        self.assertEqual(p.slug, 'banana')
        self.assertEqual(p.price, Decimal("15.00"))
        self.assertEqual(p.description, \
            'A nice piece of fruit for the whole family to enjoy.')
