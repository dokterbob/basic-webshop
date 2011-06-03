from decimal import Decimal
from basic_webshop.tests.base import WebshopTestCase

from shopkit.core.tests import CoreTestMixin
from shopkit.extensions.category.simple.tests import CategoryTestMixin

from basic_webshop.models import Product
from basic_webshop.tests.discounts import DiscountTest
from basic_webshop.tests.shipping import ShippingTest
from basic_webshop.tests.stock import StockTest
from basic_webshop.tests.orders import OrderTest


class SimpleTest(WebshopTestCase, CategoryTestMixin, CoreTestMixin):
    """ Test some basic functionality. """

    def test_product_properties(self):
        c = self.make_test_category()
        c.save()

        p = self.make_test_product()
        p.save()

        p.categories.add(c)

        pt = self.make_test_producttranslation(p)
        pt.save()

        p = Product.objects.get(pk=p.pk)
        self.assertEqual(p.name, 'Banana')
        self.assertEqual(p.slug, 'banana')
        self.assertEqual(p.price, Decimal("15.00"))
        self.assertEqual(p.description, \
            'A nice piece of fruit for the whole family to enjoy.')
