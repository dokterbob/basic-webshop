from decimal import Decimal

from basic_webshop.tests.base import WebshopTestCase
from basic_webshop.models import Discount, Order

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
        o.update()
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

        # Update discounts etcetera
        order.update()

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
        o.update()

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
        o.update()

        self.assertEqual(o.discounts.all().count(), 0)
        self.assertEqual(o.get_order_discount(), Decimal('0.00'))
        self.assertEqual(o.get_price(), Decimal('10.00'))

        o.coupon_code = code
        o.update()

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
        o.update()

        self.assertEqual(o.discounts.all().count(), 0)
        self.assertEqual(o.get_order_discount(), Decimal('0.00'))
        self.assertEqual(o.get_price(), Decimal('10.00'))

        o.coupon_code = code
        o.update()

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
        o.update()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('2.00'))
        self.assertEqual(o.get_price(), Decimal('8.00'))

        o.confirm()

        # Check the discount object
        discount = Discount.objects.get(pk=discount.pk)
        self.assertEqual(discount.used, 1)

        # Do the same dance over again with a different order
        ######

        # Delete the original order
        o.delete()

        # Create orderitem
        i = self.make_test_orderitem(quantity=2, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update()
        o.confirm()

        # Check the discount object
        discount = Discount.objects.get(pk=discount.pk)
        self.assertEqual(discount.used, 2)

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('2.00'))
        self.assertEqual(o.get_price(), Decimal('18.00'))

        # Start with a new order
        o.delete()

        # There should still be one more use possible

        # Create orderitem
        i = self.make_test_orderitem(quantity=1, piece_price=Decimal('10.00'))
        i.save()

        # No discounts
        o = i.order
        o.update()

        self.assertEqual(o.discounts.all()[0], discount)
        self.assertEqual(o.get_order_discount(), Decimal('2.00'))
        self.assertEqual(o.get_price(), Decimal('8.00'))


        # Make sure no more uses are left
        o.confirm()
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
        o.update()

        self.assertEqual(o.discounts.all().count(), 0)
        self.assertEqual(o.get_order_discount(), Decimal('0.00'))
        self.assertEqual(o.get_price(), Decimal('10.00'))
