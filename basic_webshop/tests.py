from decimal import Decimal

from django.test import TestCase
from webshop.core.tests import CoreTestMixin
from webshop.extensions.category.simple.tests import CategoryTestMixin

from basic_webshop.models import *


class WebshopTestBase(TestCase):
    """ Base class with helper function for actual tests. """
    def make_test_category(self):
        """ Return a test category """

        c = Category(slug='test')

        return c

    def make_test_brand(self):
        """ Return a test brand """

        b = Brand(slug='test')

        return b

    def make_test_product(self, slug='banana', price="15.00", stock=1,
                          brand=None):
        """ Return a test product """

        if not brand:
            brand = self.make_test_brand()
            brand.save()

        p = Product(slug=slug,
                    price=price,
                    stock=stock,
                    brand=brand)
        return p

    def make_test_producttranslation(self, parent):
        t = ProductTranslation(name='Banana', language_code='en')
        t.parent = parent
        t.description = 'A nice piece of fruit for the whole family to enjoy.'
        return t

    def make_test_productvariation(self, product, stock=1, slug='test'):
        v = ProductVariation(product=product)
        v.stock = stock
        v.slug = slug
        return v

    def make_test_customer(self):
        c = Customer()
        return c

    def make_test_order(self, customer):
        o = Order(customer=customer)
        return o

class SimpleTest(WebshopTestBase, CategoryTestMixin, CoreTestMixin):
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

class OrderTest(WebshopTestBase):
    """ Test basic order process functionality """

    def make_test_cart(self):
        # Create cart
        c = Cart()

        return c

    def test_cartadd(self):
        """ Create a cart and add a product to it """

        # Create product
        p = self.make_test_product()
        p.save()

        # Create cart
        c = self.make_test_cart()
        c.save()

        # Add product to cart
        c.add_item(product=p)

        self.assertEqual(len(c.get_items()), 1)
        self.assertEqual(c.get_items()[0].product, p)

    def test_cartaddone(self):
        """
        1) Add one product to a cart, then add one more of the same kind.
        2) Add some different product to the cart

        """
        # Create product
        p = self.make_test_product()
        p.save()

        # Create cart
        c = self.make_test_cart()
        c.save()

        # Add product to cart
        c.add_item(quantity=1, product=p)

        self.assertEqual(len(c.get_items()), 1)
        self.assertEqual(c.get_items()[0].quantity, 1)
        self.assertEqual(c.get_total_items(), 1)

        # Add product to cart
        c.add_item(quantity=1, product=p)

        self.assertEqual(len(c.get_items()), 1)
        self.assertEqual(c.get_items()[0].quantity, 2)
        self.assertEqual(c.get_total_items(), 2)

        # Create product
        p2 = self.make_test_product(slug='cheese', brand=p.brand)
        p2.save()

        # Add product to cart
        c.add_item(quantity=3, product=p2)

        self.assertEqual(len(c.get_items()), 2)
        self.assertEqual(c.get_total_items(), 5)

        self.assertEqual(c.get_items().get(product=p2).quantity, 3)
        self.assertEqual(c.get_items().get(product=p).quantity, 2)

    def test_cartremove(self):
        """ Add and remove an item from cart """
        # Create product
        p = self.make_test_product()
        p.save()

        # Create cart
        c = self.make_test_cart()
        c.save()

        # Add product to cart
        c.add_item(quantity=23, product=p)
        ret = c.remove_item(product=p)
        self.assert_(ret)
        self.assertEqual(len(c.get_items()), 0)

        # See whether remove on a non-available product returns None
        # as it should
        # Create product
        p2 = self.make_test_product(slug='cheese', brand=p.brand)
        p2.save()

        ret = c.remove_item(product=p2)
        self.assertFalse(ret)
        self.assertEqual(len(c.get_items()), 0)

    def test_cartvariation(self):
        """ Test adding and removing a cart item with a variation. """
        # Create product
        p = self.make_test_product()
        p.save()

        v = self.make_test_productvariation(p)
        v.save()

        p2 = self.make_test_product(slug='cheese', brand=p.brand)
        p2.save()

        # Create cart
        c = self.make_test_cart()
        c.save()

        # Add product to cart
        c.add_item(product=p, variation=v)

        # Added a bogus product
        c.add_item(product=p2)

        self.assertEqual(len(c.get_items()), 2)
        self.assert_(c.get_items().get(product=p))
        self.assert_(c.get_items().get(variation=v))

        ret = c.remove_item(product=p, variation=v)
        self.assert_(ret)
        self.assertEqual(len(c.get_items()), 1)
        self.assertEqual(c.get_items()[0].product, p2)
        self.assertEqual(c.get_items()[0].variation, None)

    def test_orderfromcart(self):
        """ Test creating an order from a cart. """
        # Create product
        p = self.make_test_product()
        p.save()

        # Create cart
        cart = self.make_test_cart()
        cart.save()

        # Create customer
        c = self.make_test_customer()
        c.save()

        # Add product to cart
        cart.add_item(product=p, quantity=5)

        # To order
        o = Order.from_cart(cart, c)
        o.save()

        self.assertEqual(len(o.get_items()), 1)
        self.assertEqual(o.get_items()[0].product, p)
        self.assertEqual(o.get_items()[0].quantity, 5)
        self.assertEqual(o.get_total_items(), 5)

    def test_ordervariation(self):
        """ Test converting a cart item with variation to an order. """
        # Create product
        p = self.make_test_product()
        p.save()

        v = self.make_test_productvariation(p)
        v.save()

        p2 = self.make_test_product(slug='cheese', brand=p.brand)
        p2.save()

        # Create cart
        cart = self.make_test_cart()
        cart.save()

        # Add product to cart
        cart.add_item(product=p, variation=v)

        # Added a bogus product
        cart.add_item(product=p2)

        # Create customer
        c = self.make_test_customer()
        c.save()

        # To order
        o = Order.from_cart(cart, c)
        o.save()

        self.assertEqual(len(o.get_items()), 2)
        self.assert_(o.get_items().get(product=p))
        self.assert_(o.get_items().get(variation=v))

    def test_orderstate_change(self):
        """ Test changing order states. """
        # Create customer
        c = self.make_test_customer()
        c.save()

        o = self.make_test_order(customer=c)
        o.save()
# class DiscountTest(WebshopTestBase):
#     """ Test discounts. """
#
#     def test_discount(self):
#
