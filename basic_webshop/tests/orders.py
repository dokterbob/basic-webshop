from decimal import Decimal

from basic_webshop.tests.base import WebshopTestCase
from basic_webshop.models import Order, OrderItem, OrderStateChange, Cart


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

        # Update discounts etcetera
        o.update()

        self.assertEqual(len(o.get_items()), 1)
        self.assertEqual(o.get_items()[0].product, p)
        self.assertEqual(o.get_items()[0].quantity, 5)
        self.assertEqual(o.get_total_items(), 5)
        self.assertEqual(o.coupon_code, cart.coupon_code)
        self.assertEqual(o.customer, cart.customer)

        # Confirm the order - this should delete the cart
        o.confirm()

        # This should have deleted the cart - but all else should remain
        self.assertRaises(Cart.DoesNotExist, Cart.objects.get, pk=cart.pk)
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

        # Update discounts etcetera
        o.update()

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

    def test_order_number(self):
        """ Test whether a valid order number is generated. """
        # Create order
        o = self.make_test_order()
        o.save()

        # Make sure an order number exists in the first place
        self.assert_(o.order_number)

        # Create order
        o2 = self.make_test_order()
        o2.save()

        # Make sure an order number exists in the first place
        self.assert_(o2.order_number)

    def test_invoice_number(self):
        """ Test whether a valid invoice number is generated. """

        # Create order
        o1 = self.make_test_order()
        o1.save()

        # Create order
        o2 = self.make_test_order()
        o2.save()

        # Create order
        o3 = self.make_test_order()
        o3.save()

        self.assertFalse(o1.invoice_number)
        o1.confirm()
        self.assert_(o1.invoice_number)

        o2.confirm()

        self.assertEqual(o2.invoice_number,
                         int(o1.invoice_number) + 1)
