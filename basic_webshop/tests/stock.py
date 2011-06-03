from decimal import Decimal

from shopkit.core.exceptions import AlreadyConfirmedException
from shopkit.stock.exceptions import NoStockAvailableException

from basic_webshop.tests.base import WebshopTestCase
from basic_webshop.models import \
    Product, ProductVariation, OrderItem, Discount

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
        o.prepare_confirm()

        # Register order confirmation, update stock
        o.confirm()

        # Prepare again: this should raise an AlreadyConfirmedException
        self.assertRaises(AlreadyConfirmedException, o.prepare_confirm)

        # This should raise an AssertionError as it is potentially to call
        # confirm twice!
        self.assertRaises(AssertionError, o.confirm)

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
        o.prepare_confirm()

        # Register order confirmation
        o.confirm()

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
        o.update()

        # Check the stock, this should raise no error
        o.prepare_confirm()

        # Register order confirmation
        o.confirm()

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
