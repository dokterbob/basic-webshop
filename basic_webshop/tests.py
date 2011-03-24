from decimal import Decimal

from django.test import TestCase

from countries.models import Country

from webshop.core.tests import CoreTestMixin
from webshop.extensions.category.simple.tests import CategoryTestMixin

from webshop.extensions.stock.exceptions import NoStockAvailableException

from basic_webshop.models import *


class WebshopTestCase(TestCase):
    """ Base class with helper function for actual tests. """
    def make_test_category(self):
        """ Return a test category """

        c = Category(slug='test')

        return c

    def make_test_brand(self):
        """ Return a test brand """

        b = Brand(slug='test')

        return b

    def make_test_cart(self):
        # Create cart
        c = Cart()

        return c

    def make_test_product(self, slug='banana',
                          price=Decimal('15.00'), stock=100,
                          brand=None):
        """ Return a test product """

        if not brand:
            try:
                brand = Brand.objects.all()[0]
            except IndexError:
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

    def make_test_address(self, country=None, customer=None):
        if not customer:
            try:
                customer = Customer.objects.all()[0]
            except IndexError:
                customer = self.make_test_customer()
                customer.save()

        if not country:
            country = Country.objects.all()[0]

        a = Address(customer=customer, country=country)
        return a

    def make_test_order(self, customer=None, shipping_address=None):
        if not customer:
            try:
                customer = Customer.objects.all()[0]
            except IndexError:
                customer = self.make_test_customer()
                customer.save()

        if not shipping_address:
            try:
                shipping_address = Address.objects.all()[0]
            except IndexError:
                shipping_address = self.make_test_address(customer=customer)
                shipping_address.save()


        o = Order(customer=customer, shipping_address=shipping_address)
        return o

    def make_test_discount(self):
        """ Create a discount object with all required fields set """
        return Discount()

    def make_test_orderitem(self,
                            quantity=1,
                            product=None,
                            piece_price=Decimal('10.00'),
                            order=None):
        """ Create a test orderitem. """

        if not product:
            try:
                product = Product.objects.all()[0]
            except IndexError:
                product = self.make_test_product()
                product.save()

        if not order:
            try:
                order = Order.objects.all()[0]
            except IndexError:
                order = self.make_test_order()
                order.save()

        i = OrderItem(quantity=quantity,
                      product=product,
                      piece_price=piece_price,
                      order=order)

        return i

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

class OrderTest(WebshopTestCase):
    """ Test basic order process functionality """

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
        p2 = self.make_test_product(slug='cheese')
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
        p2 = self.make_test_product(slug='cheese')
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

        p2 = self.make_test_product(slug='cheese')
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

    def test_cartprice(self):
        """ Test price calculation mechanics. """

        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.save()

        # Create cart
        c = self.make_test_cart()
        c.save()

        self.assertEqual(c.get_price(), Decimal('0.00'))

        # Add product to cart
        item = c.add_item(quantity=2, product=p)

        self.assertEqual(c.get_price(), Decimal('20.00'))
        self.assertEqual(item.get_price(), Decimal('20.00'))
        self.assertEqual(item.get_piece_price(), Decimal('10.00'))

        # Create product
        p2 = self.make_test_product(price=Decimal('15.00'), slug='p2')
        p2.save()

        # Add product to cart
        c.add_item(quantity=1, product=p2)

        self.assertEqual(c.get_price(), Decimal('35.00'))

    def test_orderfromcart(self):
        """ Test creating an order from a cart. """
        # Create product
        p = self.make_test_product()
        p.save()

        # Create customer
        c = self.make_test_customer()
        c.save()

        # Create cart
        cart = self.make_test_cart()
        cart.coupon_code = 'testme'
        cart.customer = c
        cart.save()

        # Add product to cart
        cart.add_item(product=p, quantity=5)

        # To order
        o = Order.from_cart(cart)
        o.save()

        self.assertEqual(len(o.get_items()), 1)
        self.assertEqual(o.get_items()[0].product, p)
        self.assertEqual(o.get_items()[0].quantity, 5)
        self.assertEqual(o.get_total_items(), 5)
        self.assertEqual(o.coupon_code, cart.coupon_code)
        self.assertEqual(o.customer, cart.customer)

    def test_ordervariation(self):
        """ Test converting a cart item with variation to an order. """
        # Create product
        p = self.make_test_product()
        p.save()

        v = self.make_test_productvariation(p)
        v.save()

        p2 = self.make_test_product(slug='cheese')
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
        cart.customer = c

        # To order
        o = Order.from_cart(cart)
        o.save()

        self.assertEqual(len(o.get_items()), 2)
        self.assert_(o.get_items().get(product=p))
        self.assert_(o.get_items().get(variation=v))

    def test_orderprice(self):
        """ Test price calculation mechanics. """

        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.save()

        # Create order
        o = self.make_test_order()
        o.save()

        self.assertEqual(o.get_price(), Decimal('0.00'))

        i = OrderItem(quantity=2, product=p, piece_price=p.get_price())
        self.assertEqual(i.get_piece_price(), Decimal('10.00'))
        self.assertEqual(i.get_price(), Decimal('20.00'))

        o.orderitem_set.add(i)

        self.assertEqual(o.get_price(), Decimal('20.00'))

        # Create product
        p2 = self.make_test_product(price=Decimal('15.00'), slug='p2')
        p2.save()

        i2 = OrderItem(quantity=1, product=p2, piece_price=p2.get_price())

        # Add product to cart
        o.orderitem_set.add(i2)

        self.assertEqual(o.get_price(), Decimal('35.00'))

    def test_orderstate_change(self):
        """ Test changing order states. """

        from webshop.core.signals import order_state_change

        def assert_state_change(sender, old_state, new_state, state_change, **kwargs):
            self.assert_(old_state != new_state or state_change.message)

        order_state_change.connect(assert_state_change)

        # state_changed = False
        # def signal():
        # def assert_signal_called(sender, **kwargs):
        #     state_changed = True
        # self.assert_(state_changed)
        # state_changed = False

        o = self.make_test_order()
        o.save()

        o2 = self.make_test_order()
        o2.save()

        self.assertEqual(OrderStateChange.objects.count(), 2)
        self.assertIn(OrderStateChange.get_latest(o),
                         OrderStateChange.objects.all())
        self.assertIn(OrderStateChange.get_latest(o2),
                         OrderStateChange.objects.all())

        new_state = 2
        o.state = new_state
        o.save()

        self.assertEqual(OrderStateChange.objects.count(), 3)
        self.assertEqual(OrderStateChange.get_latest(o).state, new_state)


class DiscountTest(WebshopTestCase):
    """ Test discounts. """

    def test_amountdiscount(self):
        """
        Test whether creating a discount which represents some amount of order
        discount applies well.
        """

        # Create discount
        discount = self.make_test_discount()
        discount.order_amount = Decimal('2.00')
        discount.save()

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('2.00'))
        self.assertEqual(o.get_price(), Decimal('8.00'))


    def test_amountcartdiscount(self):
        """
        Test an amount discount on a cart and test whether it is properly
        converted to a discount on an order.
        """
        # Create discount
        discount = self.make_test_discount()
        discount.order_amount = Decimal('2.00')
        discount.save()

        # Create product
        p = self.make_test_product(price=Decimal('10.00'))
        p.save()

        # Create customer
        c = self.make_test_customer()
        c.save()

        # Create cart
        cart = self.make_test_cart()
        # cart.coupon_code = 'testme'
        cart.customer = c
        cart.save()

        # Add product to cart
        cart.add_item(product=p, quantity=5)

        # Check cart discounts
        self.assertEqual(cart.get_order_discount(), Decimal('2.00'))
        self.assertEqual(cart.get_price(), Decimal('48.00'))

        # To order
        order = Order.from_cart(cart)
        order.save()

        # Check order discounts
        self.assertEqual(order.get_order_discount(), Decimal('2.00'))
        self.assertEqual(order.get_price(), Decimal('48.00'))
        self.assertEqual(order.discounts.all()[0], discount)


    def test_percentagediscount(self):
        """
        Test whether creating a discount which represents some percentage of
        the order amount applies well.
        """

        # Create discount
        discount = self.make_test_discount()
        discount.order_percentage = 10
        discount.save()

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('1.00'))
        self.assertEqual(o.get_price(), Decimal('9.00'))


    def test_coupondiscountamount(self):
        """ Test whether coupon discounts work. """

        # Create discount
        discount = self.make_test_discount()
        discount.order_amount = Decimal('2.00')
        discount.use_coupon = True
        discount.save()

        code = discount.coupon_code
        self.assert_(code)

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all().count(), 0)
        self.assertEqual(o.get_order_discount(), Decimal('0.00'))
        self.assertEqual(o.get_price(), Decimal('10.00'))

        o.coupon_code = code
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('2.00'))
        self.assertEqual(o.get_price(), Decimal('8.00'))

    def test_coupondiscountpercentage(self):
        """ Test whether coupon discounts work. """

        # Create discount
        discount = self.make_test_discount()
        discount.order_percentage = 10
        discount.use_coupon = True
        discount.save()

        code = discount.coupon_code
        self.assert_(code)

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all().count(), 0)
        self.assertEqual(o.get_order_discount(), Decimal('0.00'))
        self.assertEqual(o.get_price(), Decimal('10.00'))

        o.coupon_code = code
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('1.00'))
        self.assertEqual(o.get_price(), Decimal('9.00'))

    def test_limitedusagediscount(self):
        """ Test whether coupon discounts work. """

        # Create discount
        discount = self.make_test_discount()
        discount.order_amount = Decimal('2.00')
        discount.use_limit = 3
        discount.save()

        self.assertEqual(discount.used, 0)

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('2.00'))
        self.assertEqual(o.get_price(), Decimal('8.00'))

        o.register_confirmation()
        o.register_confirmation()

        # Discount.register_use(o.discounts.all(), count=2)

        # Update the discount object
        discount = Discount.objects.get(pk=discount.pk)
        self.assertEqual(discount.used, 2)

        # There should still be one more use possible

        # Start with a new order
        o.delete()

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('2.00'))
        self.assertEqual(o.get_price(), Decimal('8.00'))


        # Make sure no more uses are left
        o.register_confirmation()
        # Discount.register_use(o.discounts.all())

        # Update the discount object
        discount = Discount.objects.get(pk=discount.pk)
        self.assertEqual(discount.used, 3)
        self.assertEqual(discount.get_uses_left(), 0)

        # Start with a new order
        o.delete()

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update_discount()
        o.save()

        self.assertEqual(o.discounts.all().count(), 0)
        self.assertEqual(o.get_order_discount(), Decimal('0.00'))
        self.assertEqual(o.get_price(), Decimal('10.00'))


class StockTest(WebshopTestCase):
    """ Test products with limited stock. """

    def test_cartadd(self):
        """ Test creating a product with stock and adding it to a cart."""

        product = self.make_test_product()
        product.stock = 2
        product.save()

        cart = self.make_test_cart()
        cart.save()

        # Add one of product to the cart
        cart.add_item(product, quantity=1)

        cartitem = cart.get_items()[0]
        self.assertEqual(cartitem.quantity, 1)

        # Add two more - this should fail
        self.assertRaises(NoStockAvailableException, cart.add_item,
                          product, quantity=2)

        cartitem = cart.get_items()[0]
        self.assertEqual(cartitem.quantity, 1)

        # Add one more to the cart
        cart.add_item(product, quantity=1)

        # See whether quantity has increased
        cartitem = cart.get_items()[0]
        self.assertEqual(cartitem.quantity, 2)

        # Add one more - this should fail
        self.assertRaises(NoStockAvailableException, cart.add_item,
                          product, quantity=1)

    def test_cartvariationadd(self):
        """
        Test stock management for cart items with products having variations.

        If a variation has been defined, product stock should be ignored.
        """
        # Create product
        p = self.make_test_product()
        p.stock = 2
        p.save()

        # Create cart
        c = self.make_test_cart()
        c.save()

        v = self.make_test_productvariation(p)
        v.stock = 1
        v.save()

        # Add product to cart
        c.add_item(product=p, variation=v, quantity=1)

        # Add one more - this should fail
        self.assertRaises(NoStockAvailableException, c.add_item,
                          p, quantity=1, variation=v)


    def test_orderconfirm(self):
        """
        Test whether sold-out items cannot have their orders confirmed and
        whether non-sold-out items can but have their stock decreased.
        """
        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.stock=2
        p.save()

        # Create order
        o = self.make_test_order()
        o.save()

        i = OrderItem(quantity=2, product=p, piece_price=p.get_price())
        o.orderitem_set.add(i)

        # Check the stock, this should raise no error
        o.check_stock()

        # Register order confirmation, update stock
        o.register_confirmation()

        p = Product.objects.get(pk=p.pk)
        self.assertEquals(p.stock, 0)

        # Create order
        o = self.make_test_order()
        o.save()

        i = OrderItem(quantity=1, product=p, piece_price=p.get_price())
        o.orderitem_set.add(i)

        # Add one more - this should fail
        self.assertRaises(NoStockAvailableException, o.check_stock)


    def test_ordervariationconfirm(self):
        """
        Test the same as tested in `test_orderconfirm` but now for a product
        with variations.
        """
        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.stock=2
        p.save()

        # Create order
        o = self.make_test_order()
        o.save()

        # Create variation
        v = self.make_test_productvariation(p)
        v.stock = 2
        v.save()

        # Order item with variation
        i = OrderItem(quantity=2, product=p, piece_price=p.get_price(),
                      variation=v)
        o.orderitem_set.add(i)

        # Check the stock, this should raise no error
        o.check_stock()

        # Register order confirmation
        o.register_confirmation()

        v = ProductVariation.objects.get(pk=v.pk)
        self.assertEquals(v.stock, 0)

        # This should not have changed as it should have been ignored
        p = Product.objects.get(pk=p.pk)
        self.assertEquals(p.stock, 2)

        # Create order
        o = self.make_test_order()
        o.save()

        i = OrderItem(quantity=1, product=p, piece_price=p.get_price(),
                      variation=v)
        o.orderitem_set.add(i)

        # Add one more - this should fail
        self.assertRaises(NoStockAvailableException, o.check_stock)


    def test_orderconfirmuseaccountdiscount(self):
        """
        Test whether sold-out items generation an exception on order
        confirmation do not increase the use counter for discounts.
        """

        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.stock=2
        p.save()

        # Create discount
        discount = self.make_test_discount()
        discount.order_amount = Decimal('2.00')
        discount.save()

        self.assertEqual(discount.used, 0)

        # Create order
        o = self.make_test_order()
        o.save()

        i = OrderItem(quantity=1, product=p, piece_price=p.get_price())
        o.orderitem_set.add(i)

        # Make sure we update discounts for this order
        o.update_discount()

        # Check the stock, this should raise no error
        o.check_stock()

        # Register order confirmation
        o.register_confirmation()

        discount = Discount.objects.get(pk=discount.pk)
        self.assertEqual(discount.used, 1)

        # Create another order that should be sold out
        o = self.make_test_order()
        o.save()

        i = OrderItem(quantity=2, product=p, piece_price=p.get_price())
        o.orderitem_set.add(i)

        # Make sure register_confirmation fails
        self.assertRaises(NoStockAvailableException, o.check_stock)

        # Now check whether the discount has not been applied
        discount = Discount.objects.get(pk=discount.pk)
        self.assertEqual(discount.used, 1)


class ShippingTest(WebshopTestCase):
    """ Test shipping for orders. """

    def make_test_shippingmethod(self, order_cost=Decimal('10.00')):
        """ Make a shipping method for testing. """
        s = ShippingMethod()
        s.order_cost = order_cost
        return s

    def test_shippingorder(self):
        # Shipping method
        s = self.make_test_shippingmethod()
        s.save()

        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.save()

        # Create order
        o = self.make_test_order()
        o.save()

        i = OrderItem(quantity=2, product=p, piece_price=p.get_price())
        o.orderitem_set.add(i)
