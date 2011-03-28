from django import forms
from django.utils.translation import ugettext_lazy as _

from basic_webshop.models import ProductRating

from recaptcha_works.fields import RecaptchaField

import contact_form.forms


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

        if not self.product.is_available(quantity):
            raise forms.ValidationError(self.quantity_error)

        return quantity

    quantity = forms.IntegerField(min_value=1, initial=1)

attrs_dict = { 'class': 'required' }

class ContactForm(contact_form.forms.ContactBaseForm):
    """
    Contact form which requires users to enter firstname, lastname, email adress,
    subject, message body as well a message captcha.
    """

    recipient_list = ["alexander.schrijver@gmail.com", ]

    firstname = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs=attrs_dict),
                           label=_('Firstname'),
                           required=True)
    lastname = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs=attrs_dict),
                           label=_('Lastname'),
                           required=True)
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=200)),
                             label=_('Email address'),
                             required=True)
    subject = forms.CharField(max_length=100,
                           widget=forms.TextInput(attrs=attrs_dict),
                           label=_('Subject'),
                           required=True)
    body = forms.CharField(widget=forms.Textarea(attrs=attrs_dict),
                              label=_('Message'),
                              required=True)
    captcha = RecaptchaField()

