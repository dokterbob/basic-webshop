import logging
logger = logging.getLogger(__name__)

from django import forms
from django.utils.translation import ugettext_lazy as _

from basic_webshop.models import ProductRating, Address, Cart, CartItem, Discount


class RatingForm(forms.ModelForm):
    """ Form for ratings. """

    class Meta:
        model = ProductRating

    def __init__(self, user, product, *args, **kwargs):
        """
        We take a user and product argument and store it in the form instance
        for later reference.
        """
        self.user = user
        self.product = product

        super(RatingForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """ Make sure we store the user and product on the rating object. """
        instance = super(RatingForm, self).save(commit=False)
        instance.user = self.user
        instance.product = self.product

        if commit:
            instance.save()

        return instance


class CartAddForm(forms.Form):
    """
    Simple form for adding products to the cart from the product detail page.

    ..todo::
        Find a way to account for adding variations here.
    """

    quantity_error = _('The requested quantity of this product is not available.')

    def __init__(self, product, cart, *args, **kwargs):
        """ Store cart and product on the form object. """

        self.cart = cart
        self.product = product

        super(CartAddForm, self).__init__(*args, **kwargs)

    def save(self):
        """ Add the requested item(s) to the cart. """

        quantity = self.cleaned_data['quantity']
        self.cart.add_item(self.product, quantity)

    def clean_quantity(self):
        """ Check stock for given quantity. """
        quantity = self.cleaned_data['quantity']

        cartitem = self.cart.get_item(product=self.product)
        total_quantity = cartitem.quantity + quantity
        if not self.product.is_available(total_quantity):
            raise forms.ValidationError(self.quantity_error)

        return quantity

    QUANTITY_CHOICES =  tuple((x, x) for x in xrange(1,20))
    quantity = forms.IntegerField(widget= \
        forms.Select(choices=QUANTITY_CHOICES), min_value=1, initial=1)


class CartItemForm(forms.ModelForm):
    """ Form for updating shopping cart quantities. """

    quantity_error = _('The requested quantity of this product is not available.')

    class Meta:
        model = CartItem

    def clean_quantity(self):
        """ Check stock for given quantity. """
        quantity = self.cleaned_data['quantity']

        assert self.instance
        cartitem = self.instance
        product = cartitem.product

        cartitem = cartitem.cart.get_item(product=product)
        total_quantity = cartitem.quantity + quantity
        if not product.is_available(total_quantity):
            raise forms.ValidationError(self.quantity_error)

        return quantity


class AddressUpdateForm(forms.ModelForm):
    """ Form for updating Address objects. """

    class Meta:
        model = Address

    def __init__(self, *args, **kwargs):
        """ We should always be instantiated with an instance. """
        assert 'instance' in kwargs, 'This form is only for updating'
        super(AddressUpdateForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """ Make sure we never override an existing Address. """
        instance = super(AddressUpdateForm, self).save(commit=False)
        instance.pk = None

        if commit and self.has_changed():
            logger.debug('Saving new Address instance')
            instance.save()

        return instance


class CartDiscountCouponForm(forms.ModelForm):
    """ Form for entering a coupon code for shopping carts. """

    coupon_code_error = _('This coupon code is not valid.')

    class Meta:
        model = Cart
        fields = ('coupon_code', )

    def __init__(self, *args, **kwargs):
        """ We should always be instantiated with an instance. """
        assert 'instance' in kwargs, 'This form is only for updating'
        super(CartDiscountCouponForm, self).__init__(*args, **kwargs)

    def clean_coupon_code(self):
        coupon_code = self.cleaned_data['coupon_code'].strip()

        logger.debug('Checking coupong code validity for %s' % coupon_code)

        valid_discounts = Discount.get_valid_discounts(
                                            coupon_code=coupon_code,
                                            order_discounts=True,
                                            item_discounts=True)

        if not valid_discounts.exists():
            raise forms.ValidationError(self.coupon_code_error)

        return coupon_code
