from decimal import Decimal

from django.test import TestCase

from countries.models import Country

from basic_webshop.models import \
    ShippingMethod, Category, Brand, Product, ProductTranslation, Customer, \
    Address, Cart, Order, Discount, OrderItem, ProductVariation

class WebshopTestCase(TestCase):
    """ Base class with helper function for actual tests. """

    def make_test_shippingmethod(self, order_cost=Decimal('10.00')):
        """ Make a shipping method for testing. """
        s = ShippingMethod()
        s.order_cost = order_cost
        return s

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
