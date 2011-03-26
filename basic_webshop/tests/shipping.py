from decimal import Decimal

from countries.models import Country

from basic_webshop.tests.base import WebshopTestCase
from basic_webshop.models import ShippingMethod, OrderItem

class ShippingTest(WebshopTestCase):
    """ Test shipping for orders. """

    def test_shippingquery(self):
        # Shipping method
        s1 = self.make_test_shippingmethod(order_cost=Decimal('2.00'))
        s1.save()

        valid = ShippingMethod.get_valid_methods(order_methods=True)
        method = valid[0]
        self.assertEqual(method, s1)

        self.assertEqual(method.get_cost(), Decimal('2.00'))

    def test_countryquery(self):
        country1 = Country.objects.all()[0]
        country2 = Country.objects.all()[1]

        # Shipping method with country1
        s1 = self.make_test_shippingmethod(order_cost=Decimal('2.00'))
        s1.name = 'cheapest'
        s1.save()

        s1.countries.add(country1)

        # Shipping method with country1 and country2
        s2 = self.make_test_shippingmethod(order_cost=Decimal('3.00'))
        s2.name = 'less cheap'
        s2.save()

        s2.countries.add(country1)
        s2.countries.add(country2)

        # Shipping method without country
        s3 = self.make_test_shippingmethod(order_cost=Decimal('4.00'))
        s3.name = 'expensive'
        s3.save()

        # Check country1-s1
        valid = ShippingMethod.get_valid_methods(order_methods=True,
                                                 country=country1)
        valid = list(valid)
        self.assertEquals(len(valid), 3)
        self.assertIn(s1, valid)
        self.assertIn(s2, valid)
        self.assertIn(s3, valid)

        # Check the cheapest
        cheapest = ShippingMethod.get_cheapest(order_methods=True,
                                               country=country1)
        self.assertEqual(s1, cheapest)
        self.assertEqual(cheapest.get_cost(), Decimal('2.00'))

        # Check country2-s2
        valid = ShippingMethod.get_valid_methods(order_methods=True,
                                                 country=country2)
        valid = list(valid)
        self.assertEquals(len(valid), 2)
        self.assertIn(s2, valid)
        self.assertIn(s3, valid)

        # Check the cheapest
        cheapest = ShippingMethod.get_cheapest(order_methods=True,
                                               country=country2)
        self.assertEqual(s2, cheapest)
        self.assertEqual(cheapest.get_cost(), Decimal('3.00'))

        # Check s3, no country
        valid = ShippingMethod.get_valid_methods(order_methods=True)

        method = valid[0]
        self.assertEqual(method, s3)

        cheapest = ShippingMethod.get_cheapest(order_methods=True)
        self.assertEqual(s3, cheapest)
        self.assertEqual(cheapest.get_cost(), Decimal('4.00'))

    def test_shippingorder(self):
        # Shipping method
        s1 = self.make_test_shippingmethod(order_cost=Decimal('4.00'))
        s1.name = 'expensive'
        s1.save()

        # Get us a country
        country1 = Country.objects.all()[1]
        country2 = Country.objects.all()[2]

        # Shipping method with country1 and country2
        s2 = self.make_test_shippingmethod(order_cost=Decimal('3.00'))
        s2.name = 'less expensive'
        s2.save()

        # Make sure the second method is only valid for this country
        s2.countries.add(country2)

        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.save()

        # Create order
        o = self.make_test_order()
        o.shipping_address.country = country1
        o.shipping_address.save()
        o.save()

        i = OrderItem(quantity=2, product=p, piece_price=p.get_price())
        o.orderitem_set.add(i)

        # Update the order: calculate costs etc.
        o.update()

        self.assertEqual(o.shipping_method, s1)
        self.assertEqual(o.get_shipping_costs(), Decimal('4.00'))
        self.assertEqual(o.order_shipping_costs, Decimal('4.00'))
        self.assertEqual(o.get_order_shipping_costs(), Decimal('4.00'))
        self.assertEqual(o.get_price_without_shipping(), Decimal('20.00'))
        self.assertEqual(o.get_price(), Decimal('24.00'))

        # Create another order from a cheaper country
        # Create order
        o = self.make_test_order()
        o.shipping_address.country = country2
        o.shipping_address.save()
        o.save()

        i = OrderItem(quantity=1, product=p, piece_price=p.get_price())
        o.orderitem_set.add(i)

        # Update the order: calculate costs etc.
        o.update()

        self.assertEqual(o.shipping_method, s2)
        self.assertEqual(o.get_shipping_costs(), Decimal('3.00'))
        self.assertEqual(o.order_shipping_costs, Decimal('3.00'))
        self.assertEqual(o.get_order_shipping_costs(), Decimal('3.00'))
        self.assertEqual(o.get_price_without_shipping(), Decimal('10.00'))
        self.assertEqual(o.get_price(), Decimal('13.00'))


    def test_shippingcart(self):
        # Shipping method
        s1 = self.make_test_shippingmethod(order_cost=Decimal('4.00'))
        s1.name = 'expensive'
        s1.save()

        # Get us a country
        country1 = Country.objects.all()[0]

        # Shipping method with country1 and country2
        s2 = self.make_test_shippingmethod(order_cost=Decimal('3.00'))
        s2.name = 'less expensive'
        s2.save()

        # Make sure the second method is only valid for this country
        s2.countries.add(country1)

        # Create product
        p = self.make_test_product(price=Decimal('10.00'), slug='p1')
        p.save()

        # Create cart
        cart = self.make_test_cart()
        cart.save()

        # Add product to cart
        item = cart.add_item(quantity=2, product=p)

        self.assertEqual(cart.get_shipping_costs(), Decimal('4.00'))
        self.assertEqual(cart.get_order_shipping_costs(), Decimal('4.00'))
        self.assertEqual(cart.get_price_without_shipping(), Decimal('20.00'))
        self.assertEqual(cart.get_price(), Decimal('24.00'))
 